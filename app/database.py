from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from pymongo.collection import Collection
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from redis.client import Redis
import redis
import sys
sys.path.append("/Users/michaelchee/Documents/backend/app")
from config import settings

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{settings.db_user}:{settings.db_password}@{settings.db_host}/{settings.db_name}"
MONGO_DATABASE_URL = f"mongodb://{settings.mongo_db_host}:27017/"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_mongo_collection()-> Collection:
    try:
        client = MongoClient(MONGO_DATABASE_URL)
        db = client[settings.mongo_db_name]
        collection = db[settings.mongo_db_collection]
        # Create a TTL index on the "expireAt" field, expiring documents after 1 day
        collection.create_index("expireAt", expireAfterSeconds=0)
        yield collection
    finally:
        client.close()

def get_redis_client() -> Redis:
    try:
        redis_client = redis.Redis(host=settings.redis_db_host)
        yield redis_client
    finally:
        redis_client.close()
