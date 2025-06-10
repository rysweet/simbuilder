"""
Tests for JWT handler functionality.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest
from jose import JWTError

from simbuilder_api.auth.jwt_handler import JWTHandler
from simbuilder_api.auth.jwt_handler import TokenData


class TestJWTHandler:
    """Test JWT token encoding and decoding functionality."""

    def test_init_handler(self):
        """Test JWT handler initialization."""
        handler = JWTHandler("test-secret", "test-issuer")

        assert handler.secret == "test-secret"  # noqa: S105
        assert handler.issuer == "test-issuer"
        assert handler.algorithm == "HS256"

    def test_init_handler_default_issuer(self):
        """Test JWT handler initialization with default issuer."""
        handler = JWTHandler("test-secret")

        assert handler.secret == "test-secret"  # noqa: S105
        assert handler.issuer == "simbuilder"
        assert handler.algorithm == "HS256"

    def test_encode_token_default_expiry(self):
        """Test token encoding with default expiry time."""
        handler = JWTHandler("test-secret")

        token = handler.encode_token("user123")

        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts

    def test_encode_token_custom_expiry(self):
        """Test token encoding with custom expiry time."""
        handler = JWTHandler("test-secret")
        expires_delta = timedelta(minutes=30)

        token = handler.encode_token("user456", expires_delta)

        assert isinstance(token, str)
        # Verify token can be decoded and has correct expiry
        decoded = handler.decode_token(token)

        # Token should expire in approximately 30 minutes
        exp_time = datetime.fromtimestamp(decoded.exp, UTC)
        expected_exp = datetime.now(UTC) + expires_delta

        # Allow 1 second tolerance for test timing
        assert abs((exp_time - expected_exp).total_seconds()) < 1

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        handler = JWTHandler("test-secret", "test-issuer")

        token = handler.encode_token("user789")
        decoded = handler.decode_token(token)

        assert isinstance(decoded, TokenData)
        assert decoded.sub == "user789"
        assert decoded.iss == "test-issuer"
        assert isinstance(decoded.exp, int)
        assert isinstance(decoded.iat, int)

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        handler = JWTHandler("test-secret")

        with pytest.raises(JWTError, match="Invalid token"):
            handler.decode_token("invalid.token.string")

    def test_decode_token_wrong_secret(self):
        """Test decoding token with wrong secret."""
        handler1 = JWTHandler("secret1")
        handler2 = JWTHandler("secret2")

        token = handler1.encode_token("user123")

        with pytest.raises(JWTError, match="Invalid token"):
            handler2.decode_token(token)

    def test_decode_token_wrong_issuer(self):
        """Test decoding token with wrong issuer."""
        handler1 = JWTHandler("test-secret", "issuer1")
        handler2 = JWTHandler("test-secret", "issuer2")

        token = handler1.encode_token("user123")

        with pytest.raises(JWTError, match="Invalid token"):
            handler2.decode_token(token)

    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        handler = JWTHandler("test-secret")

        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = handler.encode_token("user123", expires_delta)

        with pytest.raises(JWTError, match="Invalid token"):
            handler.decode_token(token)

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        handler = JWTHandler("test-secret")

        token = handler.encode_token("user123")

        assert handler.verify_token(token) is True

    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        handler = JWTHandler("test-secret")

        assert handler.verify_token("invalid.token") is False

    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        handler = JWTHandler("test-secret")

        # Create expired token
        expires_delta = timedelta(seconds=-1)
        token = handler.encode_token("user123", expires_delta)

        assert handler.verify_token(token) is False

    def test_get_token_subject_valid(self):
        """Test extracting subject from valid token."""
        handler = JWTHandler("test-secret")

        token = handler.encode_token("user456")
        subject = handler.get_token_subject(token)

        assert subject == "user456"

    def test_get_token_subject_invalid(self):
        """Test extracting subject from invalid token."""
        handler = JWTHandler("test-secret")

        subject = handler.get_token_subject("invalid.token")

        assert subject is None

    def test_get_token_subject_expired(self):
        """Test extracting subject from expired token."""
        handler = JWTHandler("test-secret")

        # Create expired token
        expires_delta = timedelta(seconds=-1)
        token = handler.encode_token("user789", expires_delta)

        subject = handler.get_token_subject(token)

        assert subject is None
