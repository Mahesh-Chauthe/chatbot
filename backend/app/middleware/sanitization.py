from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import re
import html
import json
from typing import Any, Dict, List

class SanitizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Patterns to detect and clean potentially malicious content
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
        ]

    def sanitize_string(self, text: str) -> str:
        """Sanitize string input to prevent XSS and injection attacks"""
        if not isinstance(text, str):
            return text
        
        # HTML escape to prevent XSS
        text = html.escape(text)
        
        # Remove potentially dangerous patterns
        for pattern in self.xss_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove null bytes and control characters
        text = text.replace('\x00', '')
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = self.sanitize_list(value)
            else:
                sanitized[key] = value
        return sanitized

    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """Sanitize list items"""
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)
        return sanitized

    async def dispatch(self, request: Request, call_next):
        # Only sanitize requests with JSON body
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type.startswith("application/json"):
                body = await request.body()
                if body:
                    try:
                        data = json.loads(body)
                        if isinstance(data, dict):
                            sanitized_data = self.sanitize_dict(data)
                            # Replace request body with sanitized data
                            request._body = json.dumps(sanitized_data).encode()
                        elif isinstance(data, list):
                            sanitized_data = self.sanitize_list(data)
                            request._body = json.dumps(sanitized_data).encode()
                    except json.JSONDecodeError:
                        # Invalid JSON, let the endpoint handle the error
                        pass

        response = await call_next(request)
        return response
