# 🔴 Error Dictionary - Kaleidoscope Backend API

Comprehensive catalog of all possible error scenarios for each API endpoint.

---

## **Authentication Endpoints**

### **Endpoint**: `POST /auth/register`

#### 1. Rate Limit Exceeded
- **HTTP Status**: `429 Too Many Requests`
- **Reason**: User exceeded registration rate limit (5 per hour per IP)
- **Response**:
```json
{
  "detail": "Rate limit exceeded"
}
```

#### 2. Invalid JSON Format
- **HTTP Status**: `400 Bad Request`
- **Reason**: Request body is not valid JSON or missing required fields
- **Response**:
```json
{
  "detail": "Invalid JSON in request body"
}
```

#### 3. Missing Required Fields
- **HTTP Status**: `400 Bad Request`
- **Reason**: email, password, or handle field is missing
- **Response**:
```json
{
  "detail": "email, password, and handle are required"
}
```

#### 4. Invalid Handle Format
- **HTTP Status**: `400 Bad Request`
- **Reason**: Handle contains invalid characters (only letters, numbers, underscores, dashes allowed)
- **Response**:
```json
{
  "detail": "Handle can only contain letters, numbers, underscores, and dashes"
}
```

#### 5. Email Already Registered
- **HTTP Status**: `400 Bad Request`
- **Reason**: Email address is already associated with an existing account
- **Response**:
```json
{
  "detail": "Email already registered"
}
```

#### 6. Handle Already Taken
- **HTTP Status**: `400 Bad Request`
- **Reason**: Handle is already in use by another user
- **Response**:
```json
{
  "detail": "Handle already taken"
}
```

#### 7. Database Unavailable
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Firebase database connection failed
- **Response**:
```json
{
  "detail": "Database not available"
}
```

---

### **Endpoint**: `POST /auth/login`

#### 1. Rate Limit Exceeded
- **HTTP Status**: `429 Too Many Requests`
- **Reason**: User exceeded login rate limit (5 per minute per IP)
- **Response**:
```json
{
  "detail": "Rate limit exceeded"
}
```

#### 2. Invalid JSON Format
- **HTTP Status**: `400 Bad Request`
- **Reason**: Request body is not valid JSON
- **Response**:
```json
{
  "detail": "Invalid JSON in request body"
}
```

#### 3. Missing Required Fields
- **HTTP Status**: `400 Bad Request`
- **Reason**: email or password field is missing
- **Response**:
```json
{
  "detail": "email and password are required"
}
```

#### 4. Invalid Credentials
- **HTTP Status**: `401 Unauthorized`
- **Reason**: Email/password combination is incorrect
- **Response**:
```json
{
  "detail": "Invalid credentials"
}
```

#### 5. Database Unavailable
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Firebase database connection failed
- **Response**:
```json
{
  "detail": "Database not available"
}
```

---

### **Endpoint**: `POST /auth/refresh`

#### 1. Rate Limit Exceeded
- **HTTP Status**: `429 Too Many Requests`
- **Reason**: User exceeded refresh token rate limit (20 per hour per IP)
- **Response**:
```json
{
  "detail": "Rate limit exceeded"
}
```

#### 2. Invalid JSON Format
- **HTTP Status**: `400 Bad Request`
- **Reason**: Request body is not valid JSON
- **Response**:
```json
{
  "detail": "Invalid JSON in request body"
}
```

#### 3. Missing Refresh Token
- **HTTP Status**: `400 Bad Request`
- **Reason**: refresh_token field is missing from request body
- **Response**:
```json
{
  "detail": "refresh_token is required"
}
```

#### 4. Invalid Refresh Token
- **HTTP Status**: `401 Unauthorized`
- **Reason**: Token is malformed, expired, or not a refresh token
- **Response**:
```json
{
  "detail": "Invalid refresh token"
}
```

#### 5. Session Not Found
- **HTTP Status**: `401 Unauthorized`
- **Reason**: Refresh token doesn't match any active session
- **Response**:
```json
{
  "detail": "Session not found"
}
```

#### 6. Refresh Token Expired
- **HTTP Status**: `401 Unauthorized`
- **Reason**: Refresh token has exceeded its expiration time
- **Response**:
```json
{
  "detail": "Refresh token expired"
}
```

#### 7. Database Unavailable
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Firebase database connection failed
- **Response**:
```json
{
  "detail": "Database not available"
}
```

---

### **Endpoint**: `POST /auth/logout`

#### 1. Invalid JSON Format
- **HTTP Status**: `400 Bad Request`
- **Reason**: Request body is not valid JSON
- **Response**:
```json
{
  "detail": "Invalid JSON in request body"
}
```

