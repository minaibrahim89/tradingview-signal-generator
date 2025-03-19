from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime
import os
from sqlalchemy.sql import text
from sqlalchemy import inspect

# Create SQLite engine
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./email_forwarder.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database models
class WebhookConfig(Base):
    __tablename__ = "webhook_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    active = Column(Boolean, default=True)
    content_type = Column(String(100), default="application/json")
    send_raw_body = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


class EmailMonitorConfig(Base):
    __tablename__ = "email_monitor_configs"

    id = Column(Integer, primary_key=True, index=True)
    email_address = Column(String(320), nullable=False)
    filter_subject = Column(String(500), nullable=True)
    filter_sender = Column(String(320), nullable=True)
    check_interval_seconds = Column(Integer, default=60)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


class ProcessedEmail(Base):
    __tablename__ = "processed_emails"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True, index=True)
    sender = Column(String(320))
    subject = Column(String(500))
    received_at = Column(DateTime)
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
    forwarded_successfully = Column(Boolean, default=False)
    body_snippet = Column(Text, nullable=True)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_db():
    Base.metadata.create_all(bind=engine)
    
    # Update schema if new columns are missing
    try:
        # Check if the webhook_configs table has the content_type column
        conn = engine.connect()
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('webhook_configs')]
        
        # Add missing columns if they don't exist
        if 'content_type' not in columns:
            conn.execute(text("ALTER TABLE webhook_configs ADD COLUMN content_type VARCHAR(100) DEFAULT 'application/json'"))
            print("Added content_type column to webhook_configs table")
            
        if 'send_raw_body' not in columns:
            conn.execute(text("ALTER TABLE webhook_configs ADD COLUMN send_raw_body BOOLEAN DEFAULT 0"))
            print("Added send_raw_body column to webhook_configs table")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating schema: {e}")
        # Continue even if the schema update fails
