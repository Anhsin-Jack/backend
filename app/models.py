from sqlalchemy import Column, Integer, String, Text, DateTime, Date, LargeBinary, ForeignKey, Enum, Float
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import DATETIME
from sqlalchemy.orm import relationship
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(app_dir)
from .database import Base
from sqlalchemy.sql import func

class User(Base):
    """User table stores user information."""
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True, comment="The unique identifier of user")
    username = Column(String(50), nullable=False, index=True, comment="Username of the user.")
    password = Column(String(255), nullable=False, comment="Password of the user.")
    email = Column(String(100), nullable=False, unique=True, index=True, comment="Email address of the user (must be unique).")
    role = Column(Enum('tech', 'csuite'), nullable=False, comment="Role of the user, either 'tech' or 'csuite'.")
    created_at = Column(DateTime, server_default=func.now(), comment="Timestamp of user creation.")

class UserProfile(Base):
    """UserProfile table stores additional user profile information."""
    __tablename__ = 'user_profile'

    profile_id = Column(Integer, primary_key=True, autoincrement=True, comment="The unique identifier of user profile")
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, index=True, comment="Foreign key linking to the User table.")
    first_name = Column(String(50), comment="First name of the user.")
    last_name = Column(String(50), comment="Last name of the user.")
    date_of_birth = Column(Date, comment="Date of birth of the user.")
    profile_picture = Column(LargeBinary, comment="Binary data for profile picture.")
    bio = Column(Text, comment="Biographical information about the user.")
    user = relationship(User)

class CSuiteDashboardCategories(Base):
    """CSuiteDashboardCategories table stores categories for CSuite dashboards."""
    __tablename__ = 'csuite_dashboard_categories'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="The unique identifier of the CSuiteDashboardCategories table.")
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, index=True, comment="Foreign key linking to the User table.")
    categories = Column(Text, nullable=False, comment="Category types for CSuite dashboards. For example, Sales, Marketing, Accounting or others.")
    data_type = Column(Enum("Index", "Analysis"), nullable=False, comment="Type of data for the category.")
    data_type_name = Column(Text, nullable=False, comment="Name of the data type. For example, ROI of the year")
    user = relationship(User)

class CSuiteDashboard(Base):
    """CSuiteDashboard table stores CSuite dashboard information."""
    __tablename__ = 'csuite_dashboard'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="The unique identifier of the CSuiteDashboard table.")
    category_id = Column(Integer, ForeignKey('csuite_dashboard_categories.id'), nullable=False, index=True, comment="Foreign key linking to the CSuiteDashboardCategories table.")
    index_number = Column(Float, nullable=True, comment="Number value for the dashboard index.")
    index_percentage = Column(Float, nullable=True, comment="Percentage value for the dashboard index.")
    sql_query = Column(Text, nullable=True, comment="SQL query associated with the dashboard.")
    graph_type = Column(String(255), nullable=True, comment="The graph type that need to show the data.")
    x_axis = Column(String(255), nullable=True,comment="The name of the x-axis of the graph")
    y_axis = Column(String(255), nullable=True,comment="The name of the y-axis of the graph")
    categories = relationship(CSuiteDashboardCategories)

class Text2SQL(Base):
    """Text2SQL table stores text-to-SQL conversion data."""
    __tablename__ = "text2sql"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="The unique identifier of the Text2SQL table.")
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment="Foreign key linking to the User table.")
    input_text = Column(Text, nullable=False, comment="Input text for text-to-SQL AI.")
    sql_query = Column(Text, nullable=False, comment="Generated SQL query.")
    edited_sql_query = Column(Text, nullable=True, comment="Edited SQL query by the user.")
    user = relationship(User)

class TechnicalChatbotResponse(Base):
    """TechnicalChatbotResponse table stores responses from a technical chatbot."""
    __tablename__ = "technical_chatbot_response"

    response_id = Column(Integer, primary_key=True, autoincrement=True, comment="The unique identifier for the TechnicalChatbotResponse table.")
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment="Foreign key linking to the User table.")
    text2sql_id = Column(Integer, ForeignKey('text2sql.id'), nullable=False, comment="Foreign key linking to the Text2SQL table.")
    analysis_code = Column(Text, nullable=False, comment="Code analysis result.")
    prints = Column(Text, nullable=True, comment="Print statements from the analysis.")
    plots = Column(Text, nullable=True, comment="Plots generated from the analysis.")
    response = Column(Text, nullable=False, comment="Response from the technical chatbot.")
    created_at = Column(DateTime, server_default=func.now(), comment="Timestamp of response creation.")

    user = relationship(User)
    text2sql = relationship(Text2SQL)

class CSuiteChatbotResponse(Base):
    """CSuiteChatbotResponse table stores responses from a CSuite chatbot."""
    __tablename__ = "csuite_chatbot_response"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="The unique identifier for the CSuiteChatbotResponse table.")
    category_ids = Column(Text, nullable=True, comment="Category IDs associated with the response.")
    response = Column(Text, nullable=False, comment="Response from the CSuite chatbot.")
    created_at = Column(DateTime, server_default=func.now(), comment="Timestamp of response creation.")

class ClientDatabaseInfo(Base):
    """ClientDatabaseInfo table stores information about client databases."""
    __tablename__ = "client_database_info"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="The unique identifier for the ClientDatabaseInfo table.")
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment="Foreign key linking to the User table.")
    database_keys = Column(String(255), nullable=False, comment="Keys associated with the client's database.")
    user = relationship(User)

class RequestLog(Base):
    """RequestLog table stores logs of incoming requests."""
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, nullable=False, comment="Primary key for the RequestLog table.")
    request_id = Column(String(255), nullable=False, index=True, comment="Unique identifier for the incoming request.")
    method = Column(String(255), comment="HTTP method of the request.")
    url_path = Column(String(255), comment="URL path of the request.")
    query_params = Column(LONGTEXT, comment="Query parameters of the request.")
    request_headers = Column(LONGTEXT, comment="Headers of the incoming request.")
    request_body = Column(LONGTEXT, comment="Body content of the incoming request.")
    client_ip = Column(String(45), comment="IP address of the client making the request.")
    user_agent = Column(String(255), comment="User agent information from the request.")
    referer = Column(String(255), comment="Referer information from the request.")
    cookies = Column(LONGTEXT, comment="Cookies sent with the request.")
    route_name = Column(String(255), comment="Name of the route in the application.")
    created_at = Column(DATETIME(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False, comment="Timestamp of log creation.")

class ResponseLog(Base):
    """ResponseLog table stores logs of outgoing responses."""
    __tablename__ = 'response_logs'

    id = Column(Integer, primary_key=True, nullable=False, comment="Primary key for the ResponseLog table.")
    request_id = Column(String(255), nullable=False, index=True, comment="Foreign key linking to the RequestLog table.")
    response_id = Column(String(255), nullable=False, index=True, comment="Unique identifier for the outgoing response.")
    response_status_code = Column(Integer, comment="HTTP status code of the response.")
    response_headers = Column(LONGTEXT, comment="Headers of the outgoing response.")
    response_body = Column(LONGTEXT, comment="Body content of the outgoing response.")
    created_at = Column(DATETIME(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False, comment="Timestamp of log creation.")
