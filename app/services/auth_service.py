from typing import Optional

from app.repositories.user import UserRepository
from app.models.user import USER_ROLES
from app.schemas.user import RegularUserCreate
from app.utilities.security import create_access_token, encrypt_password, verify_password


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(self, username: str, password: str, role: str | None = None) -> Optional[str]:
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        if user.role not in USER_ROLES or (role and role not in USER_ROLES):
            return None
        if role and user.role != role:
            return None
        if not verify_password(plaintext_password=password, encrypted_password=user.password):
            return None
        access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role})
        return access_token

    def register_user(self, username: str, email: str, password: str, role: str = "student", full_name: str | None = None):
        if role not in USER_ROLES:
            raise ValueError("Choose Student, Company, or Department.")
        new_user = RegularUserCreate(
            username=username,
            email=email,
            password=encrypt_password(password),
            role=role,
            full_name=full_name or username,
        )
        return self.user_repo.create(new_user)

    def migrate_legacy_admin_account(self) -> bool:
        legacy_admin = self.user_repo.get_by_username("admin")
        if legacy_admin is None or legacy_admin.role != "admin":
            return False

        existing_department = self.user_repo.get_by_username("department")
        if existing_department is not None and existing_department.id != legacy_admin.id:
            raise ValueError(
                "Cannot convert the legacy admin account because a separate "
                "'department' account already exists."
            )
        email_owner = self.user_repo.get_by_email("department@example.com")
        if email_owner is not None and email_owner.id != legacy_admin.id:
            raise ValueError(
                "Cannot convert the legacy admin account because "
                "department@example.com is already in use."
            )

        legacy_admin.username = "department"
        legacy_admin.email = "department@example.com"
        legacy_admin.password = encrypt_password("departmentpass")
        legacy_admin.full_name = "Department Administrator"
        legacy_admin.role = "department"
        self.user_repo.update(legacy_admin)
        return True
