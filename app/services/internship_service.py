from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path
from fastapi import UploadFile

from app.models.internship import Application, InternshipPosition, Match
from app.repositories.internship import ApplicationRepository, InternshipPositionRepository, MatchRepository
from app.repositories.user import UserRepository


class InternshipService:
    def __init__(
        self,
        position_repo: InternshipPositionRepository,
        application_repo: ApplicationRepository,
        match_repo: MatchRepository,
        user_repo: UserRepository,
    ):
        self.position_repo = position_repo
        self.application_repo = application_repo
        self.match_repo = match_repo
        self.user_repo = user_repo

    def list_positions(self):
        return self.position_repo.list_open()

    def search_positions(self, keyword: str, company: str, location: str):
        positions = self.position_repo.search_open(
            keyword.strip(),
            company.strip(),
            location.strip(),
        )
        results = []
        for position in positions:
            company_user = self.user_repo.get_by_id(position.company_id)
            if company_user is None:
                raise ValueError("Internship position references a missing company.")
            results.append(
                {
                    "position": position,
                    "company_name": company_user.full_name or company_user.username,
                }
            )
        return results

    def create_position(
        self,
        company_id: int,
        title: str,
        description: str,
        requirements: str,
        location: str,
        application_deadline: date,
    ):
        position = InternshipPosition(
            company_id=company_id,
            title=title,
            description=description,
            requirements=requirements,
            location=location,
            status="open",
            application_deadline=application_deadline,
        )
        return self.position_repo.create(position)

    def get_company_position(self, company_id: int, position_id: int):
        position = self.position_repo.get_by_id(position_id)
        if position is None or position.company_id != company_id:
            return None
        return position

    def update_position(
        self,
        company_id: int,
        position_id: int,
        title: str,
        description: str,
        requirements: str,
        location: str,
        application_deadline: date,
    ):
        position = self.get_company_position(company_id, position_id)
        if position is None:
            raise ValueError("Internship position not found.")
        position.title = title
        position.description = description
        position.requirements = requirements
        position.location = location
        position.application_deadline = application_deadline
        return self.position_repo.update(position)

    def close_position(self, company_id: int, position_id: int):
        position = self.get_company_position(company_id, position_id)
        if position is None:
            raise ValueError("Internship position not found.")
        position.status = "closed"
        return self.position_repo.update(position)

    def get_position(self, position_id: int):
        return self.position_repo.get_by_id(position_id)

    def get_company(self, company_id: int):
        return self.user_repo.get_by_id(company_id)

    def apply_for_position(self, student_id: int, internship_id: int, resume_file: UploadFile, cover_letter: str):
        position = self.position_repo.get_by_id(internship_id)
        if not position:
            raise ValueError("Internship position not found.")
        existing_application = self.application_repo.get_by_student_and_internship(student_id, internship_id)
        if existing_application:
            raise ValueError("You have already applied for this internship.")
        if resume_file.content_type != "application/pdf":
            raise ValueError("Resume must be a PDF file.")

        header = resume_file.file.read(1024) # Read the first 1024 bytes to check for PDF signature
        if not header.startswith(b"%PDF"):
            raise ValueError("Uploaded file is not a valid PDF.")
        resume_file.file.seek(0)  # Reset file pointer to the beginning after reading
        
        upload_dir = Path("uploads") / "resumes"
        upload_dir.mkdir(parents=True, exist_ok=True)

        resume_file_path = upload_dir / f"student_{student_id}_pos_{internship_id}.pdf"
        with resume_file_path.open("wb") as f:
            shutil.copyfileobj(resume_file.file, f)
    
        application = Application(
            student_id=student_id,
            internship_id=internship_id,
            resume_path=str(resume_file_path),
            cover_letter=cover_letter,
            status="pending",
        )
        return self.application_repo.create(application)

    def get_match_dashboard(self, status_filter: str):
        if status_filter not in {"pending", "approved", "rejected", "all"}:
            raise ValueError("Invalid match status filter.")

        applications = self.application_repo.list_all()
        matches = self.match_repo.list_all()
        matches_by_application = {match.application_id: match for match in matches}
        pending_matches = sum(
            1
            for application in applications
            if application.id is not None
            and (
                matches_by_application.get(application.id) is None
                or matches_by_application[application.id].approval_status == "pending"
            )
        )
        records = []

        for application in applications:
            if application.id is None:
                raise RuntimeError("Cannot review an unsaved application.")
            match = matches_by_application.get(application.id)
            match_status = match.approval_status if match else "pending"
            if status_filter != "all" and match_status != status_filter:
                continue

            student = self.user_repo.get_by_id(application.student_id)
            position = self.position_repo.get_by_id(application.internship_id)
            if student is None or position is None:
                raise ValueError("Application references a missing student or internship.")
            company = self.user_repo.get_by_id(position.company_id)
            if company is None:
                raise ValueError("Internship references a missing company.")

            records.append(
                {
                    "application_id": application.id,
                    "student_name": student.full_name or student.username,
                    "position_title": position.title,
                    "company_name": company.full_name or company.username,
                    "position_description": position.description,
                    "position_requirements": position.requirements,
                    "position_location": position.location,
                    "application_deadline": position.application_deadline,
                    "match_status": match_status,
                }
            )

        return {
            "records": records,
            "status_filter": status_filter,
            "total_students": sum(
                1 for user in self.user_repo.get_all_users() if user.role == "student"
            ),
            "active_listings": len(self.position_repo.list_open()),
            "pending_matches": pending_matches,
            "approved_matches": sum(
                1 for match in matches if match.approval_status == "approved"
            ),
        }

    def match_application(
        self,
        application_id: int,
        department_admin_id: int,
        approval_status: str,
        notes: str,
    ):
        application = self.application_repo.get_by_id(application_id)
        if application is None:
            raise ValueError("Application not found.")
        if approval_status not in {"approved", "rejected"}:
            raise ValueError("Invalid approval status.")

        existing_match = self.match_repo.get_by_application(application_id)
        if existing_match:
            existing_match.department_admin_id = department_admin_id
            existing_match.approval_status = approval_status
            if notes.strip():
                existing_match.notes = notes
            return self.match_repo.update(existing_match)

        match = Match(
            application_id=application_id,
            department_admin_id=department_admin_id,
            approval_status=approval_status,
            notes=notes,
        )
        return self.match_repo.create(match)
        