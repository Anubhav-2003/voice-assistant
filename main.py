from fastapi import FastAPI
from pydantic import BaseModel
from typing import Union, List, Any
import os
import json
from groq import Groq # Importing the official SDK

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

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {
            "speech": "Server Error: API key is missing.", 
            "new_history": payload.history
        }

    try:
        # Initialize the official Groq client
        client = Groq(api_key=api_key.strip())
        
        # Call the model exactly as the documentation specifies
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7, # Slightly lowered for more concise/predictable voice responses
            max_tokens=150
        )
        
        # Extract the response from the SDK object
        bot_reply = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": bot_reply})
        
        return {"speech": bot_reply, "new_history": messages}
        
    except Exception as e:
        # If it still fails, the SDK provides much more detailed error messages
        return {"speech": f"Groq SDK Error: {str(e)}", "new_history": payload.history}