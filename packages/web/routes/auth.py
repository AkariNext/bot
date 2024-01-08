import aiohttp
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from packages.shared.config import settings
from packages.shared.infrastructure.database import session
from packages.shared.models import AuthRequest

class Auth(BaseModel):
    response: str

router = APIRouter()
templates = Jinja2Templates(directory="packages/web/templates")


@router.get('/auth/{auth_id}')
async def get_auth(request: Request, auth_id: str):
    hitRequest = session.query(AuthRequest).filter(AuthRequest.id == auth_id).first()
    if hitRequest is None:
        return {'error': 'not found'}
    return templates.TemplateResponse('auth.html', {'request': request, 'requestId': hitRequest.id})
    

@router.post('/auth/{auth_id}')
async def post_auth(auth_id: str, auth: Auth):
    async with aiohttp.ClientSession() as client:
        res = await client.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', json={'response': auth.response, 'secret': settings.turnstile_secret, 'domain': settings.domain})
        data = await res.json()
        is_success = data.get('success', False)
        if not is_success:
            return {'error': 'invalid response'}
        print(is_success)
        hitRequest = session.query(AuthRequest).filter(AuthRequest.id == auth_id).first()
        if hitRequest is None:
            return {'error': 'not found'}
        hitRequest.is_completed = True
        session.commit()
    return {'auth_id': auth_id}
