from __future__ import annotations

import os


from fastapi import FastAPI


from .vqe.model import VqeRequest, VqeResponse
from .vqe.executor import vqe_executor

app = FastAPI()

PRODUCTION_ENV = os.environ.get("PRODUCTION_ENV", False)


@app.get("/")
async def hello():
    return {"Hello, World!"}


@app.post("/vqe/")
async def vqe(req: VqeRequest) -> VqeResponse:
    status, result = vqe_executor(req.input)
    return VqeResponse(status=status, result=result)
