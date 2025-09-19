# Kaleidoscope Backend API

A comprehensive FastAPI backend with music streaming integration, user authentication, and profile management.

## Features

- 🔐 **JWT Authentication** with Access/Refresh tokens
- 🎵 **Multi-platform Music Streaming** (SoundCloud, YouTube, Spotify)
- 👤 **User Profiles** with avatar hosting via ImgBB
- 🔥 **Firebase Realtime Database** for data persistence

## Setup

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the project root:

```env
# SoundCloud API
SOUNDCLOUD_CLIENT_ID=your_soundcloud_client_id

# Spotify API (optional)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# JWT Secret
JWT_SECRET_KEY=your_secure_random_jwt_secret

# ImgBB for avatar hosting
IMGBB_API_KEY=your_imgbb_api_key
```

### 3. Firebase Setup
1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Realtime Database
3. Generate service account credentials (download JSON)
4. Place the JSON file at `app/core/firebase_credentials.json`
5. Update Firebase Database rules:

```json
{
  "rules": {
    ".read": "auth != null",
    ".write": "auth != null",
    "users": {
      ".indexOn": ["email"]
    },
    "sessions": {
      ".indexOn": ["userId"]
    },
    "profiles": {
      ".indexOn": ["handle", "userId", "displayName"]
    },
    "tags": {
      ".indexOn": ["profileId"]
    }
  }
}
```

### 4. Run the Application
```bash
uvicorn main:app --reload
```

Visit:
- API: http://127.0.0.1:8000
- Documentation: http://127.0.0.1:8000/docs

## Authentication

The API uses JWT tokens for authentication. All music and profile endpoints require authentication.

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "handle": "unique_handle"
}
```

**Handle Requirements:**
- Must be unique across all users
- Can only contain letters, numbers, underscores, and dashes
- Case-insensitive (stored in lowercase)

### Login User
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "your_refresh_token_here"
}
```

### Logout User
```http
POST /auth/logout
Content-Type: application/json

{
  "refresh_token": "your_refresh_token_here"
}
```

## Music API

**🔐 All music endpoints require authentication.** Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

**Non-authenticated users cannot access any music data.** All search, track details, and streaming endpoints require valid JWT tokens.

**Unauthenticated requests return:**
```json
{
  "detail": "Missing or invalid authorization header"
}
```

### Search Tracks
```http
POST /search/{platform}?query={query}&limit={limit}
```

**Platforms:** `soundcloud`, `youtube`, `spotify`

**Example:**
```http
POST /search/soundcloud?query=rihanna&limit=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "results": [
    {
      "id": "track_id",
      "title": "Track Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "duration": 180,
      "durationString": "3:00",
      "coverArt": "https://...",
      "source": "soundcloud"
    }
  ]
}
```

### Get Track Details
```http
GET /track/{platform}/{track_id}
```

**Response:**
```json
{
  "id": "track_id",
  "title": "Track Title",
  "artist": "Artist Name",
  "album": "Album Name",
  "duration": 180,
  "durationString": "3:00",
  "coverArt": "https://...",
  "source": "soundcloud"
}
```

### Get Stream URL
```http
GET /track/{platform}/{track_id}/stream
```

**Response:**
```json
{
  "url": "https://stream.url",
  "type": "audio/mpeg",
  "source": "soundcloud"
}
```

**Note:** For Spotify, streams are sourced from SoundCloud or YouTube when available, otherwise returns Spotify preview URL.

## Profile API

### Get Public Profile
```http
GET /profiles/{identifier}
```

**Identifier Types:** Can be user ID, handle, or display name. The endpoint tries to match in this order: ID → handle → display name.

**Examples:**
- `GET /profiles/f1b2c3d4-...` (by user ID)
- `GET /profiles/johndoe` (by handle)
- `GET /profiles/John%20Doe` (by display name)

**Response:**
```json
{
  "handle": "example_user",
  "displayName": "Example User",
  "bio": "Software developer creating amazing things.",
  "avatarUrl": "https://i.ibb.co/98W13PY/c1f64245afb2.gif",
  "tags": []
}
```

### Get/Update My Profile
```http
GET /profile/me
PUT /profile/me
```

**GET Response:**
```json
{
  "id": "user_uuid",
  "userId": "user_uuid",
  "handle": "my_handle",
  "displayName": "My Name",
  "bio": "About me...",
  "avatarUrl": "https://i.ibb.co/...",
  "avatarDeleteUrl": "https://ibb.co/delete/...",
  "createdAt": "2024-01-01T00:00:00",
  "updatedAt": "2024-01-01T00:00:00",
  "tags": []
}
```

**PUT Request Body:**
```json
{
  "handle": "new_handle",
  "displayName": "My New Name",
  "bio": "Updated biography."
}
```

### Avatar Management
```http
POST /profile/me/avatar
DELETE /profile/me/avatar
```

**POST Request:** JSON with base64 encoded image
```json
{
  "imageBase64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

**Response:**
```json
{
  "id": "user_uuid",
  "userId": "user_uuid",
  "handle": "my_handle",
  "displayName": "My Name",
  "avatarUrl": "https://i.ibb.co/98W13PY/avatar.jpg",
  "avatarDeleteUrl": "https://ibb.co/delete/...",
  "tags": []
}
```

**Notes:**
- Accepts base64 data URL format (`data:image/png;base64,...`) or raw base64
- Image is uploaded directly to ImgBB without local storage
- Only the direct link URL is saved in the database


## Default Profile on Registration

When a user registers, a profile is automatically created with:

```json
{
  "id": "user_uuid",
  "userId": "user_uuid",
  "handle": "provided_handle",  // Required during registration
  "displayName": "username",     // Part of email before @
  "bio": null,
  "avatarUrl": null,
  "avatarDeleteUrl": null,
  "createdAt": "timestamp",
  "updatedAt": "timestamp",
  "tags": []
}
```

**Note:** Tags are managed externally and cannot be modified by users.

## Project Structure

```
kaleidoscope-backend/
├── app/
│   ├── api/
│   │   ├── routes.py      # Auth endpoints
│   │   └── profiles.py    # Profile endpoints
│   ├── core/
│   │   ├── auth.py        # JWT utilities
│   │   ├── config.py      # Firebase & app config
│   │   ├── middleware.py  # Auth middleware
│   │   ├── models.py      # Pydantic models
│   │   └── firebase_credentials.json
│   └── platforms/
│       ├── soundcloud.py  # SoundCloud integration
│       ├── youtube.py     # YouTube integration
│       └── spotify.py     # Spotify integration
├── docs/                  # Documentation
├── tests/                 # Test files
├── main.py               # FastAPI app entry point
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## API Keys & Credentials

### Required API Keys:
- **SoundCloud Client ID**: Get from SoundCloud web app network inspection
- **ImgBB API Key**: Get from [ImgBB](https://imgbb.com/)
- **Spotify** (optional): Get from [Spotify Developer Dashboard](https://developer.spotify.com/)
- **JWT Secret**: Generate secure random string

### Firebase:
- Service account JSON file
- Realtime Database URL
- Proper security rules

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### API Documentation
- Interactive Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`