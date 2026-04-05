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


@app.post("/chat")  # type: ignore[misc]
async def chat(req: ChatRequest) -> str:
    """
    Chat endpoint that takes user message,
    and returns AI-generated message.
    """
    result = await run_agent(req.message)

    message = result.get("message")
    if not isinstance(message, str):
        raise ValueError("Invalid response from agent")

    return message


@app.get("/")  # type: ignore[misc]
def root() -> dict[str, str]:
    """
    Root endpoint.
    """
    return {"message": "API is running"}
