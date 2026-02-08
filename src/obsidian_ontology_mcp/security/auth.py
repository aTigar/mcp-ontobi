"""JWT authentication and password management."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from ..config import settings

logger = logging.getLogger(__name__)


class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""

    username: Optional[str] = None


class AuthManager:
    """Manages authentication with JWT tokens and bcrypt passwords."""

    def __init__(self) -> None:
        """Initialize authentication manager."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.logger = logging.getLogger(__name__)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Bcrypt hash

        Returns:
            True if password matches
        """
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False

    def hash_password(self, password: str) -> str:
        """
        Hash a password with bcrypt.

        Args:
            password: Plain text password

        Returns:
            Bcrypt hash
        """
        return self.pwd_context.hash(password)

    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate a user.

        Args:
            username: Username
            password: Plain text password

        Returns:
            True if authentication successful
        """
        # Check username
        if username != settings.security.admin_username:
            return False

        # Verify password
        return self.verify_password(password, settings.security.admin_password_hash)

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Data to encode in token
            expires_delta: Token expiration time

        Returns:
            JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.security.jwt_access_token_expire_minutes
            )

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode,
            settings.security.jwt_secret_key,
            algorithm=settings.security.jwt_algorithm,
        )

        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenData or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.security.jwt_secret_key,
                algorithms=[settings.security.jwt_algorithm],
            )

            username: str = payload.get("sub")
            if username is None:
                return None

            return TokenData(username=username)

        except JWTError as e:
            self.logger.warning(f"JWT verification failed: {e}")
            return None

    def create_token_for_user(self, username: str) -> Token:
        """
        Create a token for authenticated user.

        Args:
            username: Username

        Returns:
            Token object
        """
        access_token = self.create_access_token(data={"sub": username})

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.security.jwt_access_token_expire_minutes * 60,
        )
