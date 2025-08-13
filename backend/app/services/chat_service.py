import httpx
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
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        
    async def generate_response(
        self, 
        message: str, 
        conversation_id: str, 
        user_id: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Generate response from Google Gemini API"""
        
        try:
            # Build conversation context
            full_text = "You are a helpful AI assistant.\n\n"
            
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages
                    if msg.get("role") == "user":
                        full_text += f"User: {msg['content']}\n"
                    elif msg.get("role") == "assistant":
                        full_text += f"Assistant: {msg['content']}\n"
            
            full_text += f"User: {message}\nAssistant:"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": full_text
                            }
                        ]
                    }
                ]
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key
            }
            
            url = f"{self.base_url}/{self.model_name}:generateContent"
            
            logger.info(f"Sending request to Gemini API for user {user_id}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail="Error communicating with AI service"
                    )
                
                data = response.json()
                
                if "candidates" not in data or not data["candidates"]:
                    return "I apologize, but I couldn't generate a response. Please try again."
                
                assistant_response = data["candidates"][0]["content"]["parts"][0]["text"]
                
                logger.info(f"Successfully generated response for user {user_id}")
                return assistant_response.strip()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while processing your request."
            )