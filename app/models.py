
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, LargeBinary, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
import sys
sys.path.append("/Users/michaelchee/Documents/backend/app")
from database import Base
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = 'Users'
    user_id = Column(Integer, primary_key=True,autoincrement=True)
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    role = Column(Enum('tech', 'csuite'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class UserProfile(Base):
    __tablename__ = 'UserProfile'

    profile_id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'),nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    date_of_birth = Column(Date)
    profile_picture = Column(LargeBinary)  # Binary data for profile picture
    bio = Column(Text)
    user = relationship(User)

class AuditTrail(Base):
    __tablename__ = 'AuditTrail'

    audit_id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'),nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text,nullable=False)
    created_at = Column(DateTime, nullable=False)
    user = relationship(User)

class CSuiteDashboardCategories(Base):
    __tablename__ = 'CSuiteDashboardCategories'

    id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'),nullable=False)
    categories = Column(Enum('Sales', 'Marketing',"Finance","Accounting","IT","HR"),nullable=False)
    data_type = Column(Enum("Index","Analysis"),nullable=False)
    data_type_name = Column(Text,nullable=False)

class CSuiteDashboard(Base):
    __tablename__ = 'CSuiteDashboard'

    id = Column(Integer, primary_key=True,autoincrement=True)
    category_id = Column(Integer, ForeignKey('CSuiteDashboardCategories.id'),nullable=False)
    index_number = Column(Float,nullable=True)
    index_percentage = Column(Float,nullable=True)
    sql_query = Column(Text,nullable=True)
    
class Text2SQL(Base):
    __tablename__ = "Text2SQL"

    id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'),nullable=False)
    input_text = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=False)
    edited_sql_query = Column(Text, nullable=True)

class TechnicalChatbotResponse(Base):
    __tablename__ = "TechnicalChatbotResponse"

    response_id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'),nullable=False)
    text2sql_id = Column(Integer, ForeignKey('Text2SQL.id'),nullable=False)
    analysis_code = Column(Text, nullable=False)
    prints = Column(Text,nullable=True)
    plots = Column(Text, nullable=True)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship(User)
    text2sql = relationship(Text2SQL)

class CSuiteChatbotResponse(Base):
    __tablename__ = "CSuiteChatbotResponse"
    id = Column(Integer, primary_key=True,autoincrement=True)
    category_ids = Column(Text, nullable=True)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class ClientDatabaseInfo(Base):
    __tablename__ = "ClientDatabaseInfo"
    id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'),nullable=False)
    database_keys = Column(String(255), nullable=False)
    user = relationship(User)


