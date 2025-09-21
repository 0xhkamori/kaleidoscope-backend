import logging
from fastapi import FastAPI, Depends, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.api.routes import router as auth_router
from app.api.profiles import router as profile_router
from app.platforms.soundcloud import search_soundcloud, get_soundcloud_stream_url, get_soundcloud_track_details, format_soundcloud_track
from app.platforms.youtube import search_youtube, get_stream_url, get_youtube_track_details
from app.platforms.spotify import search_spotify, get_spotify_stream_url, get_spotify_track_details
from app.core.middleware import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting Kaleidoscope Backend API...")

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Configure FastAPI with rate limiting
app = FastAPI()
app.state.limiter = limiter

# Custom rate limit exceeded handler with logging
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(f"Rate limit exceeded for IP: {client_ip}, Path: {request.url.path}")
    return _rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# Add global rate limiting (100 requests per minute per IP)
@app.middleware("http")
async def add_global_rate_limit(request: Request, call_next):
    # Global rate limit is applied via SlowAPIMiddleware with default_limits
    response = await call_next(request)
    return response

# Add secure HTTP headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'"

    # Remove server header for security
    response.headers.pop("server", None)

    return response

logger.info("Including routers...")
# Include auth routes with stricter rate limits
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Include profile routes
app.include_router(profile_router, tags=["profiles"])

logger.info("API startup complete!")

@app.get("/")
def read_root():
    return {"kaleidoscope-api": "v0.1.0"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.post("/search/{platform}")
def search(platform: str, query: str, limit: int = 20, user_id: str = Depends(get_current_user)):
    if platform == "soundcloud":
        results = search_soundcloud(query, limit)
    elif platform == "youtube":
        results = search_youtube(query, limit)
    elif platform == "spotify":
        results = search_spotify(query, limit)
    else:
        return {"error": "Unsupported platform"}
    return {"results": results}

@app.get("/track/{platform}/{track_id}")
def get_track(platform: str, track_id: str, user_id: str = Depends(get_current_user)):
    if platform == "soundcloud":
        details = get_soundcloud_track_details(track_id)
        if details:
            formatted = format_soundcloud_track(details)
            return formatted
    elif platform == "youtube":
        details = get_youtube_track_details(track_id)
        if details:
            return details
    elif platform == "spotify":
        details = get_spotify_track_details(track_id)
        if details:
            return details
    return {"error": "Track not found"}

@app.get("/track/{platform}/{track_id}/stream")
def get_stream(platform: str, track_id: str, user_id: str = Depends(get_current_user)):
    if platform == "soundcloud":
        stream = get_soundcloud_stream_url(track_id)
    elif platform == "youtube":
        stream = get_stream_url(track_id)
    elif platform == "spotify":
        stream = get_spotify_stream_url(track_id)
    else:
        return {"error": "Unsupported platform"}
    if stream:
        return stream
    return {"error": "Stream not available"}