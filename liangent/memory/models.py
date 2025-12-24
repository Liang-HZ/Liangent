from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from liangent.memory.db import Base
from liangent.types import AgentState

def now_beijing():
    return datetime.utcnow() + timedelta(hours=8)

class Session(Base):
    __tablename__ = "t_sessions"

    id = Column(String(36), primary_key=True, index=True) # UUID
    user_id = Column(String(50), index=True)
    version = Column(Integer, default=1) # Optimistic Lock
    status = Column(String(20), default=AgentState.CREATED.value) # Stored as string for flexibility
    active_model_provider_id = Column(Integer, nullable=True) # Virtual FK to t_llm_providers.id
    created_at = Column(DateTime, default=now_beijing)
    updated_at = Column(DateTime, default=now_beijing, onupdate=now_beijing)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    debug_logs = relationship("DebugLog", back_populates="session", cascade="all, delete-orphan")
    provider = relationship("LLMProvider", foreign_keys=[active_model_provider_id], primaryjoin="Session.active_model_provider_id==LLMProvider.id", back_populates="sessions")

class Message(Base):
    __tablename__ = "t_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("t_sessions.id"))
    role = Column(String(20)) # user, assistant, tool, system
    content = Column(Text) # JSON or Text
    tool_call_id = Column(String(50), nullable=True) # OpenTelemetry/OpenAI compat
    tool_name = Column(String(50), nullable=True) # For tool outputs
    created_at = Column(DateTime, default=now_beijing)

    session = relationship("Session", back_populates="messages")

class DebugLog(Base):
    __tablename__ = "t_debug_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("t_sessions.id"))
    model_provider_id = Column(Integer, nullable=True) # Virtual FK to t_llm_providers.id
    step = Column(Integer)
    data = Column(Text) # JSON content stored as TEXT for readability (ensure_ascii=False)
    duration = Column(Float, default=0.0)
    
    # Token Stats
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Cost Stats
    input_cost = Column(Float, default=0.0)
    output_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    currency = Column(String(10), default="CNY")
    
    created_at = Column(DateTime, default=now_beijing)

    session = relationship("Session", back_populates="debug_logs")
    provider = relationship("LLMProvider", foreign_keys=[model_provider_id], primaryjoin="DebugLog.model_provider_id==LLMProvider.id")

class LLMProvider(Base):
    __tablename__ = "t_llm_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True) # Friendly Name e.g. "GPT-4 Production"
    model_name = Column(String(100)) # API Model string e.g. "gpt-4"
    base_url = Column(String(255))
    api_key_var = Column(String(100)) # Name of Env Var
    input_price_1k = Column(Float, default=0.0)
    output_price_1k = Column(Float, default=0.0)
    currency = Column(String(10), default="CNY")
    supports_function_calling = Column(Integer, default=0)  # 0=False, 1=True (SQLite compat)
    
    sessions = relationship("Session", primaryjoin="Session.active_model_provider_id==LLMProvider.id", foreign_keys="[Session.active_model_provider_id]", back_populates="provider")
