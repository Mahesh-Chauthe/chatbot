from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.services.chat_service import ChatService
from app.services.s3_service import S3Service

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v.strip()) > 4000:
            raise ValueError('Message too long (max 4000 characters)')
        return v.strip()

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    timestamp: datetime

def get_chat_service() -> ChatService:
    return ChatService()

def get_s3_service() -> S3Service:
    return S3Service()

@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    request: Request,
    chat_service: ChatService = Depends(get_chat_service),
    s3_service: S3Service = Depends(get_s3_service)
):
    """Send a message to ChatGPT and save the conversation to S3"""
    user_id = request.state.user_id
    
    conversation_id = chat_message.conversation_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    
    try:
        # Get existing conversation for context
        existing_conversation = await s3_service.get_conversation(conversation_id, user_id)
        conversation_history = existing_conversation.get("messages", []) if existing_conversation else []
        
        # Get response from ChatGPT
        llm_response = await chat_service.generate_response(
            message=chat_message.message,
            conversation_id=conversation_id,
            user_id=user_id,
            conversation_history=conversation_history
        )
        
        # Prepare new messages
        new_messages = [
            {
                "id": message_id,
                "role": "user",
                "content": chat_message.message,
                "timestamp": timestamp.isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": llm_response,
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        # Update conversation data
        chat_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "messages": conversation_history + new_messages
        }
        
        # Save to S3
        await s3_service.save_conversation(conversation_id, chat_data)
        
        return ChatResponse(
            response=llm_response,
            conversation_id=conversation_id,
            message_id=message_id,
            timestamp=timestamp
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )

@router.get("/conversations")
async def get_conversations(
    request: Request,
    s3_service: S3Service = Depends(get_s3_service)
):
    """Get list of conversations for the current user"""
    user_id = request.state.user_id
    
    try:
        conversations = await s3_service.get_user_conversations(user_id)
        return {"conversations": conversations}
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching conversations"
        )

@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    request: Request,
    s3_service: S3Service = Depends(get_s3_service)
):
    """Get a specific conversation by ID"""
    user_id = request.state.user_id
    
    try:
        conversation = await s3_service.get_conversation(conversation_id, user_id)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching conversation"
        )