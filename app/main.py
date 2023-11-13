from fastapi import FastAPI, Request, HTTPException, status
import sys, os, asyncio, time
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import iterate_in_threadpool

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(app_dir)
from .database import Base, engine
from .router import auth, audit_trail,analysis,datasources
from .logger import logger
from .kafka.consumers import consumer_manager
from .kafka.producers import producer_manager
from .kafka import config
from .config import settings
from . import utils

# 创建数据库表格
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(auth.router)
app.include_router(audit_trail.router)
app.include_router(analysis.router)
app.include_router(datasources.router)


"""Define the post-request hook to save the response"""
@app.middleware("http")
async def log_response(request: Request, call_next):
    try:
        """Call the next middleware or the endpoint handler
            to execute the request and generate the response"""
        start = time.time()
        request.state.app = app
        request_id = utils.generate_unique_id()
        request_body = await request.body()
        await utils.set_body(request, request_body)

        response = await call_next(request)

        response_body = [chunk async for chunk in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(response_body))
        response_body = response_body[0].decode() if response_body else ""
        request_body_str = request_body.decode('utf-8') 

        request_data = {
            "request_id": request_id,
            "method": request.method,
            "url_path": request.url.path,
            "query_params": str(dict(request.query_params)),
            "request_headers": str(dict(request.headers)),
            "request_body": request_body_str,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
            "cookies": str(dict(request.cookies)),
            "route_name": ""
        }

        response_data = {
            "request_id": request_id,
            "response_id": utils.generate_unique_id(),
            "response_status_code": response.status_code,
            "response_headers": str(dict(response.headers)),
            "response_body": response_body,
        }
        
        save_request_kafka_value = {
            "action": config.KafkaTopic.SAVE_REQUEST_TO_DB,
            "data": request_data
        }

        save_response_kafka_value = {
            "action": config.KafkaTopic.SAVE_RESPONSE_TO_DB,
            "data": response_data
        }

        await producer_manager.send(
            topic=config.KafkaTopic.SAVE_REQUEST_TO_DB,
            value = save_request_kafka_value,
        ) 
        await producer_manager.send(
            topic=config.KafkaTopic.SAVE_RESPONSE_TO_DB,
            value = save_response_kafka_value,
        )

        logger.info(f'Time take for log_response is {time.time()-start}s')
        
        """Return the response as usual"""
        return response

    except Exception as e:
        logger.error(f"An error occurred while saving the response: {e}", exc_info=sys.exc_info())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal server error")



@app.on_event("startup")
async def startup_event():
    logger.info('Initializing API ...')
    await consumer_manager.create_bg_consumer(
        topic=config.KafkaTopic.SAVE_REQUEST_TO_DB
    )
    await consumer_manager.create_bg_consumer(
        topic=config.KafkaTopic.SAVE_RESPONSE_TO_DB
    )
    await consumer_manager.create_bg_consumer(
        topic=config.KafkaTopic.WRITE_DB,
        group_id="write_db"
    )
    await consumer_manager.create_bg_consumer(
        topic=config.KafkaTopic.UPDATE_DB,
        group_id="update_db"
    )
    await consume()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info('Shutting down API')
    if config.Task.SAVE_RESPONSE_TO_DB is not None:
        config.Task.SAVE_REQUEST_TO_DB.cancel()
    if config.Task.SAVE_RESPONSE_TO_DB is not None:
        config.Task.SAVE_RESPONSE_TO_DB.cancel()
    if config.Task.WRITE_DB is not None:
        config.Task.WRITE_DB.cancel()
    if config.Task.UPDATE_DB is not None:
        config.Task.UPDATE_DB.cancel()

    await consumer_manager.stop_consumer(
        topic=config.KafkaTopic.SAVE_REQUEST_TO_DB
    )
    await consumer_manager.stop_consumer(
        topic=config.KafkaTopic.SAVE_RESPONSE_TO_DB
    )
    await consumer_manager.stop_consumer(
        topic=config.KafkaTopic.WRITE_DB
    )
    await consumer_manager.stop_consumer(
        topic=config.KafkaTopic.UPDATE_DB
    )

async def consume():
    config.Task.SAVE_REQUEST_TO_DB = asyncio.create_task(
        consumer_manager.bg_consume(
            topic=config.KafkaTopic.SAVE_REQUEST_TO_DB
        )
    )
    config.Task.SAVE_RESPONSE_TO_DB = asyncio.create_task(
        consumer_manager.bg_consume(
            topic=config.KafkaTopic.SAVE_RESPONSE_TO_DB
        )
    )
    config.Task.WRITE_DB = asyncio.create_task(
        consumer_manager.bg_consume(
            topic=config.KafkaTopic.WRITE_DB
        )
    )
    config.Task.UPDATE_DB = asyncio.create_task(
        consumer_manager.bg_consume(
            topic=config.KafkaTopic.UPDATE_DB
        )
    )

@app.get("/")
async def root():
    return {"message": f"Welcome to my api {settings.instance_name}"}