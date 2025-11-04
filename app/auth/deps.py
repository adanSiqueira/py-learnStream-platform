from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql.user import User
from app.services.security import decode_token
from app.models.sql.database import get_db
from app.services import user_ops
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = '/auth/login')

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Retrieve the current authenticated user based on the JWT access token.

    Steps:
    1. Extract and decode the JWT from the Authorization header.
    2. Validate the token and ensure it has not expired.
    3. Fetch the corresponding user from the database.

    Args:
        token (str): The access token obtained from the client.
        db (AsyncSession): Active SQLAlchemy async session.

    Returns:
        User: The user associated with the provided token.
    """
    try:
        payload = decode_token(token)
        user_id = int(payload['sub'])

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = await user_ops.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user

def require_role(roles: list[str]):
    """
    Dependency factory that enforces role-based access control (RBAC) on routes.

    This higher-order function returns a dependency that ensures the current user
    possesses one of the allowed roles. It can be used in route definitions via
    FastAPI's `Depends` mechanism.

    Example:
        ```python
        @router.post("/admin-task")
        async def admin_action(user = Depends(require_role(["admin"]))):
            ...
        ```

    Args:
        roles (list[str]): List of permitted role names (e.g., ["admin", "manager"]).

    Returns:
        Callable: A FastAPI dependency that validates the user's role.

    Raises:
        HTTPException: 403 if the user does not have sufficient privileges.
    """
    async def inner(user = Depends(get_current_user)):
        if user.role.value not in roles:  
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient privileges")
        return user
    return inner