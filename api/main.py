"""
    Main API for the AI Automations project.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from agents.frontdesk_agent import run_agent

app = FastAPI()


class ChatRequest(BaseModel):
    """
    Request model for chat endpoint.
    """
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Chat endpoint.
    """
    result = await run_agent(req.message)
    return result
