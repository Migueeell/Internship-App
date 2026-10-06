from typing import Literal

from fastapi import Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import DepartmentDep
from app.dependencies.session import SessionDep
from app.repositories.internship import ApplicationRepository, InternshipPositionRepository, MatchRepository
from app.repositories.user import UserRepository
from app.services.internship_service import InternshipService
from app.utilities.flash import flash
from . import router, templates


@router.get("/department", response_class=HTMLResponse, name="department_home_view")
async def department_home_view(
    request: Request,
    user: DepartmentDep,
    db: SessionDep,
    status_filter: Literal["pending", "approved", "rejected", "all"] = Query(default="pending"),
):
    service = InternshipService(
        position_repo=InternshipPositionRepository(db),
        application_repo=ApplicationRepository(db),
        match_repo=MatchRepository(db),
        user_repo=UserRepository(db),
    )
    dashboard = service.get_match_dashboard(status_filter)
    return templates.TemplateResponse(
        request=request,
        name="department_dashboard.html",
        context={
            "user": user,
            **dashboard,
        },
    )

@router.post("/department/match", response_class=HTMLResponse, name="match_application")
async def match_application(
    request: Request,
    user: DepartmentDep,
    db: SessionDep,
    application_id: int = Form(...),
    approval_status: str = Form(...),
    notes: str = Form(default=""),
):
    service = InternshipService(
        position_repo=InternshipPositionRepository(db),
        application_repo=ApplicationRepository(db),
        match_repo=MatchRepository(db),
        user_repo=UserRepository(db),
    )
    try:
        service.match_application(application_id, user.id, approval_status, notes)
    except ValueError as e:
        flash(request, str(e), "danger")
        return RedirectResponse(request.url_for("department_home_view"), status_code=status.HTTP_303_SEE_OTHER)
    flash(request, "Match decision recorded.", "success")
    return RedirectResponse(request.url_for("department_home_view"), status_code=status.HTTP_303_SEE_OTHER)
