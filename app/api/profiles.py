from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from firebase_admin import db
from datetime import datetime
import uuid
import requests
import os
import base64
import json
import re
import html

from app.core.models import ProfileUpdate, TagCreate, Tag, Profile, ProfilePublic, AvatarUpload
from app.core.middleware import get_current_user
from app.core.config import profiles_ref, tags_ref

router = APIRouter()

def sanitize_text(text: str) -> str:
    """Sanitize text input to prevent XSS attacks."""
    if not text:
        return text
    # Escape HTML entities
    text = html.escape(text)
    # Remove potentially dangerous tags/attributes that might have been missed
    text = re.sub(r'<[^>]*>', '', text)  # Remove any remaining HTML tags
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)  # Remove javascript: URLs
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)  # Remove event handlers
    return text.strip()

@router.get("/profiles/{identifier}", response_model=ProfilePublic)
def get_public_profile(identifier: str):
    """Get public profile by id, handle, or displayName"""
    from app.core.config import profiles_ref, tags_ref

    if not profiles_ref or not tags_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    profile_data = None
    profile_id = None

    # Try to find by id first (exact match)
    if profiles_ref.child(identifier).get():
        profile_data = profiles_ref.child(identifier).get()
        profile_id = identifier
    else:
        # Try to find by handle (case insensitive)
        profiles = profiles_ref.order_by_child('handle').equal_to(identifier.lower()).get()
        if profiles:
            profile_id = list(profiles.keys())[0]
            profile_data = profiles[profile_id]
        else:
            # Try to find by displayName (case insensitive)
            profiles = profiles_ref.order_by_child('displayName').equal_to(identifier).get()
            if profiles:
                profile_id = list(profiles.keys())[0]
                profile_data = profiles[profile_id]

    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get tags for this profile
    tags_data = tags_ref.order_by_child('profileId').equal_to(profile_id).get()
    tags = []
    if tags_data:
        for tag_id, tag_info in tags_data.items():
            tags.append(Tag(
                id=tag_id,
                profileId=tag_info['profileId'],
                text=tag_info['text'],
                iconName=tag_info.get('iconName'),
                color=tag_info.get('color')
            ))

    return ProfilePublic(
        handle=profile_data['handle'],
        displayName=profile_data['displayName'],
        bio=profile_data.get('bio'),
        avatarUrl=profile_data.get('avatarUrl'),
        tags=tags
    )

@router.get("/profile/me", response_model=Profile)
def get_my_profile(user_id: str = Depends(get_current_user)):
    """Get current user's profile"""
    from app.core.config import profiles_ref, tags_ref

    if not profiles_ref or not tags_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    profile_data = profiles_ref.child(user_id).get()
    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get tags
    tags_data = tags_ref.order_by_child('profileId').equal_to(user_id).get()
    tags = []
    if tags_data:
        for tag_id, tag_info in tags_data.items():
            tags.append(Tag(
                id=tag_id,
                profileId=tag_info['profileId'],
                text=tag_info['text'],
                iconName=tag_info.get('iconName'),
                color=tag_info.get('color')
            ))

    return Profile(
        id=profile_data['id'],
        userId=profile_data['userId'],
        handle=profile_data.get('handle'),
        displayName=profile_data.get('displayName'),
        bio=profile_data.get('bio'),
        avatarUrl=profile_data.get('avatarUrl'),
        avatarDeleteUrl=profile_data.get('avatarDeleteUrl'),
        createdAt=datetime.fromisoformat(profile_data['createdAt']),
        updatedAt=datetime.fromisoformat(profile_data['updatedAt']),
        tags=tags
    )

@router.put("/profile/me", response_model=Profile)
async def update_my_profile(request: Request, user_id: str = Depends(get_current_user)):
    """Update current user's profile"""
    from app.core.config import profiles_ref

    if not profiles_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    # Debug: check what we're receiving
    body = await request.body()
    content_type = request.headers.get('content-type', '')

    # Parse JSON manually
    try:
        if 'application/json' in content_type:
            data = await request.json()
        else:
            # Try to parse as JSON anyway
            data = json.loads(body.decode('utf-8'))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}. Make sure there are no trailing commas.")

    # Validate required fields
    handle = data.get('handle')
    display_name = data.get('displayName')
    bio = data.get('bio')
    avatar_url = data.get('avatarUrl')

    # Check handle uniqueness if provided
    if handle:
        handle_lower = handle.lower()
        existing = profiles_ref.order_by_child('handle').equal_to(handle_lower).get()
        if existing:
            existing_id = list(existing.keys())[0]
            if existing_id != user_id:
                raise HTTPException(status_code=400, detail="Handle already taken")

    # Update profile with sanitized data
    update_data = {'updatedAt': datetime.utcnow().isoformat()}
    if handle is not None:
        update_data['handle'] = handle.lower()
    if display_name is not None:
        update_data['displayName'] = sanitize_text(display_name)
    if bio is not None:
        update_data['bio'] = sanitize_text(bio)
    if avatar_url is not None:
        update_data['avatarUrl'] = avatar_url

    profiles_ref.child(user_id).update(update_data)

    # Return updated profile
    return get_my_profile(user_id)



