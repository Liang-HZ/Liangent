import enum

class AgentState(str, enum.Enum):
    THINKING = "THINKING"
    ACTING = "ACTING"
    EXECUTING = "EXECUTING"
    SAVING = "SAVING"
    LOOPING = "LOOPING"
    FINISHING = "FINISHING"
    # Additional states for error handling or initial state
    CREATED = "CREATED"
    ERROR = "ERROR"
    COMPLETED = "COMPLETED"

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
