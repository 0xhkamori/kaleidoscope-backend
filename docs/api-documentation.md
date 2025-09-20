# Kaleidoscope Backend API Documentation

This documentation is tailored for frontend developers to understand how to interact with the API endpoints, including request formats and expected responses.

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