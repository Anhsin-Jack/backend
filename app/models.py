
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Float, LargeBinary, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy.sql import func

# Users Table
class User(Base):
    __tablename__ = 'Users'
    user_id = Column(Integer, primary_key=True,autoincrement=True)
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    role = Column(Enum('admin', 'user'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

# User Profile Table
class UserProfile(Base):
    __tablename__ = 'UserProfile'

    profile_id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    first_name = Column(String(50))
    last_name = Column(String(50))
    date_of_birth = Column(Date)
    profile_picture = Column(LargeBinary)  # Binary data for profile picture
    bio = Column(Text)
    user = relationship(User)

# Sessions Table
class UserSession(Base):
    __tablename__ = 'UserSessions'

    session_id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    login_time = Column(DateTime, nullable=False)
    logout_time = Column(DateTime)
    user = relationship(User)

# Audit Trail Table
class AuditTrail(Base):
    __tablename__ = 'AuditTrail'

    audit_id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    timestamp = Column(DateTime, nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    user = relationship(User)

# User Settings Table
class UserSettings(Base):
    __tablename__ = 'UserSettings'

    setting_id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    setting_name = Column(String(50), nullable=False)
    setting_value = Column(Text)
    user = relationship(User)