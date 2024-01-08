from glob import glob
from importlib import import_module
from pathlib import PurePath
from fastapi.templating import Jinja2Templates

import uvicorn
from fastapi import FastAPI

app = FastAPI()


for route in glob("packages/web/routes/*.py"):
    if "__init__" in route:
        continue
    
    app.include_router(
        import_module(
            PurePath(route).as_posix()[:-3].replace("/", ".")
        ).router
    )


def run():
    uvicorn.run(app, host="0.0.0.0", loop="asyncio")
