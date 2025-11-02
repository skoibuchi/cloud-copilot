from fastapi import FastAPI
from app.api import auth, cloud_config, cloud_resources, chat
from app.database.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.create_admin import create_admin_user

Base.metadata.create_all(bind=engine)

# create admin user
create_admin_user()

app = FastAPI(title="Cloud Support AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cloud_config.router)
app.include_router(cloud_resources.router)
app.include_router(chat.router)
