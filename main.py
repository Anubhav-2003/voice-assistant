from fastapi import FastAPI
from pydantic import BaseModel
import os
import json
import urllib.request

app = FastAPI()

class ChatPayload(BaseModel):
    prompt: str
    history: list

@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    prompt_text = payload.prompt.lower().strip()
    
    # Handle voice commands programmatically
    if prompt_text in ["new chat", "clear history", "start over"]:
        return {"speech": "Starting a new conversation.", "new_history": []}
        
    messages = payload.history
    if not messages:
        messages.append({
            "role": "system", 
            "content": "You are a helpful, concise voice assistant. Keep answers brief so they can be spoken aloud naturally."
        })
        
    messages.append({"role": "user", "content": payload.prompt})

    api_key = os.environ.get("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": 150
    }
    
    try:
        req = urllib.request.Request(url, headers=headers, data=json.dumps(data).encode("utf-8"))
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode("utf-8"))
        
        bot_reply = result["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": bot_reply})
        
        return {"speech": bot_reply, "new_history": messages}
        
    except Exception as e:
        return {"speech": "Connection error.", "new_history": payload.history}