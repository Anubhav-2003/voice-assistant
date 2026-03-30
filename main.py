from fastapi import FastAPI
from pydantic import BaseModel
from typing import Union, List, Any
import os
import json
import urllib.request

app = FastAPI()

class ChatPayload(BaseModel):
    prompt: str
    history: Union[str, List[Any]] = ""

@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    prompt_text = payload.prompt.lower().strip()
    
    if prompt_text in ["new chat", "clear history", "start over"]:
        return {"speech": "Starting a new conversation.", "new_history": []}
        
    messages = []
    if isinstance(payload.history, str):
        if payload.history.strip():
            try:
                messages = json.loads(payload.history)
            except json.JSONDecodeError:
                pass 
    elif isinstance(payload.history, list):
        messages = payload.history

    if not messages:
        messages.append({
            "role": "system", 
            "content": "You are a helpful, concise voice assistant. Keep answers brief so they can be spoken aloud naturally."
        })
        
    messages.append({"role": "user", "content": payload.prompt})

    # --- NEW VALIDATION LAYER ---
    api_key = os.environ.get("GROQ_API_KEY")
    
    # 1. Check if the variable is completely missing or None
    if not api_key:
        return {
            "speech": "Server Error: The Groq API key is missing from the Vercel environment variables.", 
            "new_history": payload.history
        }
        
    # Strip any accidental whitespace from copy-pasting
    api_key = api_key.strip() 
    
    # 2. Check if it looks like a valid Groq key (starts with gsk_)
    if not api_key.startswith("gsk_"):
        return {
            "speech": "Server Error: The Groq API key is malformed. It does not start with g-s-k.", 
            "new_history": payload.history
        }
    # ----------------------------

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
        return {"speech": f"Groq API Error: {str(e)}", "new_history": payload.history}