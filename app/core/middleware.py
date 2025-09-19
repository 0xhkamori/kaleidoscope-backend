from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.auth import decode_token
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and validate JWT token from Authorization header"""
    if not credentials or not credentials.credentials:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Missing authorization header from IP: {client_ip}")
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get('type') != 'access':
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Invalid or expired token from IP: {client_ip}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get('sub')
    if not user_id:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Invalid token payload from IP: {client_ip}")
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id