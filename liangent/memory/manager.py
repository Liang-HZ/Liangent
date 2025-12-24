from sqlalchemy.orm import Session as DbSession
from sqlalchemy.exc import NoResultFound
from sqlalchemy import select, update
import uuid
import json
from liangent.memory.models import Session, Message, DebugLog, LLMProvider
from liangent.types import AgentState

class SessionManager:
    def __init__(self, db: DbSession):
        self.db = db

    def get_default_provider(self) -> LLMProvider:
        # For now, return the first one or one named "Default"
        stmt = select(LLMProvider).order_by(LLMProvider.id)
        return self.db.scalars(stmt).first()

    def seed_default_provider(self, settings):
        """Creates a default provider from env settings if DB is empty"""
        if not self.get_default_provider():
            print("Seeding default LLM provider from settings...")
            provider = LLMProvider(
                name="Default Provider",
                model_name=settings.MODEL_NAME,
                base_url=settings.OPENAI_API_BASE,
                api_key_var="OPENAI_API_KEY", # Assuming standard env var
                input_price_1k=settings.INPUT_PRICE_PER_1K,
                output_price_1k=settings.OUTPUT_PRICE_PER_1K,
                currency=settings.CURRENCY_UNIT,
                supports_function_calling=1 if settings.SUPPORTS_FUNCTION_CALLING else 0
            )
            self.db.add(provider)
            self.db.commit()

    def create_session(self, user_id: str, model_provider_id: int = None) -> Session:
        # If no model_provider_id, try to use default
        if model_provider_id is None:
            default_p = self.get_default_provider()
            model_provider_id = default_p.id if default_p else None
            
        new_session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            status=AgentState.CREATED.value,
            active_model_provider_id=model_provider_id,
            version=1
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        return new_session

    def get_session(self, session_id: str) -> Session:
        try:
            # Eager load messages
            stmt = select(Session).where(Session.id == session_id)
            session = self.db.scalars(stmt).one()
            return session
        except NoResultFound:
            return None

    def get_or_create_session(self, session_id: str | None, user_id: str) -> Session:
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
            print(f"Session {session_id} not found, creating new one.")
        
        return self.create_session(user_id)

    def append_message(self, session_id: str, role: str, content: str | dict, tool_call_id: str = None, tool_name: str = None):
        if isinstance(content, dict) or isinstance(content, list):
            content = json.dumps(content, ensure_ascii=False)
            
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            tool_call_id=tool_call_id,
            tool_name=tool_name
        )
        self.db.add(msg)
        # Note: In atomic step this might be deferred, but for now simple commit
        self.db.commit()
        return msg

    def update_session_state(self, session_id: str, new_status: str, old_version: int) -> bool:
        """
        Optimistic locking update. Returns True if successful, False if version mismatch.
        """
        stmt = (
            update(Session)
            .where(Session.id == session_id, Session.version == old_version)
            .values(status=new_status, version=Session.version + 1)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def save_step(self, session_id: str, new_messages: list[dict], new_status: str, old_version: int):
        """
        Atomic save of multiple messages + state update.
        """
        try:
            # 1. Add messages
            for m in new_messages:
                content = m.get("content", "")
                if isinstance(content, (dict, list)):
                    content = json.dumps(content, ensure_ascii=False)
                
                msg = Message(
                    session_id=session_id,
                    role=m.get("role"),
                    content=str(content),
                    tool_call_id=m.get("tool_call_id"),
                    tool_name=m.get("tool_name")
                )
                self.db.add(msg)
            
            # 2. Update session state with optimistic lock
            stmt = (
                update(Session)
                .where(Session.id == session_id, Session.version == old_version)
                .values(status=new_status, version=Session.version + 1)
            )
            result = self.db.execute(stmt)
            
            if result.rowcount == 0:
                self.db.rollback()
                raise Exception("Optimistic Lock Failed: Session modified by concurrent request.")
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def save_debug_log(self, session_id: str, step: int, data: dict, duration: float, 
                       input_cost: float, output_cost: float, total_cost: float,
                       model_provider_id: int = None, input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0, currency: str = "CNY"):
        
        # Manually serialize to ensure Chinese characters are readable (ensure_ascii=False)
        data_str = json.dumps(data, ensure_ascii=False)
        
        log = DebugLog(
            session_id=session_id,
            step=step,
            data=data_str,
            duration=duration,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model_provider_id=model_provider_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            currency=currency
        )
        self.db.add(log)
        self.db.commit()
