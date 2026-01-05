from fastapi import APIRouter

from app.api.v1 import categories, products, stock

api_router = APIRouter()

api_router.include_router(products.router)
api_router.include_router(categories.router)
api_router.include_router(stock.router)