#### 2. Missing Refresh Token
- **HTTP Status**: `400 Bad Request`
- **Reason**: refresh_token field is missing from request body
- **Response**:
```json
{
  "detail": "refresh_token is required"
}
```

#### 3. Invalid Refresh Token
- **HTTP Status**: `401 Unauthorized`
- **Reason**: Token is malformed or not a refresh token
- **Response**:
```json
{
  "detail": "Invalid refresh token"
}
```

#### 4. Session Not Found
- **HTTP Status**: `401 Unauthorized`
- **Reason**: Refresh token doesn't match any active session
- **Response**:
```json
{
  "detail": "Session not found"
}
```

#### 5. Database Unavailable
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Firebase database connection failed
- **Response**:
```json
{
  "detail": "Database not available"
}
```

---

## **Profile Endpoints**

### **Endpoint**: `GET /profiles/{identifier}`

#### 1. Profile Not Found
- **HTTP Status**: `404 Not Found`
- **Reason**: No profile matches the provided identifier (ID, handle, or display name)
- **Response**:
```json
{
  "detail": "Profile not found"
}
```

#### 2. Database Unavailable
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Firebase database connection failed
- **Response**:
```json
{
  "detail": "Database not available"
}
```

---

### **Endpoint**: `GET /profile/me`

#### 1. Missing Authorization
- **HTTP Status**: `401 Unauthorized`
- **Reason**: No valid JWT token provided in Authorization header
- **Response**:
```json
{
  "detail": "Missing or invalid authorization header"
}
```

#### 2. Invalid Token
- **HTTP Status**: `401 Unauthorized`
- **Reason**: JWT token is expired, malformed, or invalid
- **Response**:
```json
{
  "detail": "Invalid or expired token"
}
```

#### 3. Profile Not Found
- **HTTP Status**: `404 Not Found`
- **Reason**: User's profile data is missing from database
- **Response**:
```json
{
  "detail": "Profile not found"
}
```

#### 4. Database Unavailable
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Firebase database connection failed
- **Response**:
```json
{
  "detail": "Database not available"
}
```

---

### **Endpoint**: `PUT /profile/me`

#### 1. Missing Authorization
- **HTTP Status**: `401 Unauthorized`
- **Reason**: No valid JWT token provided in Authorization header
- **Response**:
```json
{
  "detail": "Missing or invalid authorization header"
}
```

#### 2. Invalid Token
- **HTTP Status**: `401 Unauthorized`
- **Reason**: JWT token is expired, malformed, or invalid
- **Response**:
```json
{
  "detail": "Invalid or expired token"
}
```

#### 3. Invalid JSON Format
- **HTTP Status**: `400 Bad Request`
- **Reason**: Request body contains invalid JSON or trailing commas
- **Response**:
```json
{
  "detail": "Invalid JSON: Illegal trailing comma before end of object: line 4 column 14 (char 74). Make sure there are no trailing commas."
}
```

#### 4. Handle Already Taken
- **HTTP Status**: `400 Bad Request`
- **Reason**: The requested handle is already in use by another user
- **Response**:
```json
{
  "detail": "Handle already taken"
}
```

#### 5. Database Unavailable
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Firebase database connection failed
- **Response**:
```json
{
  "detail": "Database not available"
}
```

---

### **Endpoint**: `POST /profile/me/avatar`

#### 1. Missing Authorization
- **HTTP Status**: `401 Unauthorized`
- **Reason**: No valid JWT token provided in Authorization header
- **Response**:
```json
{
  "detail": "Missing or invalid authorization header"
}
```

#### 2. Invalid Token
- **HTTP Status**: `401 Unauthorized`
- **Reason**: JWT token is expired, malformed, or invalid
- **Response**:
```json
{
  "detail": "Invalid or expired token"
}
```

#### 3. Invalid JSON Format
- **HTTP Status**: `400 Bad Request`
- **Reason**: Request body is not valid JSON
- **Response**:
```json
{
  "error": "Invalid request. Content-Type: text/plain, Body: {...}, Error: ..."
}
```

#### 4. Missing Image Data
- **HTTP Status**: `400 Bad Request`
- **Reason**: imageBase64 field is missing from request body
- **Response**:
```json
{
  "detail": "imageBase64 field required"
}
```

#### 5. Invalid Base64 Data
- **HTTP Status**: `400 Bad Request`
- **Reason**: Provided image data is not valid base64 or corrupted
- **Response**:
```json
{
  "detail": "Invalid base64 image data: [error details]"
}
```

