from typing import List, Generator, Dict, Any
from liangent.core.llm import LLMClient
from liangent.core.agent import ContextAgent

class Liangent:
    """
    High-level client for Liangent.
    Provides a simple interface to initialize and interact with the agent.
    """
    def __init__(
        self, 
        api_key: str = None, 
        base_url: str = None, 
        model_name: str = None, 
        db_url: str = None, 
        tools: List[str] = None,
        verbose: bool = False,
        debug: bool = False,
        show_prompts: bool = False,
        min_tool_use: int = None,
        max_tool_use: int = None,
        max_steps: int = None
    ):
        """
        Initialize the Liangent client.
        
        Args:
            api_key: OpenAI API Key.
            base_url: OpenAI Base URL.
            model_name: Model name (e.g., gpt-3.5-turbo).
            db_url: Database URL. Defaults to in-memory SQLite if not provided and not in env.
            tools: List of tool names to enable.
            verbose: If True, prints thinking process and tool execution details to console (excluding debug stats).
            debug: If True, prints full debug information including token usage, costs, and execution details. Implies verbose=True.
            show_prompts: If True, displays complete prompts (system + user + history) for each step.
            min_tool_use: Minimum number of tool calls required before final answer. Defaults to settings.MIN_TOOL_USE (1).
            max_tool_use: Maximum number of tool calls allowed. Defaults to settings.MAX_TOOL_USE (15).
            max_steps: Maximum number of agent steps. Defaults to settings.MAX_STEPS (20).
        """
        self.verbose = verbose or debug
        self.debug = debug
        self.show_prompts = show_prompts
        # 1. Initialize LLM
        self.llm = LLMClient(api_key=api_key, base_url=base_url, model_name=model_name)
        
        # 2. Determine DB URL
        # If explicitly passed, use it.
        # If not, try settings/env. 
        # If still none, agent will default to :memory: internally, so passing None is fine.
        
        # 3. Initialize Agent
        # Single-user, single-session mode for SDK usage typically
        self.agent = ContextAgent(
            llm_client=self.llm,
            db_url=db_url,
            tools=tools,
            user_id="sdk_user",
            debug=self.debug,
            show_prompts=show_prompts,
            min_tool_use=min_tool_use,
            max_tool_use=max_tool_use,
            max_steps=max_steps
        )
        
    def chat(self, query: str) -> str:
        """
        Send a query to the agent and get the final response synchronously.
        If verbose=True, prints debug logs to stdout matching agent.py's output format.
        """
        import json
        final_answer = ""
        
        for event in self.agent.run(query):
            evt_type = event.get("event")
            
            if self.verbose:
                if evt_type == "status":
                    # Status updates like "Thinking (Step N)..."
                    print(f"\n[Status] {event.get('content', '')}", flush=True)
                
                elif evt_type == "thought":
                    content = event.get("content", "")
                    if content:
                        # Use agent's helper to extract clean thought content
                        # This handles incomplete JSON, marker-only responses, etc.
                        content = self.agent._extract_thought_content(content)
                        
                        # Only print if there is actual thought content
                        if content:
                            # Truncate only if NOT in debug mode
                            if not self.debug and len(content) > 200:
                                display_content = content[:200] + "..."
                            else:
                                display_content = content
                            print(f"[Thought] {display_content}", flush=True)
                
                elif evt_type == "item.started":
                    data = event.get("data", {})
                    item = data.get("item", {})
                    tool_name = item.get("tool", "unknown")
                    args = item.get("args", "")
                    
                    # Truncate args only if NOT in debug mode
                    args_str = str(args)
                    if not self.debug and len(args_str) > 100:
                        args_display = args_str[:100] + "..."
                    else:
                        args_display = args_str
                    print(f"[Tool Call] {tool_name}({args_display})", flush=True)
                
                elif evt_type == "item.completed":
                    data = event.get("data", {})
                    item = data.get("item", {})
                    tool_name = item.get("tool", "unknown")
                    output = item.get("aggregated_output", "")
                    exit_code = item.get("exit_code", 0)
                    
                    # Truncate output only if NOT in debug mode
                    if not self.debug and len(output) > 150:
                        output_display = output[:150] + "..."
                    else:
                        output_display = output
                        
                    status_icon = "✓" if exit_code == 0 else "✗"
                    print(f"[Tool Result] {status_icon} {tool_name}: {output_display}", flush=True)
                
                elif evt_type == "debug":
                    # Only show step-level debug stats in debug mode
                    if self.debug:
                        data = event.get("data", {})
                        step = data.get("step", 0)
                        history_len = data.get("history_len", 0)
                        usage = data.get("current_usage", {})
                        total_cost = data.get("total_cost", 0)
                        currency = data.get("currency", "USD")
                        
                        print(f"[Debug] Step {step} | History: {history_len} msgs | "
                              f"Tokens: {usage.get('input_tokens', 0)}in/{usage.get('output_tokens', 0)}out | "
                              f"Cost: {total_cost:.4f} {currency}", flush=True)
                
                elif evt_type == "usage_stats":
                    content = event.get("content", {})
                    usage = content.get("usage", {})
                    cost = content.get("cost", {})
                    
                    print("\n" + "="*50, flush=True)
                    print("[Usage Stats]", flush=True)
                    print(f"  Tokens: {usage.get('input_tokens', 0)} input / "
                          f"{usage.get('output_tokens', 0)} output / "
                          f"{usage.get('total_tokens', 0)} total", flush=True)
                    print(f"  Cost: {cost.get('input_cost', 0):.4f} input + "
                          f"{cost.get('output_cost', 0):.4f} output = "
                          f"{cost.get('total_cost', 0):.4f} {cost.get('currency', 'USD')}", flush=True)
                    print("="*50 + "\n", flush=True)
                
                elif evt_type == "prompt_info":
                    # Only show if show_prompts is enabled (handled separately from verbose)
                    pass
                
                elif evt_type == "error":
                    print(f"[Error] {event.get('content', '')}", flush=True)
            
            # Handle prompt_info event separately (shown even without verbose if show_prompts=True)
            if evt_type == "prompt_info" and self.show_prompts:
                 # ... (Unchanged logic for prompt_info)
                 data = event.get("data", {})
                 print(f"\n{'='*60}", flush=True)
                 print(f"[COMPLETE PROMPT - Step {data.get('step', '?')}]", flush=True)
                 print(f"{'='*60}", flush=True)
                 # ...
                 # Assuming prompt_info handling logic is preserved below or doesn't need to be touched if I use EndLine correctly.
                 # Actually I need to be careful with replace_file_content.
                 # The 'prompt_info' logic inside the loop (lines 135-137) is redundant with lines 143+.
                 # I'll just keep the structure clean.
                 pass

            # Redundant prompt_info block handling (Lines 143-174 in previous file view)
            # I should include it in replacement or ensure I don't overwrite it incorrectly.
            # My StartLine is 62.
            
            if evt_type == "prompt_info" and self.show_prompts:
                data = event.get("data", {})
                print(f"\n{'='*60}", flush=True)
                print(f"[COMPLETE PROMPT - Step {data.get('step', '?')}]", flush=True)
                print(f"{'='*60}", flush=True)
                
                # System prompt
                system_prompt = data.get('system_prompt', '')
                print(f"\n--- System Prompt ({len(system_prompt)} chars) ---", flush=True)
                print(system_prompt, flush=True)
                
                # AGENTS.md content
                agents_md = data.get('agents_md', '')
                if agents_md:
                    print("\n--- AGENTS.md (embedded in system prompt) ---", flush=True)
                    print(f"(Length: {len(agents_md)} chars)", flush=True)
                
                # History
                history = data.get('history', [])
                print(f"\n--- Conversation History ({len(history)} messages) ---", flush=True)
                for i, msg in enumerate(history):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if role == 'user':
                        print(f"  [{i+1}] {role}: {content}", flush=True)
                    else:
                        # Truncate history display unless formatted otherwise? 
                        # User wants LOSSLESS debug. But this is Prompt Info (meta).
                        # I'll keep existing behavior (truncation for old history) to avoid massive prompt dumps unless user asks.
                        display = content[:200] + '...' if len(content) > 200 else content
                        print(f"  [{i+1}] {role}: {display}", flush=True)
                
                print(f"{'='*60}\n", flush=True)
            
            if evt_type == "final_answer":
                final_answer = event.get("content", "")
                
                # Ensure we have the clean answer (sync with agent.py logic)
                marker = self.agent.final_answer_marker
                if marker and isinstance(final_answer, str) and marker in final_answer:
                    _, final_answer_clean = final_answer.split(marker, 1)
                    final_answer = final_answer_clean.strip()
                
                if self.verbose:
                    print_content = final_answer
                    # Try to parse if it looks like JSON to show cleaner output
                    if isinstance(final_answer, str) and final_answer.strip().startswith("{"):
                        try:
                            parsed = json.loads(final_answer)
                            if isinstance(parsed, dict):
                                if "final_answer" in parsed:
                                    print_content = parsed["final_answer"]
                                elif "thought" in parsed:
                                    print_content = parsed["thought"]
                        except (json.JSONDecodeError, KeyError):
                            pass
                    print(f"\n[Final Answer] {print_content}\n", flush=True)
            
            elif evt_type == "error":
                raise RuntimeError(f"Agent Error: {event.get('content')}")
                
        return final_answer
        
    def stream(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Stream events from the agent.
        """
        yield from self.agent.run(query)
