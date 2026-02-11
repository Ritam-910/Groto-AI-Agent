"""
Core AI Agent implementation using Ollama and Phi3:latest
"""

import ollama
from typing import List, Dict, Any, Optional, AsyncGenerator
import uuid
from datetime import datetime

from agent.prompts import SYSTEM_PROMPT, get_tool_prompt
from agent.tools import tool_registry, parse_tool_call
from models.schemas import Message, AgentState, ToolCall


class AIAgent:
    """
    AI Agent powered by Phi3:latest through Ollama
    """

    def __init__(
        self,
        model: str = "phi3:latest",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tool_registry = tool_registry
        self.conversations: Dict[str, AgentState] = {}

    def _get_or_create_conversation(
        self, conversation_id: Optional[str] = None
    ) -> AgentState:
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]

        new_id = conversation_id or str(uuid.uuid4())
        self.conversations[new_id] = AgentState(
            conversation_id=new_id,
            messages=[],
            tool_calls=[]
        )
        return self.conversations[new_id]

    def _add_message(self, state: AgentState, role: str, content: str):
        state.messages.append(Message(role=role, content=content))
        state.updated_at = datetime.now()

    def _add_tool_call(
        self,
        state: AgentState,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Any
    ):
        state.tool_calls.append(
            ToolCall(
                tool_name=tool_name,
                parameters=parameters,
                result=result
            )
        )

    async def chat(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        use_tools: bool = True
    ) -> Dict[str, Any]:
        state = self._get_or_create_conversation(conversation_id)
        self._add_message(state, "user", user_message)

        messages = self._prepare_messages(state, use_tools)

        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            )

            assistant_message = response["message"]["content"]

            if use_tools:
                tool_name, parameters = parse_tool_call(assistant_message)
                if tool_name:
                    tool_result = self.tool_registry.execute(tool_name, parameters)
                    self._add_tool_call(state, tool_name, parameters, tool_result)

                    messages.extend([
                        {"role": "assistant", "content": assistant_message},
                        {
                            "role": "user",
                            "content": (
                                f"Tool Result ({tool_name}): {tool_result}\n\n"
                                "Respond naturally using this information."
                            )
                        }
                    ])

                    response = ollama.chat(
                        model=self.model,
                        messages=messages,
                        options={
                            "temperature": self.temperature,
                            "num_predict": self.max_tokens
                        }
                    )
                    assistant_message = response["message"]["content"]

            self._add_message(state, "assistant", assistant_message)

            return {
                "response": assistant_message,
                "conversation_id": state.conversation_id,
                "timestamp": datetime.now(),
                "metadata": {
                    "model": self.model,
                    "message_count": len(state.messages),
                    "tool_calls": len(state.tool_calls)
                }
            }

        except Exception as e:
            return {
                "response": f"Error generating response: {str(e)}",
                "conversation_id": state.conversation_id,
                "timestamp": datetime.now(),
                "metadata": {"error": True}
            }

    async def chat_stream(
        self,
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        state = self._get_or_create_conversation(conversation_id)
        self._add_message(state, "user", user_message)

        messages = self._prepare_messages(state)

        try:
            stream = ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            )

            full_response = ""
            for chunk in stream:
                content = chunk["message"]["content"]
                full_response += content
                yield content

            self._add_message(state, "assistant", full_response)

        except Exception as e:
            yield f"Error: {str(e)}"

    def _prepare_messages(
        self, state: AgentState, use_tools: bool = False
    ) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if use_tools:
            messages[0]["content"] += "\n\n" + get_tool_prompt(
                self.tool_registry.get_descriptions()
            )

        for msg in state.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    async def health_check(self) -> Dict[str, Any]:
        """
        Reliable health check:
        - verifies Ollama connection
        - verifies model availability
        """
        try:
            ollama.show(self.model)

            return {
                "status": "healthy",
                "ollama_connected": True,
                "model": self.model,
                "model_available": True
            }

        except Exception as e:
            return {
                "status": "model_not_found",
                "ollama_connected": True,
                "model": self.model,
                "model_available": False,
                "error": str(e)
            }
