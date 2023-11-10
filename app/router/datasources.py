from fastapi import APIRouter, Depends, status, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from fastapi.responses import JSONResponse
import sys
sys.path.append("/Users/michaelchee/Documents/backend/app")
from database import get_db, get_mongo_collection,get_redis_client
from pymongo.collection import Collection
import utils, schemas,models
from redis import Redis
import pandas as pd
import redis
from bson import ObjectId
from analysis.text2sql import Text2SQL

router = APIRouter(
    prefix="/datasources",
    tags=['DataSources']
)

@router.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...),access_token :str =  Header(None),db:Session = Depends(get_db), collection: Collection = Depends(get_mongo_collection), r:Redis = Depends(get_redis_client)):
    current_user = utils.authentication(access_token,db)
    try:
        df = pd.read_csv(file.file)
        json_data = df.to_dict(orient='records')
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty")
    except pd.errors.ParserError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to parse CSV file")
    store_data = {"store_data": json_data}
    # Insert data into MongoDB (for caching)
    try:
        insert_result = collection.insert_one(store_data)
        id = insert_result.inserted_id
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to insert data into MongoDB: {str(e)}")
    try:
        r.setex(f"{current_user.user_id}:csv_data_id", 86400, str(id))
    except redis.RedisError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to interact with Redis: {str(e)}")
    return {"filename":file.filename,"csv_id":str(id)} 

@router.get("/delete_csv")
async def delete_csv(access_token :str =  Header(None),db:Session = Depends(get_db), collection: Collection = Depends(get_mongo_collection), r:Redis = Depends(get_redis_client)):
    current_user = utils.authentication(access_token,db)
    try:
        csv_id = r.get(f"{current_user.user_id}:csv_data_id")
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to connect to the Redis server")
    if not csv_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User don't have such csv file with user id: {current_user.user_id}")
    csv_id = csv_id.decode('utf-8')
    # Specify the ObjectId of the document you want to delete
    delete_id = ObjectId(csv_id)
    try:
        # Delete the document with the specified ObjectId
        collection.delete_one({'_id': delete_id})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete csv data: {str(e)}")
    try:
        r.delete(f"{current_user.user_id}:csv_data_id")
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to connect to the Redis server")
    return JSONResponse(content={"message": f"Successfully delete csv data with id: {csv_id}"}, status_code=200)

@router.post("/add_database")
async def add_database(connections: schemas.DatabaseConnection, db:Session = Depends(get_db), access_token :str =  Header(None)):
    current_user = utils.authentication(access_token,db)
    database_key = f"{connections.database_host}:{connections.database_name}:{connections.database_user}:{connections.database_password}"
    db_connections = db.query(models.ClientDatabaseInfo).filter(models.ClientDatabaseInfo.user_id == current_user.user_id).all()
    for connection in db_connections:
        if utils.decrypt_data(connection.database_keys) == database_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Connection exists.")
    encrypted_key = utils.encrypt_data(database_key)
    new_connection = models.ClientDatabaseInfo(**{"user_id":current_user.user_id,"database_keys":encrypted_key.decode()})
    try:
        # Attempt to insert the log
        db.add(new_connection)
        db.commit()
        db.refresh(new_connection)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to connect to database: {str(e)}")
    return connections

@router.post("/connect_database")
async def add_database(connections: schemas.DatabaseConnection, db:Session = Depends(get_db), access_token :str =  Header(None),r:Redis = Depends(get_redis_client)):
    current_user = utils.authentication(access_token,db)
    database_key = f"{connections.database_host}:{connections.database_name}:{connections.database_user}:{connections.database_password}"
    db_connections = db.query(models.ClientDatabaseInfo).filter(models.ClientDatabaseInfo.user_id == current_user.user_id).all()
    connection_exists = False
    for connection in db_connections:
        if utils.decrypt_data(connection.database_keys) == database_key:
            connection_exists = True
    if not connection_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connection not found.")
    db_uri = f"mysql+pymysql://{connections.database_user}:{connections.database_password}@{connections.database_host}/{connections.database_name}"
    try:
        create_engine(db_uri)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database Connection Failed.")
    try:
        r.setex(f"{current_user.user_id}:database_connection", 86400, db_uri)
    except redis.RedisError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to interact with Redis: {str(e)}")
    return JSONResponse(content={"message": f"Connect Database sucessful."}, status_code=200)
