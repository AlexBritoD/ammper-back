from sqlalchemy import Column, Integer, String, DateTime, func, JSON
from sqlalchemy.sql import text
from app.database import Base
from sqlalchemy.dialects.postgresql import JSONB

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Link(Base):
    __tablename__ = "links"

    id = Column(String, primary_key=True, index=True)
    institution = Column(String, nullable=False)
    access_mode = Column(String)
    last_accessed_at = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    external_id = Column(String)
    institution_user_id = Column(String)
    status = Column(String, nullable=False)
    created_by = Column(String)
    refresh_rate = Column(String)
    credentials_storage = Column(String)
    fetch_resources = Column(JSON)
    stale_in = Column(String)
    credentials = Column(JSON)


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String, primary_key=True, index=True)   
    code = Column(String, nullable=True)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    type = Column(String, nullable=True)
    country_code = Column(String, nullable=True)
    country_codes = Column(JSONB, nullable=True)
    website = Column(String, nullable=True)
    primary_color = Column(String, nullable=True)
    logo = Column(String, nullable=True)
    icon_logo = Column(String, nullable=True)
    text_logo = Column(String, nullable=True)
    form_fields = Column(JSONB, nullable=True) 
    features = Column(JSONB, nullable=True)    
    integration_type = Column(String, nullable=True)
    status = Column(String, nullable=True)
    resources = Column(JSONB, nullable=True)   
    openbanking_information = Column(JSONB, nullable=True)  