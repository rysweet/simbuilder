"""
JWT token handling for SimBuilder API authentication.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

from jose import JWTError
from jose import jwt
from pydantic import BaseModel


class TokenData(BaseModel):
    """Token payload data model."""

    sub: str  # Subject (user ID)
    exp: int  # Expiration timestamp
    iss: str  # Issuer
    iat: int  # Issued at timestamp


class JWTHandler:
    """JWT token encoder/decoder with HS256 algorithm."""

    def __init__(self, secret: str, issuer: str = "simbuilder") -> None:
        """Initialize JWT handler.

        Args:
            secret: Secret key for signing tokens
            issuer: Token issuer identifier
        """
        self.secret = secret
        self.issuer = issuer
        self.algorithm = "HS256"

    def encode_token(
        self,
        subject: str,
        expires_delta: timedelta | None = None
    ) -> str:
        """Encode a JWT token.

        Args:
            subject: Token subject (user ID)
            expires_delta: Token expiration time delta (default: 1 hour)

        Returns:
            Encoded JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=1)

        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "sub": subject,
            "iss": self.issuer,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        }

        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_token(self, token: str) -> TokenData:
        """Decode and validate a JWT token.

        Args:
            token: JWT token string to decode

        Returns:
            Decoded token data

        Raises:
            JWTError: If token is invalid, expired, or malformed
        """
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                issuer=self.issuer
            )
            return TokenData(**payload)
        except JWTError as e:
            raise JWTError(f"Invalid token: {str(e)}") from e

    def verify_token(self, token: str) -> bool:
        """Verify if a token is valid.

        Args:
            token: JWT token string to verify

        Returns:
            True if token is valid, False otherwise
        """
        try:
            self.decode_token(token)
            return True
        except JWTError:
            return False

    def get_token_subject(self, token: str) -> str | None:
        """Extract subject from token without validation.

        Args:
            token: JWT token string

        Returns:
            Token subject if extractable, None otherwise
        """
        try:
            token_data = self.decode_token(token)
            return token_data.sub
        except JWTError:
            return None
