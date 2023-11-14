import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(app_dir)
from .. import models


class KafkaTopic:
    WRITE_DB = "write_db"
    READ_DB = "read_db"
    UPDATE_DB = "update_db"
    DELETE_DB = "delete_db"
    SAVE_RESPONSE_TO_DB = "save_response_to_db"
    SAVE_REQUEST_TO_DB = "save_request_to_db"

class KafkaAction:
    WRITE_DB = "write_db"
    READ_DB = "read_db"
    UPDATE_DB = "update_db"
    DELETE_DB = "delete_db"
    SAVE_RESPONSE_TO_DB = "save_response_to_db"
    SAVE_REQUEST_TO_DB = "save_request_to_db"

class Task:
    WRITE_DB = None
    READ_DB = None
    UPDATE_DB = None
    DELETE_DB = None
    SAVE_RESPONSE_TO_DB = None
    SAVE_REQUEST_TO_DB = None

class DatabaseSchemas:
    USER = models.User.__tablename__
    USER_PROFILE = models.UserProfile.__tablename__
    CSUITE_DASHBOARD_CATEGORIES = models.CSuiteDashboardCategories.__tablename__
    CSUITE_DASHBOARD = models.CSuiteDashboard.__tablename__
    TEXT2SQL = models.Text2SQL.__tablename__
    TECHNICAL_CHATBOT_RESPONSE = models.TechnicalChatbotResponse.__tablename__
    CSUITE_CHATBOT_RESPONSE = models.CSuiteChatbotResponse.__tablename__
    CLIENT_DATABASE_INFO = models.ClientDatabaseInfo.__tablename__
    REQUEST_LOG = models.RequestLog.__tablename__
    RESPONSE_LOG = models.ResponseLog.__tablename__
