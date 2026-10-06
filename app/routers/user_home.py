from datetime import date

from fastapi import File, Form, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import StudentDep, CompanyDep
from app.dependencies.session import SessionDep
from app.repositories.internship import ApplicationRepository, InternshipPositionRepository, MatchRepository
from app.repositories.user import UserRepository
from app.services.internship_service import InternshipService
from app.utilities.flash import flash
from . import router, templates


@router.get("/app", response_class=HTMLResponse, name="user_home_view")
async def user_home_view(
    request: Request,
    user: StudentDep,
    db: SessionDep,
    keyword: str = Query(default=""),
    company: str = Query(default=""),
    location: str = Query(default=""),
):
    return await student_home_view(
        request=request,
        user=user,
        db=db,
        keyword=keyword,
        company=company,
        location=location,
    )


@router.get("/student", response_class=HTMLResponse, name="student_home_view")
async def student_home_view(
    request: Request,
    user: StudentDep,
    db: SessionDep,
    keyword: str = Query(default=""),
    company: str = Query(default=""),
    location: str = Query(default=""),
):
    service = InternshipService(
        position_repo=InternshipPositionRepository(db),
        application_repo=ApplicationRepository(db),
        match_repo=MatchRepository(db),
        user_repo=UserRepository(db),
    )
    positions = service.search_positions(keyword=keyword, company=company, location=location)
    return templates.TemplateResponse(
        request=request,
        name="student_dashboard.html",
        context={
            "user": user,
            "positions": positions,
            "keyword": keyword,
            "company": company,
            "location": location,
        },
    )


@router.get("/company", response_class=HTMLResponse, name="company_home_view")
async def company_home_view(request: Request, user: CompanyDep, db: SessionDep):
    positions = InternshipPositionRepository(db).list_by_company(user.id)
    return templates.TemplateResponse(
        request=request,
        name="company_dashboard.html",
        context={
            "user": user,
            "positions": positions,
        },
    )


@router.get("/internships/{position_id}", response_class=HTMLResponse, name="internship_detail_view")
async def internship_detail_view(request: Request, user: StudentDep, db: SessionDep, position_id: int):
    position_repo = InternshipPositionRepository(db)
    service = InternshipService(
        position_repo=position_repo,
        application_repo=ApplicationRepository(db),
        match_repo=MatchRepository(db),
        user_repo=UserRepository(db),
    )
    position = service.get_position(position_id)
    if not position:
        flash(request, "Internship not found.", "danger")
        return RedirectResponse(request.url_for("student_home_view"), status_code=status.HTTP_303_SEE_OTHER)
    company = service.get_company(position.company_id)
    if company is None:
        flash(request, "Company profile not found.", "danger")
        return RedirectResponse(request.url_for("student_home_view"), status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="internship_detail.html",
        context={
            "user": user,
            "position": position,
            "company": company,
        },
    )


@router.post("/company/internships", response_class=HTMLResponse, name="create_internship_position")
async def create_internship_position(
    request: Request,
    user: CompanyDep,
    db: SessionDep,
    title: str = Form(...),
    description: str = Form(...),
    requirements: str = Form(...),
    location: str = Form(...),
    application_deadline: date = Form(...),
):
    service = InternshipService(
        position_repo=InternshipPositionRepository(db),
        application_repo=ApplicationRepository(db),
        match_repo=MatchRepository(db),
        user_repo=UserRepository(db),
    )
    try:
        service.create_position(
            company_id=user.id,
            title=title,
            description=description,
            requirements=requirements,
            location=location,
            application_deadline=application_deadline,
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(request.url_for("company_home_view"), status_code=status.HTTP_303_SEE_OTHER)
    flash(request, "Internship position created successfully.", "success")
    return RedirectResponse(request.url_for("company_home_view"), status_code=status.HTTP_303_SEE_OTHER)


@router.get(
    "/company/internships/{position_id}/edit",
    response_class=HTMLResponse,
    name="edit_internship_position",
)
async def edit_internship_position_view(
    request: Request,
    user: CompanyDep,
    db: SessionDep,
    position_id: int,
):
    service = InternshipService(
        position_repo=InternshipPositionRepository(db),
        application_repo=ApplicationRepository(db),
        match_repo=MatchRepository(db),
        user_repo=UserRepository(db),
    )
    position = service.get_company_position(user.id, position_id)
    if position is None:
        flash(request, "Internship position not found.", "danger")
        return RedirectResponse(request.url_for("company_home_view"), status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="internship_edit.html",
        context={
            "user": user,
            "position": position,
        },
    )


@router.post(
    "/company/internships/{position_id}/edit",
    response_class=HTMLResponse,
    name="update_internship_position",
)
async def update_internship_position(
    request: Request,
    user: CompanyDep,
    db: SessionDep,
    position_id: int,
    title: str = Form(...),
    description: str = Form(...),
    requirements: str = Form(...),
    location: str = Form(...),
    application_deadline: date = Form(...),
):
    service = InternshipService(
        position_repo=InternshipPositionRepository(db),
        application_repo=ApplicationRepository(db),
        match_repo=MatchRepository(db),
        user_repo=UserRepository(db),
    )
    try:
        service.update_position(
            company_id=user.id,
            position_id=position_id,
            title=title,
            description=description,
            requirements=requirements,
            location=location,
            application_deadline=application_deadline,
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(
            request.url_for("edit_internship_position", position_id=position_id),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    flash(request, "Internship position updated.", "success")
    return RedirectResponse(request.url_for("company_home_view"), status_code=status.HTTP_303_SEE_OTHER)


@router.post(
    "/company/internships/{position_id}/close",
    response_class=HTMLResponse,
    name="close_internship_position",
)
async def close_internship_position(
    request: Request,
    user: CompanyDep,
    db: SessionDep,
    position_id: int,
):
    service = InternshipService(
        position_repo=InternshipPositionRepository(db),
        application_repo=ApplicationRepository(db),
        match_repo=MatchRepository(db),
        user_repo=UserRepository(db),
    )
    try:
        service.close_position(company_id=user.id, position_id=position_id)
    except ValueError as exc:
        flash(request, str(exc), "danger")
    else:
        flash(request, "Internship listing closed.", "success")
    return RedirectResponse(request.url_for("company_home_view"), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/internships/{position_id}/apply", response_class=HTMLResponse, name="apply_to_internship")
async def apply_to_internship(
    request: Request,
    user: StudentDep,
    db: SessionDep,
    position_id: int,
    resume: UploadFile = File(...),
    cover_letter: str = Form(...),
):
    service = InternshipService(
        position_repo=InternshipPositionRepository(db),
        application_repo=ApplicationRepository(db),
        match_repo=MatchRepository(db),
        user_repo=UserRepository(db),
    )
    try:
        service.apply_for_position(student_id=user.id, internship_id=position_id, resume_file=resume, cover_letter=cover_letter)
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(request.url_for("internship_detail_view", position_id=position_id), status_code=status.HTTP_303_SEE_OTHER)
    flash(request, "Application submitted successfully.", "success")
    return RedirectResponse(request.url_for("student_home_view"), status_code=status.HTTP_303_SEE_OTHER)
