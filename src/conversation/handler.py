# handler.py
import logging
import streamlit as st
from src.utils.helpers import normalize_string
from .analyzer import ConversationAnalyzer
from config import Config
from typing import List, Optional, Dict, Tuple

class ConversationHandler:
    def __init__(self, tts_service):
        """Initialize conversation handler"""
        self.logger = logging.getLogger(__name__)
        self.analyzer = ConversationAnalyzer()
        self.tts_service = tts_service

    def handle_conversation(self, conversation_repository=None, conversation_state=None):
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
        self.tts_service.speak_with_wavenet(introduction)

    def generate_response(self, user_input: str, emotions: List[tuple] = None) -> str:
        try:
            # Get conversation data
            conversation_repository = self._get_conversation_repository()
            conversation_state = self._get_conversation_state()
            
            # Get next action category
            category = self.analyzer.analyze_user_input(
                user_input,
                conversation_repository,
                conversation_state
            )
            
            if category == "Error":
                self.logger.error("Error determining conversation category")
                return "I apologize, but I encountered an error. Could you please repeat that?"
                
            # Get appropriate handler
            handler = self._get_handler_function(category)
            if handler:
                response = handler(
                    user_input,
                    emotions,
                    conversation_repository,
                    conversation_state
                )
                if response:
                    self.tts_service.speak_with_wavenet(response)
                    return response
                    
            return "I apologize, but I encountered an error. Could you please repeat that?"
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error. Could you please repeat that?"

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

    def _establish_issue(self, user_input, emotions, conversation_repository, conversation_state):
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
        
        response = self.analyzer.generate_ai_response(prompt)
        conversation_state["issue_established"] = True
        return response

    def _categorize_discrimination(self, user_input, emotions, conversation_repository, conversation_state):
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
        
        response = self.analyzer.generate_ai_response(prompt)
        conversation_state["discrimination_type_categorized"] = True
        return response

    def _probe_further_information(self, user_input, emotions, conversation_repository, conversation_state):
        """Handle information gathering"""
        conversation_state["probe_counter"] += 1
        
        if conversation_state["probe_counter"] >= Config.PROBE_LIMIT:
            conversation_state["probing_completed"] = True
            return self._ask_to_file_case(user_input, emotions, conversation_repository, conversation_state)
        
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
        
        return self.analyzer.generate_ai_response(prompt)

    def _ask_to_file_case(self, user_input, emotions, conversation_repository, conversation_state):
        """Handle case filing request"""
        if "yes" in user_input.lower():
            return self._file_case_and_send_email(conversation_repository)
        
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
        
        return self.analyzer.generate_ai_response(prompt)

    def _closure_conversation(self, user_input, emotions, conversation_repository, conversation_state):
        """Handle conversation closure"""
        prompt = f"""
        Task: Close the conversation professionally.
        1. Thank the user
        2. Confirm next steps
        3. Provide TAFEP contact info
        4. Keep response concise (max 30 words)
        """
        
        return self.analyzer.generate_ai_response(prompt)

    def _file_case_and_send_email(self, conversation_repository):
        """Handle case filing and email sending"""
        try:
            # Generate case summary
            case_summary = self._generate_case_summary(conversation_repository)
            
            if case_summary:
                return "Thank you. Your case has been filed with TAFEP. You will receive a confirmation email shortly."
            else:
                return "Error"
                
        except Exception as e:
            self.logger.error(f"Error filing case: {e}")
            return "Error"

    def _generate_case_summary(self, conversation_repository):
        """Generate summary of the case"""
        prompt = f"""
        Based on this conversation: {conversation_repository}
        
        Create a concise summary including:
        1. Type of discrimination
        2. Key incidents
        3. Evidence provided
        4. Timeline of events
        """
        
        return self.analyzer.generate_ai_response(prompt)

    def _get_conversation_state(self):
        """Get current conversation state from session"""
        if "conversation_state" not in st.session_state:
            st.session_state.conversation_state = {
                "issue_established": False,
                "discrimination_type_categorized": False,
                "probe_counter": 0,
                "probing_completed": False,
                "user_agreed_to_file_case": False
            }
        return st.session_state.conversation_state

    def _get_conversation_repository(self):
        """Get conversation history from session"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        return st.session_state.messages