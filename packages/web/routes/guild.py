from fastapi import APIRouter

router = APIRouter()

@router.get("/guild/{guild_id}")
async def get_guild(guild_id: int):
    return {"guild_id": guild_id}
