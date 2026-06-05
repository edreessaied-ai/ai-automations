"""
Slack request signature verification.

Slack signs every request with an HMAC-SHA256 of the raw body using the app's
signing secret. Verifying it ensures inbound events/commands/interactions
genuinely originate from Slack and not a forged request to a public URL.

When `SLACK_SIGNING_SECRET` is unset the check is skipped, which keeps the
local Slack simulator (which posts unsigned JSON) working unchanged. Set the
secret in any environment that is exposed to real Slack traffic.
"""
import hashlib
import hmac
import os
import time

from fastapi import HTTPException, Request

from utilities.logger import get_logger

log_handler = get_logger(__name__)

# Slack's current signature version prefix.
_SIGNATURE_VERSION = "v0"
# Reject requests whose timestamp is older than this, to blunt replay attacks.
_MAX_TIMESTAMP_SKEW_SECONDS = 60 * 5


def _signing_secret() -> str | None:
    """Return the configured Slack signing secret, or None when unset."""
    return os.getenv("SLACK_SIGNING_SECRET")


def verify_slack_signature(request: Request, raw_body: bytes) -> None:
    """
    Verify the `X-Slack-Signature` header against the raw request body.

    No-op when no signing secret is configured (local/simulator mode). Raises
    HTTP 401 when a secret is configured but the signature is missing, stale,
    or invalid.
    """
    secret = _signing_secret()
    if not secret:
        return

    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if not timestamp or not signature:
        log_handler.warning("Rejecting Slack request: missing signature.")
        raise HTTPException(status_code=401, detail="Missing Slack signature.")

    try:
        request_age = abs(time.time() - int(timestamp))
    except ValueError as exc:
        log_handler.warning("Rejecting Slack request: invalid timestamp")
        raise HTTPException(
            status_code=401, detail="Invalid Slack timestamp."
        ) from exc

    if request_age > _MAX_TIMESTAMP_SKEW_SECONDS:
        log_handler.warning("Rejecting Slack request: stale timestamp")
        raise HTTPException(status_code=401, detail="Stale Slack request.")

    basestring = f"{_SIGNATURE_VERSION}:{timestamp}:{raw_body.decode('utf-8')}"
    digest = hmac.new(
        secret.encode("utf-8"),
        basestring.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    expected_signature = f"{_SIGNATURE_VERSION}={digest}"

    if not hmac.compare_digest(expected_signature, signature):
        log_handler.warning("Rejecting Slack request: signature mismatch")
        raise HTTPException(status_code=401, detail="Invalid Slack signature.")
