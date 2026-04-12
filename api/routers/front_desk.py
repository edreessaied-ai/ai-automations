"""
    Front Desk Router
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/slack/commands")
async def slack_commands(request: Request):
    form = await request.form()

    command = form.get("command")
    text = form.get("text")
    user_id = form.get("user_id")
    channel_id = form.get("channel_id")

    # For now: stub response
    return JSONResponse(
        {
            "response_type": "ephemeral",
            "text": f"Received: {text}, from user {user_id} "
            f"in channel {channel_id} for command {command}",
        }
    )
