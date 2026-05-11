import pytest
from app.core.errors import (
    ResiliError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    SSRFBlockedError,
    CreditsExhaustedError,
)

def test_base_resili_error_schema():
    """Test that the base ResiliError conforms to the Dec-D schema."""
    error = ResiliError()
    error_dict = error.to_dict()
    
    assert "error" in error_dict
    assert "code" in error_dict["error"]
    assert "message" in error_dict["error"]
    assert "hint" in error_dict["error"]
    assert "docs_url" in error_dict["error"]
    
    assert error_dict["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert error_dict["error"]["message"] == "An unexpected error occurred"

def test_not_found_error_schema():
    error = NotFoundError()
    error_dict = error.to_dict()
    assert error_dict["error"]["code"] == "NOT_FOUND"
    assert error.status_code == 404

def test_unauthorized_error_schema():
    error = UnauthorizedError()
    error_dict = error.to_dict()
    assert error_dict["error"]["code"] == "UNAUTHORIZED"
    assert error.status_code == 401

def test_forbidden_error_schema():
    error = ForbiddenError()
    error_dict = error.to_dict()
    assert error_dict["error"]["code"] == "FORBIDDEN"
    assert error.status_code == 403

def test_ssrf_blocked_error_schema():
    error = SSRFBlockedError()
    error_dict = error.to_dict()
    assert error_dict["error"]["code"] == "SSRF_BLOCKED"
    assert error.status_code == 400

def test_credits_exhausted_error_schema():
    error = CreditsExhaustedError()
    error_dict = error.to_dict()
    assert error_dict["error"]["code"] == "CREDITS_EXHAUSTED"
    assert error.status_code == 429
