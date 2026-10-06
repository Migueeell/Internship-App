from __future__ import annotations

from datetime import date, datetime, timezone
from sqlmodel import Field, SQLModel

class InternshipPositionBase(SQLModel):
    company_id: int = Field(foreign_key="user.id", index=True)
    title: str = Field(index=True)
    description: str
    requirements: str
    location: str
    application_deadline: date = Field(description="Deadline for applications")
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ApplicationCreate(SQLModel):
    student_id: int = Field(foreign_key="user.id", index=True)
    internship_id: int = Field(foreign_key="internship_position.id", index=True)
    resume_path: str = Field(default="", description="Path to the uploaded resume PDF")
    cover_letter: str = Field(default="", description="Cover letter text")
    status: str = Field(default="pending")
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))