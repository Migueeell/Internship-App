from __future__ import annotations

from typing import Optional

from sqlmodel import Session, or_, select

from app.models.internship import Application, InternshipPosition, Match
from app.models.user import User

class InternshipPositionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, position: InternshipPosition) -> InternshipPosition:
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def update(self, position: InternshipPosition) -> InternshipPosition:
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def get_by_id(self, position_id: int) -> Optional[InternshipPosition]:
        return self.db.get(InternshipPosition, position_id)

    def list_open(self) -> list[InternshipPosition]:
        return self.db.exec(select(InternshipPosition).where(InternshipPosition.status == "open")).all()

    def search_open(
        self,
        keyword: str,
        company: str,
        location: str,
    ) -> list[InternshipPosition]:
        statement = select(InternshipPosition).where(InternshipPosition.status == "open")
        if keyword:
            pattern = f"%{keyword}%"
            statement = statement.where(or_(InternshipPosition.title.ilike(pattern), InternshipPosition.description.ilike(pattern),InternshipPosition.requirements.ilike(pattern)))
        if company:
            company_pattern = f"%{company}%"
            statement = statement.join(User).where(
                or_(
                    User.full_name.ilike(company_pattern),
                    User.username.ilike(company_pattern),
                )
            )
        if location:
            statement = statement.where(InternshipPosition.location.ilike(f"%{location}%"))
        return self.db.exec(statement).all()
            
    def list_by_company(self, company_id: int) -> list[InternshipPosition]:
        return self.db.exec(
            select(InternshipPosition).where(InternshipPosition.company_id == company_id)
        ).all()


class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, application: Application) -> Application:
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def get_by_id(self, application_id: int) -> Optional[Application]:
        return self.db.get(Application, application_id)

    def get_by_student_and_internship(self, student_id: int, internship_id: int) -> Optional[Application]:
        statement = select(Application).where(
            Application.student_id == student_id,
            Application.internship_id == internship_id
        )
        return self.db.exec(statement).first()

    def get_by_internship(self, internship_id: int) -> list[Application]:
        return self.db.exec(select(Application).where(Application.internship_id == internship_id)).all()

    def list_all(self) -> list[Application]:
        return self.db.exec(select(Application)).all()


class MatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, match: Match) -> Match:
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        return match

    def get_by_application(self, application_id: int) -> Optional[Match]:
        statement = select(Match).where(Match.application_id == application_id)
        return self.db.exec(statement).first()

    def update(self, match: Match) -> Match:
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        return match

    def list_all(self) -> list[Match]:
        return self.db.exec(select(Match)).all()
