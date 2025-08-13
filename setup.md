# ChatGPT-like Chatbot with Free Gemini API

## Quick Setup

1. **Get your free Gemini API key**:
   - Go to https://aistudio.google.com/app/apikey
   - Create a new API key
   - Copy the key

2. **Set your Gemini API key**:
   - Edit `backend/.env` file
   - Replace `your-gemini-api-key-here` with your actual Gemini API key

3. **Start the application**:
   ```bash
   docker-compose up --build
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - MinIO Console: http://localhost:9001 (admin/minioadmin123)

## Test Gemini API

Test your API key with curl:
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" \
  -H 'Content-Type: application/json' \
  -H 'X-goog-api-key: YOUR_API_KEY' \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Explain how AI works in a few words"
          }
        ]
      }
    ]
  }'
```

## Environment Variables

Update `backend/.env`:
```
GEMINI_API_KEY=your-actual-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash
S3_BUCKET_NAME=chat-conversations
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin123
S3_ENDPOINT_URL=http://localhost:9000
```

## Features

- ✅ Free Gemini API integration
- ✅ S3 storage for chat history
- ✅ JWT authentication
- ✅ Responsive React UI
- ✅ Conversation management