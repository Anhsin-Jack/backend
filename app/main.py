from fastapi import FastAPI
from .database import Base, engine
from .router import user, auth, audit_trail
from fastapi.middleware.cors import CORSMiddleware

# 创建数据库表格
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


app.include_router(user.router)
app.include_router(auth.router)
app.include_router(audit_trail.router)