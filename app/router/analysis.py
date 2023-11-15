from fastapi import APIRouter, Depends, status, HTTPException, Header, Request
from sqlalchemy.orm import Session
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(app_dir)
from ..database import get_db, get_redis_client
from .. import schemas, utils
from redis import ConnectionError, Redis
from fastapi.responses import JSONResponse, StreamingResponse
from ..analysis.utils import get_recommendation, get_analysis_recommendation, test_streamimg
from ..analysis.text2sql import Text2SQL
import pandas as pd
import json
from openai import OpenAI
from ..config import settings

router = APIRouter(
    prefix="/analysis",
    tags=['Analysis']
)

@router.post("/store_message")
async def store_message(user_input:schemas.UserInput,r:Redis = Depends(get_redis_client)):
    r.setex(f"test_message", 60, user_input.message)
    return JSONResponse(content={"message": "Successfully store message"}, status_code=200)


@router.get("/test_response")
async def test_response(request: Request, r:Redis = Depends(get_redis_client)):
    message = r.get("test_message")
    if message:
        message = message.decode('utf-8')
    print("Message: ", message)
    response = StreamingResponse(test_streamimg(message), media_type="text/event-stream",headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",  # Enable CORS, adjust this to match your frontend's origin
    })
    return response


@router.post("/store_analysis_data")
async def store_analysis_data(user_input:schemas.UserInput,access_token :str =  Header(None),db:Session = Depends(get_db), r:Redis = Depends(get_redis_client)):
    current_user = utils.authentication(access_token,db)
    try:
        r.setex(f"{current_user.user_id}:message", 60, user_input.message)
        r.setex(f"{current_user.user_id}:data", 60, json.dumps(user_input.data))
        r.setex(f"{current_user.user_id}:industry", 60, user_input.industry)
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to connect to the Redis server")
    return JSONResponse(content={"message": "Successfully store analysis data"}, status_code=200)

@router.get("/recommendation/{language}")
async def recommendation(language:str, access_token :str =  Header(None), db:Session = Depends(get_db),r:Redis = Depends(get_redis_client)):
    current_user = utils.authentication(access_token,db)
    # Handle Redis connection errors
    try:
        message = r.get(f"{current_user.user_id}:message")
        analysis_results = r.get(f"{current_user.user_id}:data")
        industry = r.get(f"{current_user.user_id}:industry")
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to connect to the Redis server")
    if not message or not analysis_results or not industry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Can't get message, analysis results or industry.")
    message = message.decode('utf-8')
    analysis_results = analysis_results.decode('utf-8')
    industry = industry.decode('utf-8')
    response = StreamingResponse(get_recommendation(message,analysis_results, industry,language), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    return response

@router.post("/text2sql")
async def text2sql(user_input:schemas.UserInput,access_token :str =  Header(None),db:Session = Depends(get_db),r:Redis = Depends(get_redis_client)):
    current_user = utils.authentication(access_token,db)
    try:
        db_uri = r.get(f"{current_user.user_id}:database_connection")
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to connect to the Redis server")
    db_uri = db_uri.decode('utf-8')
    text2sql = Text2SQL(db_uri)
    analysis_steps, sql_query = text2sql.get_sql_query(user_input.message,user_input.industry)
    if not sql_query or "Error" in sql_query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Generate SQL Query got error.")
    return {"analysis_steps":analysis_steps,"sql_query": sql_query}

@router.get("/get_analysis_results/{language}")
async def get_analysis_results(language:str, access_token :str =  Header(None),db:Session = Depends(get_db), r:Redis = Depends(get_redis_client)):
    current_user = utils.authentication(access_token,db)
    # Handle Redis connection errors
    try:
        message = r.get(f"{current_user.user_id}:message")
        analysis_results = r.get(f"{current_user.user_id}:data")
        industry = r.get(f"{current_user.user_id}:industry")
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to connect to the Redis server")
    if not message or not analysis_results or not industry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Can't get message, analysis results or industry.")
    message = message.decode('utf-8')
    analysis_results = analysis_results.decode('utf-8')
    industry = industry.decode('utf-8')
    # Read JSON file into a DataFrame
    try:
        df = pd.read_json(json.loads(analysis_results)).to_string()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Can't load data.")
    response = StreamingResponse(get_analysis_recommendation(message,df, industry,language), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    return response
    





