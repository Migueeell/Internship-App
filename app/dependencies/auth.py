from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
import jwt
from jwt.exceptions import InvalidTokenError
from app.config import get_settings
from app.models.user import USER_ROLES, User
from app.dependencies.session import SessionDep
from app.repositories.user import UserRepository

async def get_current_user(request:Request, db:SessionDep)->User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = request.cookies.get("access_token")

    if token is None:
        raise credentials_exception
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().jwt_algorithm])
        user_id = payload.get("sub",None)
    except InvalidTokenError as e:
        print("Invalid token error: ", e)
        raise credentials_exception

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if user is None or user.role not in USER_ROLES:
        raise credentials_exception
    return user

async def is_logged_in(request: Request, db:SessionDep):
    try:
        await get_current_user(request, db)
        return True
    except Exception:
        return False

IsUserLoggedIn = Annotated[bool, Depends(is_logged_in)]
AuthDep = Annotated[User, Depends(get_current_user)]

async def is_student_dep(user: AuthDep):
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit internship applications",
        )
    return user

StudentDep = Annotated[User, Depends(is_student_dep)]

async def is_company_dep(user: AuthDep):
    if user.role != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company accounts can create internship positions",
        )
    return user

CompanyDep = Annotated[User, Depends(is_company_dep)]

async def is_department_dep(user: AuthDep):
    if user.role != "department":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only department accounts can review matches",
        )
    return user

DepartmentDep = Annotated[User, Depends(is_department_dep)]
