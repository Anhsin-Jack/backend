import sys, time
from fastapi import HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Tuple, Union
import datetime

import os

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(app_dir)
from .. import models
from ..database import SessionLocal
from . import config
from ..logger import logger

async def write_db(
        data: dict,
        schemas: str, 
        db: Session = SessionLocal(),
        max_retries: int = 3,
        retry_delay: float = 1.0  
    ):
    """
    Write the request details to the database.

    Args:
        data: The request object containing additional database object information.
        schemas (str): The SQLAlchemy model to operate on.
        db (Session): The database session.
        max_retries (int): The maximum number of retry attempts on SQLAlchemy errors.
        retry_delay (float): The delay between retry attempts in seconds.

    Raises:
        HTTPException: If any unexpected error occurs while saving the request.
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            match schemas:
                case config.DatabaseSchemas.USER:
                    new_request = models.User(**data)
                case config.DatabaseSchemas.USER_PROFILE:
                    new_request = models.UserProfile(**data)
                case config.DatabaseSchemas.AUDIT_TRAIL:
                    new_request = models.AuditTrail(**data)
                case config.DatabaseSchemas.CSUITE_DASHBOARD_CATEGORIES:
                    new_request = models.CSuiteDashboardCategories(**data)
                case config.DatabaseSchemas.CSUITE_DASHBOARD:
                    new_request = models.CSuiteDashboard(**data)
                case config.DatabaseSchemas.TEXT2SQL:
                    new_request = models.Text2SQL(**data)
                case config.DatabaseSchemas.TECHNICAL_CHATBOT_RESPONSE:
                    new_request = models.TechnicalChatbotResponse(**data)
                case config.DatabaseSchemas.CSUITE_CHATBOT_RESPONSE:
                    new_request = models.CSuiteChatbotResponse(**data)
                case config.DatabaseSchemas.CLIENT_DATABASE_INFO:
                    new_request = models.ClientDatabaseInfo(**data)
            
            db.add(new_request)
            db.commit() 
            db.refresh(new_request)

            """if successful, break out of the loop"""
            break

        except SQLAlchemyError as sqla_error:
            if db is not None:
                """Rollback the transaction in case of an SQLAlchemy error"""
                db.rollback() 
                db.close()

            logger.error(
                "SQLAlchemy error occurred while writing data to db: "
                f"{str(sqla_error)}. "
                f"Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
            retry_count += 1
        
        except Exception as e:
            logger.error(
                f"An error occurred while writing data to db: {e}", 
                exc_info=sys.exc_info()
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
        finally:
            db.close()

    else:
        logger.error(
            "Max retries reached. Unable to establish database connection "
            "while writing data to db"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

async def read_db(
        schemas: str,  
        operation: str,
        columns: List[str] = None,
        filters: List[Tuple[str, str]] = None,
        db: Session = SessionLocal(),
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
    retry_count = 0
    while retry_count < max_retries:
        try:
            match schemas:
                case config.DatabaseSchemas.USER:
                    model = models.User
                case config.DatabaseSchemas.USER_PROFILE:
                    model = models.UserProfile
                case config.DatabaseSchemas.AUDIT_TRAIL:
                    model = models.AuditTrail
                case config.DatabaseSchemas.CSUITE_DASHBOARD_CATEGORIES:
                    model = models.CSuiteDashboardCategories
                case config.DatabaseSchemas.CSUITE_DASHBOARD:
                    model = models.CSuiteDashboard
                case config.DatabaseSchemas.TEXT2SQL:
                    model = models.Text2SQL
                case config.DatabaseSchemas.TECHNICAL_CHATBOT_RESPONSE:
                    model = models.TechnicalChatbotResponse
                case config.DatabaseSchemas.CSUITE_CHATBOT_RESPONSE:
                    model = models.CSuiteChatbotResponse
                case config.DatabaseSchemas.CLIENT_DATABASE_INFO:
                    model = models.ClientDatabaseInfo
            
            
            if operation != "all" and operation != "first":
                raise ValueError(f"Unsupported operation: {operation}")

            """Build the filter conditions dynamically"""
            if filters is not None:
                filter_conditions = []
                for column, operator, value in filters:
                    if operator == "=" or operator == "==":
                        filter_conditions.append(getattr(model, column) == value)
                    elif operator == ">":
                        filter_conditions.append(getattr(model, column) > value)
                    elif operator == "<":
                        filter_conditions.append(getattr(model, column) < value)
                    elif operator == ">=":
                        filter_conditions.append(getattr(model, column) >= value)
                    elif operator == "<=":
                        filter_conditions.append(getattr(model, column) <= value)
                    else:
                        raise ValueError(f"Unsupported operator: {operator}")
            
            if columns is not None:
                """Build a list of expressions for the selected columns"""
                column_expressions = [
                    getattr(model, column) for column in columns
                ]

            """Query the selected columns based on the filter conditions"""
            if filters is None and columns is None:
                query = db.query(model)
            elif filters is None and columns is not None:
                query = db.query(*column_expressions)
            elif filters is not None and columns is None:
                query = db.query(model).filter(*filter_conditions)
            else:
                query = db.query(*column_expressions).filter(
                    *filter_conditions)
                
            if operation == "all":
                return query.all()
            elif operation == "first":
                return query.first()
            
        except SQLAlchemyError as sqla_error:
            if db is not None:
                """Rollback the transaction in case of an SQLAlchemy error"""
                db.rollback() 
                db.close()

            logger.error(
                f"SQLAlchemy error occurred while reading data from db: "
                f"{str(sqla_error)}. "
                f"Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
            retry_count += 1
        
        except Exception as e:
            logger.error(
                f"An error occurred while reading data from db: {e}", 
                exc_info=sys.exc_info()
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
        finally:
            db.close()

    else:
        logger.error(
            "Max retries reached. Unable to establish database connection "
            "while reading data from db"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

async def update_db(
        schemas: str,  
        update_data: List[Tuple[str, Union[bool, int, str]]] = None,
        filters: List[Tuple[str, str, Union[str, int, float]]] = None,
        db: Session = SessionLocal(),
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
    retry_count = 0
    while retry_count < max_retries:
        try:
            match schemas:
                case config.DatabaseSchemas.USER:
                    model = models.User
                case config.DatabaseSchemas.USER_PROFILE:
                    model = models.UserProfile
                case config.DatabaseSchemas.AUDIT_TRAIL:
                    model = models.AuditTrail
                case config.DatabaseSchemas.CSUITE_DASHBOARD_CATEGORIES:
                    model = models.CSuiteDashboardCategories
                case config.DatabaseSchemas.CSUITE_DASHBOARD:
                    model = models.CSuiteDashboard
                case config.DatabaseSchemas.TEXT2SQL:
                    model = models.Text2SQL
                case config.DatabaseSchemas.TECHNICAL_CHATBOT_RESPONSE:
                    model = models.TechnicalChatbotResponse
                case config.DatabaseSchemas.CSUITE_CHATBOT_RESPONSE:
                    model = models.CSuiteChatbotResponse
                case config.DatabaseSchemas.CLIENT_DATABASE_INFO:
                    model = models.ClientDatabaseInfo

            if update_data is None: 
                """If no update_data is provided, raise an error"""
                raise ValueError(
                    "No update_data provided for the update operation."
                )
            
            if filters is None:
                """If no filters is provided, raise an error"""
                raise ValueError(
                    "No conditions provided for the update operation."
                )
            
            """Build the filter conditions dynamically"""
            filter_conditions = []
            for column, operator, value in filters:
                if column == "created_at":
                    value = datetime.datetime.fromisoformat(value)
                if operator == "=" or operator == "==":
                    filter_conditions.append(getattr(model, column) == value)
                elif operator == ">":
                    filter_conditions.append(getattr(model, column) > value)
                elif operator == "<":
                    filter_conditions.append(getattr(model, column) < value)
                elif operator == ">=":
                    filter_conditions.append(getattr(model, column) >= value)
                elif operator == "<=":
                    filter_conditions.append(getattr(model, column) <= value)
                else:
                    raise ValueError(f"Unsupported operator: {operator}")

            """Update based on a list of tuples (column name, value) and the filter conditions"""
            update_dict = {column: value for column, value in update_data}
            db.query(model).filter(*filter_conditions).update(update_dict)
            
            """Commit the changes to the database"""
            db.commit() 

            """if successful, break out of the loop"""
            break

        except SQLAlchemyError as sqla_error:
            if db is not None:
                """Rollback the transaction in case of an SQLAlchemy error"""
                db.rollback() 
                db.close()

            logger.error(
                f"SQLAlchemy error occurred while updating data from db: "
                f"{str(sqla_error)}. "
                f"Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
            retry_count += 1
        
        except Exception as e:
            logger.error(
                f"An error occurred while updating data from db: {e}", 
                exc_info=sys.exc_info()
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
        finally:
            db.close()

    else:
        logger.error(
            "Max retries reached. Unable to establish database connection "
            "while updating data from db"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

async def delete_db(
        schemas: str,  
        filters: List[Tuple[str, str]],
        db: Session = SessionLocal(),
        max_retries: int = 3,
        retry_delay: float = 1.0  
    ):
    """
    Deletes data from a table based on filter conditions.

    Args:
        schemas (str): The SQLAlchemy model to operate on.
        filters (List[Tuple[str, str]]): A list of filter conditions as tuples (column_name, value).
        db (Session): The database session dependency.
        max_retries (int): The maximum number of retry attempts on SQLAlchemy errors.
        retry_delay (float): The delay between retry attempts in seconds.

    Returns:
        Response: A response indicating the successful deletion of data.

    Raises:
        HTTPException: If any error happened in the sqlalchemy
        HTTPException: If the data with the specified filter conditions does not exist, a 404 Not Found error is raised.
        HTTPException: If any other unexpected error occurs, a 500 Internal Server Error is raised.
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            match schemas:
                case config.DatabaseSchemas.USER:
                    model = models.User
                case config.DatabaseSchemas.USER_PROFILE:
                    model = models.UserProfile
                case config.DatabaseSchemas.AUDIT_TRAIL:
                    model = models.AuditTrail
                case config.DatabaseSchemas.CSUITE_DASHBOARD_CATEGORIES:
                    model = models.CSuiteDashboardCategories
                case config.DatabaseSchemas.CSUITE_DASHBOARD:
                    model = models.CSuiteDashboard
                case config.DatabaseSchemas.TEXT2SQL:
                    model = models.Text2SQL
                case config.DatabaseSchemas.TECHNICAL_CHATBOT_RESPONSE:
                    model = models.TechnicalChatbotResponse
                case config.DatabaseSchemas.CSUITE_CHATBOT_RESPONSE:
                    model = models.CSuiteChatbotResponse
                case config.DatabaseSchemas.CLIENT_DATABASE_INFO:
                    model = models.ClientDatabaseInfo

            """Build the filter conditions dynamically"""
            filter_conditions = []
            for column, operator, value in filters:
                if column == "created_at":
                    value = datetime.datetime.fromisoformat(value)
                if operator == "=" or operator == "==":
                    filter_conditions.append(getattr(model, column) == value)
                elif operator == ">":
                    filter_conditions.append(getattr(model, column) > value)
                elif operator == "<":
                    filter_conditions.append(getattr(model, column) < value)
                elif operator == ">=":
                    filter_conditions.append(getattr(model, column) >= value)
                elif operator == "<=":
                    filter_conditions.append(getattr(model, column) <= value)
                else:
                    raise ValueError(f"Unsupported operator: {operator}")
            
            """Query the data based on the filter conditions"""
            data_query = db.query(model).filter(*filter_conditions)
            
            """Get the data based on the filter conditions"""
            data = data_query.all()

            """If no data matching the filter conditions exist, raise a 404 Not Found error"""
            if not data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"No data matching the filter conditions"
                )

            """Delete the data and commit the transaction"""
            data_query.delete(synchronize_session=False)
            db.commit()

            return Response(status_code=status.HTTP_204_NO_CONTENT)

        except SQLAlchemyError as sqla_error:
            if db is not None:
                """Rollback the transaction in case of an SQLAlchemy error"""
                db.rollback() 
                db.close()

            logger.error(
                f"SQLAlchemy error occurred while deleting data from db: "
                f"{str(sqla_error)}. "
                f"Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
            retry_count += 1
        
        except Exception as e:
            logger.error(
                f"An error occurred while deleting data from db: {e}", 
                exc_info=sys.exc_info()
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
        finally:
            db.close()

    else:
        logger.error(
            "Max retries reached. Unable to establish database connection "
            "while deleting data from db"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
async def save_request_to_db(
        request: dict, 
        db: Session = SessionLocal(),
        max_retries: int = 3,
        retry_delay: float = 1.0  
    ):
    """
    Save the request details to the database.

    Args:
        request (Request): The request object containing additional information.
        request_id (str): The ID of the request.
        request_body (str): The body of the request.
        db (Session): The database session.
        max_retries (int): The maximum number of retry attempts on SQLAlchemy errors.
        retry_delay (float): The delay between retry attempts in seconds.

    Raises:
        HTTPException: If any unexpected error occurs while saving the request.
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            """Create a new RequestLog object with the request details and 
                add it to the database"""
            logger.info("saving request")

            request_log = models.RequestLog(
                request_id=request.get("request_id"),
                method=request.get("method"),
                url_path=request.get("url_path"),
                query_params=request.get("query_params"),
                request_headers=request.get("request_headers"),
                request_body=request.get("request_body"),
                client_ip=request.get("client_ip"),
                user_agent=request.get("user_agent"),
                referer=request.get("referer"),
                cookies=request.get("cookies"),
                route_name=request.get("route_name"),
            )

            db.add(request_log)
            db.commit()
            logger.info("done saving request")

            """if successful, break out of the loop"""
            break

        except SQLAlchemyError as sqla_error:
            if db is not None:
                """Rollback the transaction in case of an SQLAlchemy error"""
                db.rollback() 
                db.close()

            logger.error(
                "SQLAlchemy error occurred while saving request to db: "
                f"{str(sqla_error)}. "
                f"Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
            retry_count += 1
        
        except Exception as e:
            logger.error(
                f"An error occurred while saving request to db: {e}",
                exc_info=sys.exc_info()
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
        finally:
            db.close()
    
    else:
        logger.error(
            "Max retries reached. Unable to establish database connection "
            "while saving reqeust to db"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

async def save_response_to_db(
        response: dict, 
        db: Session = SessionLocal(),
        max_retries: int = 3,
        retry_delay: float = 1.0  
    ):
    """
    Save the response details to the database.

    Args:
        request_id (str): The ID of the request.
        response (Response): The response object containing additional information.
        db (Session): The database session.
        max_retries (int): The maximum number of retry attempts on SQLAlchemy errors.
        retry_delay (float): The delay between retry attempts in seconds.

    Raises:
        HTTPException: If any unexpected error occurs while saving the response.
    """
    retry_count = 0
    while retry_count < max_retries:
        try: 
            logger.info("saving response")

            """Create a new ResponseLog object with the response details and 
                add it to the database"""
            response_log =  models.ResponseLog(
                request_id=response.get("request_id"),
                response_id=response.get("response_id"),
                response_status_code=response.get("response_status_code"),
                response_headers=response.get("response_headers"),
                response_body=response.get("response_body")
            )

            db.add(response_log)
            db.commit()
            logger.info("done saving response")

            """if successful, break out of the loop"""
            break

        except SQLAlchemyError as sqla_error:
            if db is not None:
                """Rollback the transaction in case of an SQLAlchemy error"""
                db.rollback() 
                db.close()

            logger.error(
                "SQLAlchemy error occurred while saving response to db: "
                f"{str(sqla_error)}. "
                f"Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
            retry_count += 1
        
        except Exception as e:
            logger.error(
                f"An error occurred while saving response to db: {e}", 
                exc_info=sys.exc_info()
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
        finally:
            db.close()

    else:
        logger.error(
            "Max retries reached. Unable to establish database connection "
            "while saving response to db"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )