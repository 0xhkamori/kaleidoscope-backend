from fastapi import APIRouter, HTTPException, Depends, Request
from firebase_admin import db
from datetime import datetime, timedelta
from typing import Optional
import uuid
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.models import UserCreate, UserLogin, TokenResponse, RefreshTokenRequest
from app.core.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, generate_session_id
from app.core.config import users_ref, sessions_ref, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/hour")
async def register(request: Request):
    from app.core.config import users_ref, profiles_ref

    if not users_ref or not profiles_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    # Parse JSON manually
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")

    # Extract and validate fields
    email = data.get('email')
    password = data.get('password')
    handle = data.get('handle')

    if not email or not password or not handle:
        raise HTTPException(status_code=400, detail="email, password, and handle are required")

    # Check if user exists
    existing_user = users_ref.order_by_child('email').equal_to(email).get()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if handle is taken
    existing_profile = profiles_ref.order_by_child('handle').equal_to(handle.lower()).get()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Handle already taken")

    # Validate handle format (alphanumeric, underscore, dash only)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', handle):
        raise HTTPException(status_code=400, detail="Handle can only contain letters, numbers, underscores, and dashes")

    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(password)
    user_data = {
        'userId': user_id,
        'email': email,
        'passwordHash': hashed_password,
        'createdAt': datetime.utcnow().isoformat()
    }
    users_ref.child(user_id).set(user_data)

    # Create profile
    display_name = email.split('@')[0]  # Use part before @ as display name
    profile_data = {
        'id': user_id,
        'userId': user_id,
        'handle': handle.lower(),
        'displayName': display_name,
        'bio': None,
        'avatarUrl': None,
        'avatarDeleteUrl': None,
        'createdAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    }
    profiles_ref.child(user_id).set(profile_data)

    # Create tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})

    # Create session
    session_id = generate_session_id()
    session_data = {
        'sessionId': session_id,
        'userId': user_id,
        'refreshToken': refresh_token,
        'userAgent': request.headers.get('user-agent'),
        'expiresAt': (datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    }
    sessions_ref.child(user_id).child(session_id).set(session_data)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request):
    from app.core.config import users_ref

    if not users_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    # Parse JSON manually
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")

    # Extract and validate fields
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password are required")

    # Find user
    users = users_ref.order_by_child('email').equal_to(email).get()
    if not users:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = list(users.keys())[0]
    user_data = users[user_id]

    # Verify password
    if not verify_password(password, user_data['passwordHash']):
        logger.warning(f"Failed login attempt for email: {email} from IP: {request.client.host if request.client else 'unknown'}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})

    # Create session
    session_id = generate_session_id()
    session_data = {
        'sessionId': session_id,
        'userId': user_id,
        'refreshToken': refresh_token,
        'userAgent': request.headers.get('user-agent'),
        'expiresAt': (datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    }
    sessions_ref.child(user_id).child(session_id).set(session_data)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/hour")
async def refresh_token(request: Request):
    from app.core.config import sessions_ref

    if not sessions_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    # Parse JSON manually
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")

    refresh_token_value = data.get('refresh_token')
    if not refresh_token_value:
        raise HTTPException(status_code=400, detail="refresh_token is required")

    # Decode refresh token
    payload = decode_token(refresh_token_value)
    if not payload or payload.get('type') != 'refresh':
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Find session
    sessions = sessions_ref.child(user_id).get()
    if not sessions:
        raise HTTPException(status_code=401, detail="Session not found")

    session_found = None
    for session_id, session_data in sessions.items():
        if session_data.get('refreshToken') == refresh_token_value:
            session_found = (session_id, session_data)
            break

    if not session_found:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    session_id, session_data = session_found

    # Check expiration
    expires_at = datetime.fromisoformat(session_data['expiresAt'])
    if datetime.utcnow() > expires_at:
        # Delete expired session
        sessions_ref.child(user_id).child(session_id).delete()
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Create new tokens
    new_access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})

    # Update session
    new_session_data = {
        'sessionId': session_id,
        'userId': user_id,
        'refreshToken': new_refresh_token,
        'userAgent': request.headers.get('user-agent'),
        'expiresAt': (datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    }
    sessions_ref.child(user_id).child(session_id).set(new_session_data)

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)

@router.post("/logout")
async def logout(request: Request):
    from app.core.config import sessions_ref

    if not sessions_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    # Parse JSON manually
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")

    refresh_token_value = data.get('refresh_token')
    if not refresh_token_value:
        raise HTTPException(status_code=400, detail="refresh_token is required")

    # Decode refresh token
    payload = decode_token(refresh_token_value)
    if not payload or payload.get('type') != 'refresh':
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Find and delete session
    sessions = sessions_ref.child(user_id).get()
    if sessions:
        for session_id, session_data in sessions.items():
            if session_data.get('refreshToken') == refresh_token_value:
                sessions_ref.child(user_id).child(session_id).delete()
                return {"message": "Logged out successfully"}

    raise HTTPException(status_code=401, detail="Session not found")