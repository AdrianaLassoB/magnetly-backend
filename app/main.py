from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.marketing import router as marketing_router
from app.routers.products import router as products_router
from app.routers.trends import router as trends_router

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health_check():
    return {
        'status': 'ok',
        'app': settings.app_name,
        'positioning': 'Marketing intelligence for fast growing D2C home goods brands',
    }


app.include_router(marketing_router)
app.include_router(products_router)
app.include_router(trends_router)
