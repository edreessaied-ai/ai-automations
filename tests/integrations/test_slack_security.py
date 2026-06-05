"""
Tests for Slack request signature verification.
"""
import hashlib
import hmac
import time

import pytest
from fastapi import HTTPException
from starlette.requests import Request

import integrations.slack.security as security


def _make_request(headers: dict[str, str]) -> Request:
    """Build a minimal Starlette Request carrying the given headers."""
    raw_headers = [
        (key.lower().encode(), value.encode())
        for key, value in headers.items()
    ]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/slack/events",
        "headers": raw_headers,
    }
    return Request(scope)


def _sign(secret: str, timestamp: str, body: bytes) -> str:
    basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    digest = hmac.new(
        secret.encode(), basestring.encode(), hashlib.sha256
    ).hexdigest()
    return f"v0={digest}"


def test_no_secret_skips_verification(monkeypatch) -> None:
    monkeypatch.delenv("SLACK_SIGNING_SECRET", raising=False)
    # Should not raise even with no signature headers (simulator mode).
    security.verify_slack_signature(_make_request({}), b"{}")


def test_valid_signature_passes(monkeypatch) -> None:
    secret = "test-secret"
    monkeypatch.setenv("SLACK_SIGNING_SECRET", secret)
    body = b'{"type":"event_callback"}'
    timestamp = str(int(time.time()))
    request = _make_request(
        {
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": _sign(secret, timestamp, body),
        }
    )
    security.verify_slack_signature(request, body)


def test_invalid_signature_rejected(monkeypatch) -> None:
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
    timestamp = str(int(time.time()))
    request = _make_request(
        {
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": "v0=deadbeef",
        }
    )
    with pytest.raises(HTTPException) as exc:
        security.verify_slack_signature(request, b"{}")
    assert exc.value.status_code == 401


def test_stale_timestamp_rejected(monkeypatch) -> None:
    secret = "test-secret"
    monkeypatch.setenv("SLACK_SIGNING_SECRET", secret)
    body = b"{}"
    old_timestamp = str(int(time.time()) - 60 * 10)
    request = _make_request(
        {
            "X-Slack-Request-Timestamp": old_timestamp,
            "X-Slack-Signature": _sign(secret, old_timestamp, body),
        }
    )
    with pytest.raises(HTTPException) as exc:
        security.verify_slack_signature(request, body)
    assert exc.value.status_code == 401


def test_missing_headers_rejected(monkeypatch) -> None:
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
    with pytest.raises(HTTPException) as exc:
        security.verify_slack_signature(_make_request({}), b"{}")
    assert exc.value.status_code == 401
