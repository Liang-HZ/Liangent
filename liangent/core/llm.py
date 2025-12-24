import os
from openai import OpenAI
from liangent.config import get_settings

settings = get_settings()

class LLMClient:
    def __init__(self, api_key: str = None, base_url: str = None, model_name: str = None):
        # Resolve settings only if needed
        if not api_key or not base_url or not model_name:
            settings = get_settings()
            
        final_api_key = api_key or settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        final_base_url = base_url or settings.OPENAI_BASE_URL or settings.OPENAI_API_BASE
        self.model = model_name or settings.OPENAI_MODEL_NAME or settings.MODEL_NAME

        if not final_api_key:
            raise ValueError("API Key must be provided via argument, config, or environment variable (OPENAI_API_KEY).")

        self.client = OpenAI(
            api_key=final_api_key,
            base_url=final_base_url
        )

    def chat(self, messages: list[dict], temperature: float = 0.0, stop: list[str] = None):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stop=stop,
                stream=False 
            )
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "content": f"Error calling LLM: {str(e)}",
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            }
    
    def chat_with_tools(self, messages: list[dict], tools: list[dict], temperature: float = 0.0):
        """
        Call LLM with native function calling support.
        Returns tool_calls if model requests tool execution.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                temperature=temperature,
                stream=False
            )
            
            choice = response.choices[0]
            result = {
                "content": choice.message.content,
                "tool_calls": None,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            # Check for tool calls
            if choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments  # JSON string
                    }
                    for tc in choice.message.tool_calls
                ]
            
            return result
        except Exception as e:
            print(f"LLM Error (with tools): {e}")
            return {
                "content": f"Error calling LLM: {str(e)}",
                "tool_calls": None,
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            }
    
    def chat_stream(self, messages: list[dict], temperature: float = 0.0, stop: list[str] = None):
        pass
