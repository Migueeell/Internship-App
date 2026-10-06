"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.internship import Application, InternshipPosition, Match
from app.models.user import User

__all__ = ["User", "InternshipPosition", "Application", "Match"]
