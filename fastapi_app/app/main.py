# fastapi_app/app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.v1 import orders
from pathlib import Path
from fastapi import Request

app = FastAPI(title="Trading System")

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# API 라우터 등록
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request})
