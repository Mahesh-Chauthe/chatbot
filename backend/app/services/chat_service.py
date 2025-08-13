import google.generativeai as genai
from typing import Optional, List, Dict
from fastapi import HTTPException
import os
import logging

logger = logging.getLogger(__name__)

class ChatService:
    """Service for Google Gemini API integration"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        # Default system prompt for organization
        self.default_system_prompt = (
            "You are a helpful AI assistant for this organization. "
            "Provide accurate, professional, and helpful responses. "
            "Keep responses concise but informative. "
            "Do not share sensitive information or engage in inappropriate content. "
            "If you're unsure about something, say so rather than guessing."
        )
        
    async def generate_response(
        self, 
        message: str, 
        conversation_id: str, 
        user_id: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Generate response from Google Gemini API"""
        
        # Use default system prompt if none provided
        if not system_prompt:
            system_prompt = self.default_system_prompt
        
        try:
            # Combine system prompt with user message
            # Gemini doesn't have a separate system role, so we include it in the prompt
            if conversation_history and len(conversation_history) > 0:
                # Build conversation context from history
                context_messages = []
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    if msg.get("role") == "user":
                        context_messages.append(f"User: {msg['content']}")
                    elif msg.get("role") == "assistant":
                        context_messages.append(f"Assistant: {msg['content']}")
                
                full_prompt = f"""System: {system_prompt}

Previous conversation:
{chr(10).join(context_messages)}

Current user message: {message}

Please respond as the assistant:"""
            else:
                full_prompt = f"""System: {system_prompt}

User: {message}

Please respond as the assistant:"""
            
            logger.info(f"Sending request to Gemini API for user {user_id}")
            
            # Generate response using Gemini
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2048,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40
                )
            )
            
            assistant_response = response.text
            
            if not assistant_response:
                return "I apologize, but I couldn't generate a response. Please try again."
            
            logger.info(f"Successfully generated response for user {user_id}")
            return assistant_response
            
        except Exception as e:
            error_message = str(e).lower()
            logger.error(f"Gemini API error: {str(e)}")
            
            if "quota" in error_message or "rate limit" in error_message:
                raise HTTPException(
                    status_code=429, 
                    detail="API rate limit exceeded. Please try again in a few moments."
                )
            elif "api_key" in error_message or "authentication" in error_message:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid API configuration. Please contact administrator."
                )
            elif "safety" in error_message:
                raise HTTPException(
                    status_code=400,
                    detail="Content was blocked due to safety policies. Please rephrase your message."
                )
            else:
                raise HTTPException(
                    status_code=500, 
                    detail="An unexpected error occurred while processing your request."
                )
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about the current model"""
        return {
            "model": self.model_name,
            "provider": "Google Gemini",
            "api_version": "v1beta"
        }
