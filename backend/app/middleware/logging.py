from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import logging
import time
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request details
        logger.info(
            f"Request: {request.method} {request.url} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log response details
        logger.info(
            f"Response: {response.status_code} - "
            f"Process time: {process_time:.3f}s - "
            f"Path: {request.url.path}"
        )
        
        # Log errors with more details
        if response.status_code >= 400:
            logger.error(
                f"Error Response: {response.status_code} - "
                f"Path: {request.url.path} - "
                f"Method: {request.method}"
            )
        
        return response