@router.post("/profile/me/avatar", response_model=Profile)
async def upload_avatar(request: Request, user_id: str = Depends(get_current_user)):
    """Upload/update user avatar using base64 data to ImgBB"""
    from app.core.config import profiles_ref

    # Debug: let's see what we're receiving
    body = await request.body()
    content_type = request.headers.get('content-type', '')

    try:
        if 'application/json' in content_type:
            data = await request.json()
        else:
            # Try to parse as JSON anyway
            data = json.loads(body.decode('utf-8'))
    except:
        return {"error": f"Invalid request. Content-Type: {content_type}, Body: {body[:200]}"}

    # Extract imageBase64 from the parsed data
    image_base64 = data.get('imageBase64')
    if not image_base64:
        raise HTTPException(status_code=400, detail="imageBase64 field required")

    if not profiles_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    # Get current profile
    profile_data = profiles_ref.child(user_id).get()
    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Delete old avatar if exists
    if profile_data.get('avatarDeleteUrl'):
        try:
            requests.get(profile_data['avatarDeleteUrl'])
        except Exception as e:
            # Log but don't fail if delete fails
            pass

    # Decode base64 image data
    try:
        # Handle data URL format: "data:image/png;base64,iVBORw0KGgo..."
        if image_base64.startswith('data:'):
            # Extract the base64 part after the comma
            base64_data = image_base64.split(',', 1)[1]
        else:
            base64_data = image_base64

        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")

    # Upload to ImgBB
    imgbb_api_key = os.getenv('IMGBB_API_KEY')
    if not imgbb_api_key:
        raise HTTPException(status_code=500, detail="ImgBB API key not configured")

    try:
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={'key': imgbb_api_key},
            files={'image': image_bytes}
        )
        response.raise_for_status()
        result = response.json()

        if not result.get('success'):
            raise HTTPException(status_code=500, detail="Failed to upload image to ImgBB")

        # Update profile with new URLs (only save the direct link)
        update_data = {
            'avatarUrl': result['data']['display_url'],
            'avatarDeleteUrl': result['data']['delete_url'],
            'updatedAt': datetime.utcnow().isoformat()
        }
        profiles_ref.child(user_id).update(update_data)

        # Return updated profile
        return get_my_profile(user_id)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
    """Upload/update user avatar using base64 data to ImgBB"""
    from app.core.config import profiles_ref

    if not profiles_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    # Get current profile
    profile_data = profiles_ref.child(user_id).get()
    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Delete old avatar if exists
    if profile_data.get('avatarDeleteUrl'):
        try:
            requests.get(profile_data['avatarDeleteUrl'])
        except Exception as e:
            # Log but don't fail if delete fails
            pass

    # Decode base64 image data
    try:
        # Handle data URL format: "data:image/png;base64,iVBORw0KGgo..."
        if avatar_data.imageBase64.startswith('data:'):
            # Extract the base64 part after the comma
            base64_data = avatar_data.imageBase64.split(',', 1)[1]
        else:
            base64_data = avatar_data.imageBase64

        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")

    # Upload to ImgBB
    imgbb_api_key = os.getenv('IMGBB_API_KEY')
    if not imgbb_api_key:
        raise HTTPException(status_code=500, detail="ImgBB API key not configured")

    try:
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={'key': imgbb_api_key},
            files={'image': image_bytes}
        )
        response.raise_for_status()
        result = response.json()

        if not result.get('success'):
            raise HTTPException(status_code=500, detail="Failed to upload image to ImgBB")

        # Update profile with new URLs (only save the direct link)
        update_data = {
            'avatarUrl': result['data']['display_url'],
            'avatarDeleteUrl': result['data']['delete_url'],
            'updatedAt': datetime.utcnow().isoformat()
        }
        profiles_ref.child(user_id).update(update_data)

        # Return updated profile
        return get_my_profile(user_id)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@router.delete("/profile/me/avatar")
def delete_avatar(user_id: str = Depends(get_current_user)):
    """Delete user avatar"""
    from app.core.config import profiles_ref

    if not profiles_ref:
        raise HTTPException(status_code=500, detail="Database not available")

    profile_data = profiles_ref.child(user_id).get()
    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Delete from ImgBB if delete URL exists
    if profile_data.get('avatarDeleteUrl'):
        try:
            requests.get(profile_data['avatarDeleteUrl'])
        except Exception as e:
            # Log but don't fail
            pass

    # Clear avatar fields
    update_data = {
        'avatarUrl': None,
        'avatarDeleteUrl': None,
        'updatedAt': datetime.utcnow().isoformat()
    }
    profiles_ref.child(user_id).update(update_data)

    return {"message": "Avatar deleted"}