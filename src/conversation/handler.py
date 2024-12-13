import logging
import asyncio
from utils.helpers import normalize_string
from .analyzer import ConversationAnalyzer
from services.email_sender import EmailSender
from config import Config

class ConversationHandler:
    def __init__(self, tts_service, transcript_queue, websocket_connection):
        """Initialize conversation handler"""
        self.logger = logging.getLogger(__name__)
        self.analyzer = ConversationAnalyzer()
        self.email_sender = EmailSender()
        self.tts_service = tts_service
        self.transcript_queue = transcript_queue
        self.websocket_connection = websocket_connection
        self.processing_lock = asyncio.Lock()

    async def handle_conversation(self, conversation_repository=None, conversation_state=None):
        """Main conversation handling loop"""
        if conversation_repository is None:
            conversation_repository = []
        if conversation_state is None:
            conversation_state = {
                "issue_established": False,
                "discrimination_type_categorized": False,
                "probe_counter": 0,
                "probing_completed": False,
                "user_agreed_to_file_case": False
            }

        # Initial greeting
        introduction = "Hello, welcome to TAFEP!"
        async with self.processing_lock:
            await self.tts_service.speak_with_wavenet(introduction)

        while True:
            try:
                # Wait for user input
                message = await self._get_transcript()
                
                if message and isinstance(message, dict) and message["type"] == "transcript":
                    transcript = message["text"]
                    emotions = message["emotions"]
                    
                    # Set processing flag
                    self.websocket_connection.is_processing_response = True
                    
                    try:
                        # Generate response
                        response = await self._generate_response(
                            transcript,
                            emotions,
                            conversation_repository,
                            conversation_state
                        )
                        
                        if response:
                            if response == "Error":
                                self.logger.error("Error generating response")
                            else:
                                # Add response to conversation history
                                conversation_repository.append({
                                    "role": "assistant",
                                    "content": response
                                })
                                # Speak response
                                await self.tts_service.speak_with_wavenet(response)
                    finally:
                        # Reset processing flag
                        self.websocket_connection.is_processing_response = False
                        
            except Exception as e:
                self.logger.error(f"Error in conversation loop: {str(e)}")
                continue

    async def _get_transcript(self, timeout=5):
        """Get transcript from queue with timeout"""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.transcript_queue.get(timeout=timeout)
            )
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Error getting transcript: {e}")
            return None

    async def _generate_response(self, user_input, emotions, conversation_repository, conversation_state):
        """Generate appropriate response based on conversation state"""
        try:
            # Analyze user input to determine next action
            category = await self.analyzer.analyze_user_input(
                user_input,
                conversation_repository,
                conversation_state
            )
            
            # Get appropriate handler function
            handler = self._get_handler_function(category)
            if handler:
                return await handler(user_input, emotions, conversation_repository, conversation_state)
            else:
                self.logger.error(f"Unknown category: {category}")
                return "Error"
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "Error"

    def _get_handler_function(self, category):
        """Get the appropriate handler function based on category"""
        category = normalize_string(category)
        
        handlers = {
            "establishissue": self._establish_issue,
            "categorizediscriminationtype": self._categorize_discrimination,
            "probeforfurtherinformation": self._probe_further_information,
            "askaboutfilingcase": self._ask_to_file_case,
            "closureconversation": self._closure_conversation
        }
        
        return handlers.get(category)

    async def _establish_issue(self, user_input, emotions, conversation_repository, conversation_state):
        """Handle issue establishment"""
        prompt = f"""
        Based on: "{user_input}"
        Previous conversation: {conversation_repository}
        
        Task: Establish the specific discrimination issue.
        1. Show empathy and understanding
        2. Clarify the type of discrimination
        3. Ask for specific incidents
        4. Keep response concise (max 30 words)
        """
        
        response = await self.analyzer.generate_ai_response(prompt)
        conversation_state["issue_established"] = True
        return response

    async def _categorize_discrimination(self, user_input, emotions, conversation_repository, conversation_state):
        """Handle discrimination categorization"""
        prompt = f"""
        Based on: "{user_input}"
        Previous conversation: {conversation_repository}
        
        Task: Categorize the discrimination type.
        1. Identify discrimination category (racial, gender, age, etc.)
        2. Confirm understanding
        3. Express concern appropriately
        4. Keep response concise (max 30 words)
        """
        
        response = await self.analyzer.generate_ai_response(prompt)
        conversation_state["discrimination_type_categorized"] = True
        return response

    async def _probe_further_information(self, user_input, emotions, conversation_repository, conversation_state):
        """Handle information gathering"""
        conversation_state["probe_counter"] += 1
        
        if conversation_state["probe_counter"] >= Config.PROBE_LIMIT:
            conversation_state["probing_completed"] = True
            return await self._ask_to_file_case(user_input, emotions, conversation_repository, conversation_state)
        
        prompt = f"""
        Based on: "{user_input}"
        Previous conversation: {conversation_repository}
        Probe count: {conversation_state['probe_counter']}
        
        Task: Gather more details about the discrimination case.
        1. Ask about specific incidents
        2. Request dates and times
        3. Inquire about witnesses
        4. Keep response concise (max 30 words)
        """
        
        return await self.analyzer.generate_ai_response(prompt)

    async def _ask_to_file_case(self, user_input, emotions, conversation_repository, conversation_state):
        """Handle case filing request"""
        if "yes" in user_input.lower():
            return await self._file_case_and_send_email(conversation_repository)
        
        prompt = f"""
        Based on gathered information:
        User input: "{user_input}"
        Conversation: {conversation_repository}
        
        Task: Ask if they want to file a case with TAFEP.
        1. Summarize key points
        2. Explain filing process
        3. Request consent
        4. Keep response concise (max 30 words)
        """
        
        return await self.analyzer.generate_ai_response(prompt)

    async def _closure_conversation(self, user_input, emotions, conversation_repository, conversation_state):
        """Handle conversation closure"""
        prompt = f"""
        Task: Close the conversation professionally.
        1. Thank the user
        2. Confirm next steps
        3. Provide TAFEP contact info
        4. Keep response concise (max 30 words)
        """
        
        return await self.analyzer.generate_ai_response(prompt)

    async def _file_case_and_send_email(self, conversation_repository):
        """Handle case filing and email sending"""
        try:
            # Generate case summary
            case_summary = await self._generate_case_summary(conversation_repository)
            
            # Send email
            email_sent = await self.email_sender.send_case_email(
                case_summary,
                conversation_repository
            )
            
            if email_sent:
                return "Thank you. Your case has been filed with TAFEP. You will receive a confirmation email shortly."
            else:
                return "Error"
                
        except Exception as e:
            self.logger.error(f"Error filing case: {e}")
            return "Error"

    async def _generate_case_summary(self, conversation_repository):
        """Generate summary of the case"""
        prompt = f"""
        Based on this conversation: {conversation_repository}
        
        Create a concise summary including:
        1. Type of discrimination
        2. Key incidents
        3. Evidence provided
        4. Timeline of events
        """
        
        return await self.analyzer.generate_ai_response(prompt)