#### 6. ImgBB API Key Missing
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: IMGBB_API_KEY environment variable is not configured
- **Response**:
```json
{
  "detail": "ImgBB API key not configured"
}
```

#### 7. ImgBB Upload Failed
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Failed to upload image to ImgBB service
- **Response**:
```json
{
  "detail": "Failed to upload image: [error details]"
}
```

#### 8. Profile Not Found
- **HTTP Status**: `404 Not Found`
- **Reason**: User's profile data is missing from database
- **Response**:
```json
{
  "detail": "Profile not found"
}
```

#### 9. Database Unavailable
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Firebase database connection failed
- **Response**:
```json
{
  "detail": "Database not available"
}
```

---

### **Endpoint**: `DELETE /profile/me/avatar`

#### 1. Missing Authorization
- **HTTP Status**: `401 Unauthorized`
- **Reason**: No valid JWT token provided in Authorization header
- **Response**:
```json
{
  "detail": "Missing or invalid authorization header"
}
```

#### 2. Invalid Token
- **HTTP Status**: `401 Unauthorized`
- **Reason**: JWT token is expired, malformed, or invalid
- **Response**:
```json
{
  "detail": "Invalid or expired token"
}
```

#### 3. Profile Not Found
- **HTTP Status**: `404 Not Found`
- **Reason**: User's profile data is missing from database
- **Response**:
```json
{
  "detail": "Profile not found"
}
```

#### 4. Database Unavailable
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Firebase database connection failed
- **Response**:
```json
{
  "detail": "Database not available"
}
```

---

## **Music API Endpoints**

### **Endpoint**: `POST /search/{platform}`

#### 1. Rate Limit Exceeded
- **HTTP Status**: `429 Too Many Requests`
- **Reason**: User exceeded global rate limit (100 requests per minute per IP)
- **Response**:
```json
{
  "detail": "Rate limit exceeded"
}
```

#### 2. Missing Authorization
- **HTTP Status**: `401 Unauthorized`
- **Reason**: No valid JWT token provided in Authorization header
- **Response**:
```json
{
  "detail": "Missing or invalid authorization header"
}
```

#### 3. Invalid Token
- **HTTP Status**: `401 Unauthorized`
- **Reason**: JWT token is expired, malformed, or invalid
- **Response**:
```json
{
  "detail": "Invalid or expired token"
}
```

#### 4. Unsupported Platform
- **HTTP Status**: `200 OK`
- **Reason**: Platform parameter is not 'soundcloud', 'youtube', or 'spotify'
- **Response**:
```json
{
  "error": "Unsupported platform"
}
```

#### 5. SoundCloud Client ID Missing
- **HTTP Status**: `200 OK`
- **Reason**: SOUNDCLOUD_CLIENT_ID environment variable not configured
- **Response**:
```json
{
  "results": []
}
```

#### 6. YouTube Music API Error
- **HTTP Status**: `200 OK`
- **Reason**: YTMusic client failed to initialize or search failed
- **Response**:
```json
{
  "results": []
}
```

#### 7. Spotify API Error
- **HTTP Status**: `200 OK`
- **Reason**: Spotify API client not configured or search failed
- **Response**:
```json
{
  "results": []
}
```

---

### **Endpoint**: `GET /track/{platform}/{track_id}`

#### 1. Rate Limit Exceeded
- **HTTP Status**: `429 Too Many Requests`
- **Reason**: User exceeded global rate limit (100 requests per minute per IP)
- **Response**:
```json
{
  "detail": "Rate limit exceeded"
}
```

#### 2. Missing Authorization
- **HTTP Status**: `401 Unauthorized`
- **Reason**: No valid JWT token provided in Authorization header
- **Response**:
```json
{
  "detail": "Missing or invalid authorization header"
}
```

#### 3. Invalid Token
- **HTTP Status**: `401 Unauthorized`
- **Reason**: JWT token is expired, malformed, or invalid
- **Response**:
```json
{
  "detail": "Invalid or expired token"
}
```

#### 4. Unsupported Platform
- **HTTP Status**: `200 OK`
- **Reason**: Platform parameter is not 'soundcloud', 'youtube', or 'spotify'
- **Response**:
```json
{
  "error": "Track not found"
}
```

#### 5. Track Not Found
- **HTTP Status**: `200 OK`
- **Reason**: Track ID doesn't exist or API returned no results
- **Response**:
```json
{
  "error": "Track not found"
}
```

#### 6. SoundCloud API Error
- **HTTP Status**: `200 OK`
- **Reason**: Failed to fetch track details from SoundCloud API
- **Response**:
```json
{
  "error": "Track not found"
}
```

