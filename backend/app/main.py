from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from app.middleware.auth import AuthMiddleware
from app.middleware.sanitization import SanitizationMiddleware  
from app.middleware.logging import LoggingMiddleware
from app.routers import chat, auth

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Organization Chat API",
    description="A secure ChatGPT-like API for organizational use",
    version="1.0.0"
)

# CORS middleware - Configure for your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware (order matters!)
app.add_middleware(LoggingMiddleware)
app.add_middleware(SanitizationMiddleware)
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Organization Chat API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "organization-chat-api"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
