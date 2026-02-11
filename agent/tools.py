"""
Tools that the AI agent can use to enhance its capabilities
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Callable
import httpx


class ToolRegistry:
    """Registry for managing agent tools"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.descriptions: Dict[str, str] = {}
        self._register_default_tools()
    
    def register(self, name: str, description: str):
        """Decorator to register a tool"""
        def decorator(func: Callable):
            self.tools[name] = func
            self.descriptions[name] = description
            return func
        return decorator
    
    def get_tool(self, name: str) -> Callable:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def get_descriptions(self) -> Dict[str, str]:
        """Get all tool descriptions"""
        return self.descriptions.copy()
    
    def execute(self, name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool with given parameters"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        try:
            return tool(**parameters)
        except Exception as e:
            return f"Error executing tool: {str(e)}"
    
    def _register_default_tools(self):
        """Register default tools"""
        
        @self.register("get_current_time", "Get the current date and time with timezone")
        def get_current_time() -> str:
            """Returns the current date and time with timezone and day of week"""
            from datetime import datetime
            import time
            
            now = datetime.now()
            
            try:
                is_dst = time.daylight and time.localtime().tm_isdst > 0
                utc_offset = - (time.altzone if is_dst else time.timezone)
                hours, remainder = divmod(abs(utc_offset), 3600)
                minutes = remainder // 60
                tz_sign = '+' if utc_offset >= 0 else '-'
                tz_str = f"UTC{tz_sign}{hours:02d}:{minutes:02d}"
            except Exception:
                tz_str = "Local Time"
            
            # Get day of week
            day_name = now.strftime("%A")
            
            time_str = now.strftime('%Y-%m-%d %H:%M:%S')
            
            return f"{day_name}, {time_str} ({tz_str})"
        
        @self.register("calculate", "Perform mathematical calculations")
        def calculate(expression: str) -> str:
            """
            Safely evaluate a mathematical expression
            
            Args:
                expression: Mathematical expression to evaluate
            
            Returns:
                Result of the calculation
            """
            try:
                allowed_chars = set("0123456789+-*/()%. ")
                if not all(c in allowed_chars for c in expression):
                    return "Error: Invalid characters in expression"
                
                result = eval(expression, {"__builtins__": {}}, {})
                return str(result)
            except Exception as e:
                return f"Calculation error: {str(e)}"
        
        @self.register("search_web", "Search the web for real-time information using DuckDuckGo")
        def search_web(query: str, max_results: int = 5) -> str:
            """
            Search the web using DuckDuckGo
            
            Args:
                query: Search query
                max_results: Maximum number of results to return (default: 5)
            
            Returns:
                Formatted search results with titles, snippets, and URLs
            """
            try:
                url = "https://html.duckduckgo.com/html/"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(
                        url,
                        data={"q": query},
                        headers=headers,
                        follow_redirects=True
                    )
                    
                    if response.status_code != 200:
                        return f"Search failed with status code: {response.status_code}"
                    
                    html = response.text
                    results = []
                    
                    result_pattern = r'result__a.*?href="(.*?)".*?>(.*?)</a>.*?result__snippet.*?>(.*?)</span'
                    matches = re.findall(result_pattern, html, re.DOTALL)
                    
                    for i, (link, title, snippet) in enumerate(matches[:max_results]):
                        title = re.sub(r'<.*?>', '', title).strip()
                        snippet = re.sub(r'<.*?>', '', snippet).strip()
                        title = title.replace('&amp;', '&').replace('&quot;', '"')
                        snippet = snippet.replace('&amp;', '&').replace('&quot;', '"')
                        
                        results.append(f"{i+1}. **{title}**\n   {snippet}\n   URL: {link}\n")
                    
                    if not results:
                        return f"No results found for: {query}"
                    
                    return f" **Web Search Results for: {query}**\n\n" + "\n".join(results)
                    
            except httpx.TimeoutException:
                return "Search timed out. Please try again."
            except Exception as e:
                return f"Search error: {str(e)}\nNote: Using DuckDuckGo search - no API key required!"
        
        @self.register("get_weather", "Get weather information (simulated)")
        def get_weather(location: str) -> str:
            """
            Simulate weather lookup (placeholder for actual implementation)
            
            Args:
                location: Location to get weather for
            
            Returns:
                Weather information
            """
            return f"[Simulated weather for {location}]\nTemperature: 22°C, Condition: Partly Cloudy\nNote: Integrate with a weather API for real data."
        
        @self.register("create_summary", "Create a summary of text")
        def create_summary(text: str, max_length: int = 100) -> str:
            """
            Create a simple summary of text
            
            Args:
                text: Text to summarize
                max_length: Maximum length of summary
            
            Returns:
                Summarized text
            """
            if len(text) <= max_length:
                return text
            
            return text[:max_length].rsplit(' ', 1)[0] + "..."

tool_registry = ToolRegistry()


def parse_tool_call(response: str) -> tuple[str | None, Dict[str, Any] | None]:
    """
    Parse a tool call from the agent's response
    
    Args:
        response: Agent's response text
    
    Returns:
        Tuple of (tool_name, parameters) or (None, None) if no tool call found
    """
    lines = response.strip().split('\n')
    tool_name = None
    parameters = None
    
    for i, line in enumerate(lines):
        if line.startswith("TOOL_CALL:"):
            tool_name = line.replace("TOOL_CALL:", "").strip()
        elif line.startswith("PARAMETERS:"):
            param_str = line.replace("PARAMETERS:", "").strip()
            try:
                parameters = json.loads(param_str)
            except json.JSONDecodeError:
                parameters = {}
    
    if tool_name:
        return tool_name, parameters or {}
    
    return None, None
