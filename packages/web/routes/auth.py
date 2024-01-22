import aiohttp
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from packages.shared.config import settings
from packages.shared.infrastructure.database import get_db
from packages.shared.models import AuthRequest
from packages.web.const import TEMPLATES


class Auth(BaseModel):
    response: str


router = APIRouter()


@router.get("/auth/{auth_id}")
async def get_auth(request: Request, auth_id: str, db: Session = Depends(get_db)):
    hitRequest = db.query(AuthRequest).filter(AuthRequest.id == auth_id).first()
    if hitRequest is None:
        return {"error": "not found"}
    return TEMPLATES.TemplateResponse(
        "auth.html", {"request": request, "requestId": hitRequest.id}
    )


@router.post("/auth/{auth_id}")
async def post_auth(auth_id: str, auth: Auth, db: Session = Depends(get_db)):
    async with aiohttp.ClientSession() as client:
        res = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            json={
                "response": auth.response,
                "secret": settings.turnstile_secret,
                "domain": settings.domain,
            },
        )
        data = await res.json()
        is_success = data.get("success", False)
        if not is_success:
            return {"error": "invalid response"}
        print(is_success)
        hitRequest = db.query(AuthRequest).filter(AuthRequest.id == auth_id).first()
        if hitRequest is None:
            return {"error": "not found"}
        hitRequest.is_completed = True
        db.commit()
    return {"auth_id": auth_id}
