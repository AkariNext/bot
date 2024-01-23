from fastapi import Request


async def get_current_path(request: Request) -> str:
    return request.scope['root_path'] + request.scope['route'].path