#### 7. YouTube API Error
- **HTTP Status**: `200 OK`
- **Reason**: Failed to fetch track details from YouTube/YTMusic API
- **Response**:
```json
{
  "error": "Track not found"
}
```

#### 8. Spotify API Error
- **HTTP Status**: `200 OK`
- **Reason**: Failed to fetch track details from Spotify API
- **Response**:
```json
{
  "error": "Track not found"
}
```

---

### **Endpoint**: `GET /track/{platform}/{track_id}/stream`

#### 1. Rate Limit Exceeded
- **HTTP Status**: `429 Too Many Requests`
- **Reason**: User exceeded global rate limit (100 requests per minute per IP)
- **Response**:
```json
{
  "detail": "Rate limit exceeded"
}
```

#### 2. Missing Authorization
- **HTTP Status**: `401 Unauthorized`
- **Reason**: No valid JWT token provided in Authorization header
- **Response**:
```json
{
  "detail": "Missing or invalid authorization header"
}
```

#### 3. Invalid Token
- **HTTP Status**: `401 Unauthorized`
- **Reason**: JWT token is expired, malformed, or invalid
- **Response**:
```json
{
  "detail": "Invalid or expired token"
}
```

#### 4. Unsupported Platform
- **HTTP Status**: `200 OK`
- **Reason**: Platform parameter is not 'soundcloud', 'youtube', or 'spotify'
- **Response**:
```json
{
  "error": "Stream not available"
}
```

#### 5. Stream Not Available
- **HTTP Status**: `200 OK`
- **Reason**: Track exists but no stream URL could be obtained
- **Response**:
```json
{
  "error": "Stream not available"
}
```

#### 6. SoundCloud Stream Error
- **HTTP Status**: `200 OK`
- **Reason**: Failed to get stream URL from SoundCloud API
- **Response**:
```json
{
  "error": "Stream not available"
}
```

#### 7. YouTube Stream Error
- **HTTP Status**: `200 OK`
- **Reason**: Failed to get stream URL from YouTube/yt-dlp
- **Response**:
```json
{
  "error": "Stream not available"
}
```

#### 8. Spotify Stream Error
- **HTTP Status**: `200 OK`
- **Reason**: Failed to get stream URL from Spotify API
- **Response**:
```json
{
  "error": "Stream not available"
}
```

---

## **Global Error Scenarios**

### **Rate Limiting (All Endpoints)**
- **HTTP Status**: `429 Too Many Requests`
- **Reason**: Request frequency exceeded configured limits
- **Response**:
```json
{
  "detail": "Rate limit exceeded"
}
```

### **Server Errors (All Endpoints)**
- **HTTP Status**: `500 Internal Server Error`
- **Reason**: Unexpected server error, database failures, or service unavailability
- **Response**:
```json
{
  "detail": "Internal server error"
}
```

### **Service Unavailable (All Endpoints)**
- **HTTP Status**: `503 Service Unavailable`
- **Reason**: External services (Firebase, ImgBB, APIs) are temporarily unavailable
- **Response**:
```json
{
  "detail": "Service temporarily unavailable"
}
```

---

## **Error Response Patterns**

### **Authentication Errors**
- Always return `401 Unauthorized` for auth failures
- Include specific reason in `detail` field
- Log security events with IP addresses

### **Validation Errors**
- Return `400 Bad Request` for invalid input
- Include specific validation failure reason
- Preserve user input in error messages when safe

### **Resource Errors**
- Return `404 Not Found` for missing resources
- Generic messages to avoid information leakage
- Different codes for auth (401) vs not found (404)

### **Rate Limiting**
- Return `429 Too Many Requests` for all rate limit violations
- Include retry information in headers when possible
- Log violations for monitoring

### **Server Errors**
- Return `500 Internal Server Error` for unexpected failures
- Generic messages to prevent information disclosure
- Detailed logging for debugging

---

## **Testing Recommendations**

### **Authentication Testing**
- Test with missing/invalid/malformed tokens
- Test with expired tokens
- Test rate limiting on auth endpoints

### **Input Validation Testing**
- Test with malformed JSON (trailing commas, invalid syntax)
- Test with missing required fields
- Test with invalid data types and formats

### **Business Logic Testing**
- Test duplicate email/handle registration
- Test profile updates with conflicts
- Test avatar upload with invalid files

### **External Service Testing**
- Test with network failures to external APIs
- Test with invalid API keys
- Test with service rate limits

### **Security Testing**
- Test for IDOR vulnerabilities
- Test for injection attacks
- Test rate limiting effectiveness

---

*This document is automatically generated and should be updated whenever new endpoints or error conditions are added to the API.*