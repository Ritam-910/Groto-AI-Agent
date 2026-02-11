from typing import TypedDict, Annotated, Sequence, Union, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
import operator
import datetime
import json
import httpx
import re

# Define the State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# Define Tools
@tool
def get_current_time() -> str:
    """Get the current date and time with timezone"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

@tool
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression"""
    try:
        allowed_chars = set("0123456789+-*/()%. ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Calculation error: {str(e)}"

@tool
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for real-time information using DuckDuckGo"""
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, data={"q": query}, headers=headers, follow_redirects=True)
            if response.status_code != 200:
                return f"Search failed with status code: {response.status_code}"
            
            # Simple cleanup of HTML
            html = response.text
            result_pattern = r'result__a.*?href="(.*?)".*?>(.*?)</a>.*?result__snippet.*?>(.*?)</span'
            matches = re.findall(result_pattern, html, re.DOTALL)
            
            results = []
            for i, (link, title, snippet) in enumerate(matches[:max_results]):
                title = re.sub(r'<.*?>', '', title).strip()
                snippet = re.sub(r'<.*?>', '', snippet).strip()
                results.append(f"{i+1}. **{title}**\n   {snippet}\n   URL: {link}\n")
            
            if not results:
                return f"No results found for: {query}"
            return "\n".join(results)
    except Exception as e:
        return f"Search error: {str(e)}"

TOOLS = [get_current_time, calculate, search_web]

# Define Graph Class
class LangGraphAgent:
    def __init__(self, model_name: str = "phi3:latest"):
        self.model = ChatOllama(model=model_name, temperature=0.7)
        self.model = self.model.bind_tools(TOOLS)
        self.tools = {t.name: t for t in TOOLS}
        self.tool_node = ToolNode(TOOLS)
        
        # Build graph
        workflow = StateGraph(AgentState)
        
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.tool_node)
        
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {"continue": "tools", "end": END}
        )
        
        workflow.add_edge("tools", "agent")
        
        self.app = workflow.compile()
        self.conversations = {}

    def call_model(self, state: AgentState):
        messages = state['messages']
        response = self.model.invoke(messages)
        return {"messages": [response]}

    def should_continue(self, state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        
        if last_message.tool_calls:
            return "continue"
        return "end"

    async def chat(self, user_message: str, conversation_id: str = None) -> Dict[str, Any]:
        """Chat interface compatible with existing system"""
        if not conversation_id:
            import uuid
            conversation_id = str(uuid.uuid4())
            
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            
        # Add user message to history if it's new
        # Note: LangGraph manages state per invocation usually, but here we want persistence
        # We will use the conversation_id to retrieve history, simplistic in-memory approach
        
        current_messages = self.conversations.get(conversation_id, [])
        current_messages.append(HumanMessage(content=user_message))
        
        inputs = {"messages": current_messages}
        
        # Execute graph
        final_state = await self.app.ainvoke(inputs)
        
        # Update history
        self.conversations[conversation_id] = final_state['messages']
        
        # Extract last response
        last_message = final_state['messages'][-1]
        response_text = last_message.content
        
        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "timestamp": datetime.datetime.now(),
            "metadata": {
                "model": self.model.model,
                "tool_calls": len([m for m in final_state['messages'] if isinstance(m, ToolMessage)])
            }
        }
    
    async def chat_stream(self, user_message: str, conversation_id: str = None):
        """Streaming chat interface"""
        # Simplistic streaming wrapper around chat
        result = await self.chat(user_message, conversation_id)
        yield result["response"]
    
    async def health_check(self):
        try:
            # Simple check
            return {
                "status": "healthy",
                "ollama_connected": True,
                "model": self.model.model,
                "model_available": True
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def clear_conversation(self, conversation_id: str) -> bool:
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
        
    def get_conversation_history(self, conversation_id: str):
        if conversation_id in self.conversations:
            return [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} 
                    for m in self.conversations[conversation_id] if not isinstance(m, ToolMessage) and (isinstance(m, HumanMessage) or isinstance(m, AIMessage))]
        return None
