import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash


load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

NORMAL_TOKEN_MINUTES = 30
REMEMBER_TOKEN_DAYS = 7


if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is missing from the .env file."
    )


password_manager = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Convert a normal password into a secure hash.
    """

    return password_manager.hash(password)


def verify_password(
    plain_password: str,
    stored_password_hash: str,
) -> bool:
    """
    Check whether the entered password matches
    the stored password hash.
    """

    try:
        return password_manager.verify(
            plain_password,
            stored_password_hash,
        )
    except Exception:
        return False


def create_access_token(
    user_id: int,
    remember_me: bool = False,
) -> str:
    """
    Create a signed JWT containing the user ID.
    """

    current_time = datetime.now(timezone.utc)

    if remember_me:
        expiration_time = (
            current_time
            + timedelta(days=REMEMBER_TOKEN_DAYS)
        )
    else:
        expiration_time = (
            current_time
            + timedelta(
                minutes=NORMAL_TOKEN_MINUTES
            )
        )

    payload = {
        "sub": str(user_id),
        "iat": current_time,
        "exp": expiration_time,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> int | None:
    """
    Validate a JWT and return its user ID.
    """

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return int(user_id)

    except (
        InvalidTokenError,
        TypeError,
        ValueError,
    ):
        return None