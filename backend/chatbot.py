import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


class Chatbot:
    def __init__(self, db=None):
        self.current_model = "gemini"  # Default to Google Generative AI
        self.school_data = self._load_school_data()
        self.openai_model = None
        self.gemini_model = None
        self.db = db  # Database reference for tool access
        self._initialize_models()
        self._setup_tools()

    def _load_school_data(self) -> str:
        """Load school information from text file"""
        try:
            with open("school_data.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            print("Warning: school_data.txt not found")
            return ""

    def _initialize_models(self):
        """Initialize both LLM models"""
        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_model = ChatOpenAI(model="gpt-4o", api_key=openai_key, temperature=0)
        except Exception as e:
            print(f"Error initializing OpenAI model: {e}")

        try:
            google_key = os.getenv("GOOGLE_API_KEY")
            if google_key:
                self.gemini_model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-pro", google_api_key=google_key, temperature=0
                )
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")

    def _setup_tools(self):
        """Setup tools for the chatbot"""
        self.tools = [
            self._create_human_escalation_tool(),
            self._create_get_booking_slots_tool(),
            self._create_book_time_slot_tool(),
        ]

    def _create_human_escalation_tool(self):
        """Create the human escalation tool"""

        @tool
        def human_escalation(reason: str) -> str:
            """
            Escalate the conversation to a human operator when the AI cannot handle the query properly.

            Use this tool when:
            - The question requires information not available in the school data
            - The question is too complex or requires personalized advice
            - The student explicitly requests to speak with a human
            - You cannot provide a satisfactory answer

            Args:
                reason: Brief explanation of why human escalation is needed

            Returns:
                Confirmation message that escalation has been triggered
            """
            return f"ESCALATION_TRIGGERED: {reason}"

        return human_escalation

    def _create_get_booking_slots_tool(self):
        """Create the get booking slots tool"""

        @tool
        def get_booking_slots() -> str:
            """
            Retrieve available time slots for booking a call with an advisor.

            Use this tool when:
            - The student wants to schedule a call or meeting
            - The student asks about available times
            - The conversation naturally leads to booking a follow-up call

            Returns:
                JSON string with available slots including id, date, and time
            """
            if not self.db:
                return "Error: Database not available"

            slots = self.db.get_available_bookings()
            if not slots:
                return "No available slots at the moment."

            # Format slots as structured data
            formatted_slots = []
            for slot in slots:
                date_str = slot["date"].strftime("%Y-%m-%d") if hasattr(slot["date"], "strftime") else str(slot["date"])
                time_formatted = f"{slot['time'][:2]}:{slot['time'][2:]}"
                formatted_slots.append(
                    {"id": slot["id"], "date": date_str, "time": time_formatted, "time_raw": slot["time"]}
                )

            import json

            return json.dumps(formatted_slots)

        return get_booking_slots

    def _create_book_time_slot_tool(self):
        """Create the book time slot tool"""

        @tool
        def book_time_slot(
            slot_id: Optional[int] = None, date: Optional[str] = None, time: Optional[str] = None
        ) -> str:
            """
            Book a time slot for the student. Can accept either a slot_id or a date and time.

            Use this tool when:
            - The student selects a specific time slot
            - The student confirms they want to book a call

            Args:
                slot_id: The ID of the slot to book (if student provides ID)
                date: The date in YYYY-MM-DD format (if student describes the date)
                time: The time in HH:MM or HHMM format (if student describes the time)

            Returns:
                Confirmation message or error message
            """
            if not self.db:
                return "Error: Database not available"

            # If slot_id is provided, book directly
            if slot_id:
                # We'll need the chat_id to book, which will be passed via context
                # For now, return the slot_id to be handled by the main flow
                return f"BOOKING_REQUESTED:{slot_id}"

            # If date and time are provided, find matching slot
            if date and time:
                slots = self.db.get_available_bookings()

                # Normalize time format (remove colons, make 4 digits)
                time_normalized = time.replace(":", "").zfill(4)

                # Find matching slot
                for slot in slots:
                    slot_date = (
                        slot["date"].strftime("%Y-%m-%d") if hasattr(slot["date"], "strftime") else str(slot["date"])
                    )
                    if slot_date == date and slot["time"] == time_normalized:
                        return f"BOOKING_REQUESTED:{slot['id']}"

                return f"Error: No available slot found for {date} at {time}"

            return "Error: Please provide either a slot_id or both date and time"

        return book_time_slot

    def set_model(self, model_name: str):
        """Switch between OpenAI and Gemini"""
        if model_name in ["openai", "gemini"]:
            self.current_model = model_name
            print(f"Switched to {model_name} model")
        else:
            print(f"Invalid model name: {model_name}")

    def get_current_model(self) -> str:
        """Get the current active model"""
        return self.current_model

    def _get_system_prompt(self) -> str:
        """Generate system prompt with school data"""
        return f"""You are a helpful chatbot assistant for Havana University. Your role is to help prospective students learn about the school.

IMPORTANT INSTRUCTIONS:
1. ONLY answer questions based on the school information provided below. Do not make up information or use general knowledge.
2. If the information is not available in the school data, use the human_escalation tool to escalate to a human operator.
3. If a question is too complex or requires personalized advice, use the human_escalation tool.
4. If a student explicitly asks to speak with a human, use the human_escalation tool immediately.

BOOKING CALLS:
5. When a student wants to schedule a call or meeting, use the get_booking_slots tool to retrieve available times.
6. Present the available slots in a friendly, natural way (don't show raw JSON). Format dates nicely and group by date.
7. When a student selects a time slot, use the book_time_slot tool. You can accept:
   - Specific slot IDs (e.g., "I'll take slot 42")
   - Natural language (e.g., "I'd like the 9am slot on October 10th")
   - Parse dates and times from student messages intelligently
8. After successfully booking, provide a warm confirmation message.

SCHOOL INFORMATION:
{self.school_data}

Be friendly, concise, and helpful. Always maintain a professional tone. Use your tools proactively when appropriate."""

    def generate_response(
        self, user_message: str, chat_history: List[Dict[str, str]] = None, chat_id: int = None
    ) -> Dict[str, any]:
        """
        Generate a response using the current model with tool calling support
        Returns: {
            'response': str,
            'needs_escalation': bool,
            'booking_id': int (optional),
            'error': str (optional)
        }
        """
        # Select the active model
        if self.current_model == "openai":
            model = self.openai_model
            if not model:
                return {
                    "response": "OpenAI model is not configured. Please check your API key.",
                    "needs_escalation": True,
                    "error": "Model not configured",
                }
        else:  # gemini
            model = self.gemini_model
            if not model:
                return {
                    "response": "Gemini model is not configured. Please check your API key.",
                    "needs_escalation": True,
                    "error": "Model not configured",
                }

        try:
            # Bind tools to the model
            model_with_tools = model.bind_tools(self.tools)

            # Prepare messages
            messages = [SystemMessage(content=self._get_system_prompt())]

            # Add chat history if provided
            if chat_history:
                for msg in chat_history[-10:]:  # Include last 10 messages for context
                    if msg["role"] == "human":
                        messages.append(HumanMessage(content=msg["message"]))
                    elif msg["role"] == "ai":
                        messages.append(AIMessage(content=msg["message"]))

            # Add current user message
            messages.append(HumanMessage(content=user_message))

            # Generate response
            response = model_with_tools.invoke(messages)

            # Check if model wants to use tools
            needs_escalation = False
            booking_id = None
            tool_results = []

            if hasattr(response, "tool_calls") and response.tool_calls:
                # Execute tool calls
                messages.append(response)  # Add the AI message with tool calls

                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("args", {})
                    tool_call_id = tool_call.get("id", "")

                    # Find and execute the tool
                    tool_result = None
                    for tool in self.tools:
                        if tool.name == tool_name:
                            result = tool.invoke(tool_args)
                            tool_result = result

                            # Check for special flags in results
                            if isinstance(result, str):
                                if result.startswith("ESCALATION_TRIGGERED:"):
                                    needs_escalation = True
                                elif result.startswith("BOOKING_REQUESTED:"):
                                    booking_id = int(result.split(":")[1])
                                    # Actually book the slot
                                    if chat_id and self.db:
                                        success = self.db.book_slot(booking_id, chat_id)
                                        if success:
                                            tool_result = "Booking successful"
                                        else:
                                            tool_result = "Booking failed - slot may no longer be available"
                            break

                    # Add tool result as ToolMessage
                    if tool_result is not None:
                        messages.append(
                            ToolMessage(content=str(tool_result), tool_call_id=tool_call_id, name=tool_name)
                        )
                        tool_results.append({"tool": tool_name, "result": tool_result})

                # Generate final response with tool results
                final_response = model_with_tools.invoke(messages)
                bot_response = final_response.content
            else:
                # No tools called, use the direct response
                bot_response = response.content

            result = {"response": bot_response, "needs_escalation": needs_escalation}

            if booking_id:
                result["booking_id"] = booking_id

            return result

        except Exception as e:
            print(f"Error generating response: {e}")
            import traceback

            traceback.print_exc()
            return {
                "response": "I'm having trouble processing your request. Would you like to speak with a human advisor?",
                "needs_escalation": True,
                "error": str(e),
            }
