from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel



class InternshipPositionBase(SQLModel):
    company_id: int = Field(foreign_key="user.id", index=True)
    title: str = Field(index=True)
    description: str
    requirements: str
    location: str
    application_deadline: date
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InternshipPosition(InternshipPositionBase, table=True):
    __tablename__ = "internship_position"

    id: Optional[int] = Field(default=None, primary_key=True)


class ApplicationBase(SQLModel):
    student_id: int = Field(foreign_key="user.id", index=True)
    internship_id: int = Field(foreign_key="internship_position.id", index=True)
    resume_path: str = Field(default="", description="Path to the uploaded resume PDF")
    cover_letter: str = Field(default="", description="Cover letter text")
    status: str = Field(default="pending")
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Application(ApplicationBase, table=True):
    __tablename__ = "application"

    id: Optional[int] = Field(default=None, primary_key=True)


class MatchBase(SQLModel):
    application_id: int = Field(foreign_key="application.id", unique=True, index=True)
    department_admin_id: int = Field(foreign_key="user.id", index=True)
    approval_status: str = Field(default="pending")
    notes: str = Field(default="", description="Notes about the match")
    matched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Match(MatchBase, table=True):
    __tablename__ = "match"

    id: Optional[int] = Field(default=None, primary_key=True)