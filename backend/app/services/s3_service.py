import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json
import os
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class S3Service:
    """Service for S3-compatible storage operations"""
    
    def __init__(self):
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv('S3_ENDPOINT_URL'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            self.bucket_name = os.getenv('S3_BUCKET_NAME', 'chat-conversations')
            
            # Ensure bucket exists
            self._ensure_bucket_exists()
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise ValueError("AWS credentials are required")
        except Exception as e:
            logger.error(f"Failed to initialize S3 service: {str(e)}")
            raise
    
    def _ensure_bucket_exists(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    # Create bucket
                    if os.getenv('AWS_REGION') == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': os.getenv('AWS_REGION', 'us-east-1')
                            }
                        )
                    logger.info(f"Created S3 bucket: {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error accessing bucket: {e}")
                raise
    
    async def save_conversation(self, conversation_id: str, conversation_data: Dict) -> bool:
        """Save conversation data to S3"""
        try:
            # Add metadata
            conversation_data.update({
                "updated_at": datetime.utcnow().isoformat(),
                "conversation_id": conversation_id
            })
            
            user_id = conversation_data.get("user_id")
            if not user_id:
                logger.error("User ID is required for saving conversation")
                return False
            
            # Create S3 key with organized structure
            s3_key = f"conversations/{user_id}/{conversation_id}.json"
            
            # Check if conversation exists and merge messages
            existing_data = await self.get_conversation(conversation_id, user_id)
            if existing_data:
                # Merge new messages with existing ones
                existing_messages = existing_data.get("messages", [])
                new_messages = conversation_data.get("messages", [])
                
                # Create set of existing message IDs to avoid duplicates
                existing_message_ids = {msg.get("id") for msg in existing_messages}
                
                # Add only new messages
                for msg in new_messages:
                    if msg.get("id") not in existing_message_ids:
                        existing_messages.append(msg)
                
                conversation_data["messages"] = existing_messages
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(conversation_data, indent=2, default=str),
                ContentType='application/json',
                Metadata={
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'updated_at': datetime.utcnow().isoformat(),
                    'message_count': str(len(conversation_data.get("messages", [])))
                }
            )
            
            logger.info(f"Successfully saved conversation {conversation_id} for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Error saving conversation to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving conversation: {str(e)}")
            return False
    
    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Dict]:
        """Retrieve conversation data from S3"""
        try:
            s3_key = f"conversations/{user_id}/{conversation_id}.json"
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            conversation_data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Successfully retrieved conversation {conversation_id} for user {user_id}")
            return conversation_data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.info(f"Conversation {conversation_id} not found for user {user_id}")
                return None
            logger.error(f"Error retrieving conversation from S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving conversation: {str(e)}")
            return None
    
    async def get_user_conversations(self, user_id: str) -> List[Dict]:
        """Get list of conversations for a user"""
        try:
            prefix = f"conversations/{user_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            conversations = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    try:
                        # Get conversation metadata
                        conv_response = self.s3_client.get_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        conv_data = json.loads(conv_response['Body'].read().decode('utf-8'))
                        
                        # Extract summary info
                        messages = conv_data.get('messages', [])
                        first_message = ""
                        if messages:
                            # Find first user message
                            for msg in messages:
                                if msg.get('role') == 'user':
                                    first_message = msg.get('content', '')
                                    break
                        
                        if not first_message:
                            first_message = "No messages"
                        
                        conversations.append({
                            'conversation_id': conv_data.get('conversation_id'),
                            'updated_at': conv_data.get('updated_at'),
                            'message_count': len(messages),
                            'preview': first_message[:100] + "..." if len(first_message) > 100 else first_message
                        })
                        
                    except Exception as e:
                        logger.error(f"Error processing conversation {obj['Key']}: {e}")
                        continue
            
            # Sort by updated_at descending (most recent first)
            conversations.sort(
                key=lambda x: x.get('updated_at', ''), 
                reverse=True
            )
            
            logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")
            return conversations
            
        except ClientError as e:
            logger.error(f"Error retrieving user conversations: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving user conversations: {str(e)}")
            return []
    
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation from S3"""
        try:
            s3_key = f"conversations/{user_id}/{conversation_id}.json"
            
            # Check if conversation exists first
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    return False
                raise
            
            # Delete the object
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Successfully deleted conversation {conversation_id} for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting conversation from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting conversation: {str(e)}")
            return False
