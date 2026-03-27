"""
    Main API for the AI Automations project.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.frontdesk_agent import run_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 👈 important
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return result["message"]


@app.get("/")
def root():
    """
    Root endpoint.
    """
    return {"message": "API is running"}
