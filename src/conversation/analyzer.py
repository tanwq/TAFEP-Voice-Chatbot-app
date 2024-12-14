# analyzer.py
import openai
import anthropic
import logging
import os
from config import Config
from typing import List, Dict, Optional

class ConversationAnalyzer:
    def __init__(self):
        """Initialize the conversation analyzer with selected AI model"""
        self.logger = logging.getLogger(__name__)
        self.ai_provider = Config.AI_MODEL
        
        # Initialize appropriate client based on config
        if self.ai_provider == "OpenAI":
            openai.api_key = Config.OPENAI_API_KEY
            self.client = openai.chat.completions
        elif self.ai_provider == "AnthropicAI":
            self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unsupported AI provider: {self.ai_provider}")
    
    def _get_openai_prompt(self, user_input, conversation_repository, conversation_state):
        """Generate OpenAI-style prompt"""
        return f"""
        You are a professional TAFEP digital advisor. 
        User input: "{user_input}"
        Conversation history: {conversation_repository}
        Current states:
        - Issue Established: {'Yes' if conversation_state['issue_established'] else 'No'}
        - Discrimination Type Categorized: {'Yes' if conversation_state['discrimination_type_categorized'] else 'No'}
        - Probe Count: {conversation_state['probe_counter']}
        - Probing Completed: {'Yes' if conversation_state['probing_completed'] else 'No'}

        Determine the next action category:
        1. "Establish Issue" (if issue not established)
        2. "Categorize Discrimination Type" (if issue established but type not categorized)
        3. "Probe for Further Information" (if more details needed)
        4. "Ask About Filing Case" (if ready to file)
        5. "Closure Conversation" (if case filed)
        """

    def _get_anthropic_prompt(self, user_input, conversation_repository, conversation_state):
        """Generate Claude-style prompt with XML tags"""
        return f"""
        <system>You are a TAFEP digital advisor tasked with analyzing conversations about workplace discrimination. You must respond with exactly one of these categories and nothing else:
        - "Establish Issue"
        - "Categorize Discrimination Type"
        - "Probe for Further Information"
        - "Ask About Filing Case"
        - "Closure Conversation"
        </system>

        <context>
        <conversation>
        <input>{user_input}</input>
        <history>{conversation_repository}</history>
        </conversation>

        <state>
        <issue_established>{conversation_state['issue_established']}</issue_established>
        <discrimination_categorized>{conversation_state['discrimination_type_categorized']}</discrimination_categorized>
        <probe_count>{conversation_state['probe_counter']}</probe_count>
        <probing_completed>{conversation_state['probing_completed']}</probing_completed>
        </state>
        </context>

        <rules>
        - If issue is not established, respond with "Establish Issue"
        - If issue is established but discrimination type not categorized, respond with "Categorize Discrimination Type"
        - If more information is needed and probe count is below limit, respond with "Probe for Further Information"
        - If sufficient information gathered, respond with "Ask About Filing Case"
        - If case is filed, respond with "Closure Conversation"
        </rules>
        """

    def analyze_user_input(self, user_input: str, conversation_repository: List, conversation_state: Dict) -> str:
        """
        Analyze user input and determine next action
        
        Args:
            user_input (str): User's message
            conversation_repository (list): Conversation history
            conversation_state (dict): Current conversation state
            
        Returns:
            str: Next action category
        """
        try:
            # Get appropriate prompt based on AI provider
            if self.ai_provider == "OpenAI":
                prompt = self._get_openai_prompt(user_input, conversation_repository, conversation_state)
            else:  # AnthropicAI
                prompt = self._get_anthropic_prompt(user_input, conversation_repository, conversation_state)
                
            # Generate response
            response = self.generate_ai_response(prompt)
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error analyzing user input: {e}")
            return "Error"

    def generate_ai_response(self, prompt: str) -> str:
        """
        Generate response using selected AI model
        
        Args:
            prompt (str): Prompt for AI model
            
        Returns:
            str: AI generated response
        """
        try:
            if self.ai_provider == "OpenAI":
                return self._generate_openai_response(prompt)
            else:
                return self._generate_anthropic_response(prompt)
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return "Error"
            
    def _generate_openai_response(self, prompt: str) -> str:
        """Generate response using OpenAI"""
        try:
            response = self.client.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional TAFEP advisor speaking directly to users via voice chat. Use concise, clear language and show empathy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"OpenAI error: {e}")
            raise

    def _generate_anthropic_response(self, prompt: str) -> str:
        """Generate response using Anthropic's Claude"""
        try:
            response = self.client.messages.create(
                model=Config.AI_MODEL_VERSION,
                max_tokens=1024,
                system="You are a professional TAFEP advisor speaking directly to users via voice chat. Use concise, clear language and show empathy.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return response.content[0].text
        except Exception as e:
            self.logger.error(f"Anthropic error: {e}")
            raise

    def analyze_emotion(self, emotions: List[tuple]) -> str:
        """
        Analyze detected emotions and generate appropriate response modifier
        
        Args:
            emotions (list): List of (emotion, score) tuples
            
        Returns:
            str: Response modification suggestion
        """
        if not emotions:
            return ""
            
        try:
            # Create prompt for emotion analysis
            emotion_prompt = f"""
            <system>You are analyzing emotions detected in a user's voice to adjust the response tone appropriately.</system>
            
            <emotions>
            {', '.join([f'{emotion}: {score:.2%}' for emotion, score in emotions])}
            </emotions>
            
            <task>
            Based on these emotions, suggest one SHORT phrase for how to modify the response tone.
            Examples: "be more empathetic", "remain calm and professional", "show more concern"
            </task>
            """
            
            response = self.generate_ai_response(emotion_prompt)
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error analyzing emotions: {e}")
            return ""