import logging
import requests
import json
import os
from typing import Optional, Dict, List, Any, Union
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SOUNDCLOUD_API_V2_URL = 'https://api-v2.soundcloud.com'
SOUNDCLOUD_APP_VERSION = '1686318471'
SOUNDCLOUD_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

def get_soundcloud_client_id():
    return os.getenv('SOUNDCLOUD_CLIENT_ID')

def _format_duration_soundcloud(duration_ms: Optional[int]) -> str:
    if not duration_ms or duration_ms <= 0:
        return "0:00"
    seconds = duration_ms // 1000
    minutes = seconds // 60
    seconds %= 60
    hours = minutes // 60
    minutes %= 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def _get_safe_artwork_url_soundcloud(url: Optional[str], preferred_size: str = 't500x500') -> Optional[str]:
    """Safely gets a larger artwork URL from SoundCloud, handling None and replacing size markers."""
    if not url or not isinstance(url, str):
        logger.debug(f"_get_safe_artwork_url_soundcloud: Received null or non-string URL: {url}")
        return None
    original_url = str(url)
    try:
        sizes_to_replace = ['badge', 'tiny', 'small', 't67x67', 'mini', 't120x120', 'large', 't300x300', 'crop']
        if f"-{preferred_size}." in original_url or "-original." in original_url:
            logger.debug(f"_get_safe_artwork_url_soundcloud: URL '{original_url}' is already preferred size or original.")
            return original_url
        for size_marker in sizes_to_replace:
            if f"-{size_marker}." in original_url:
                new_url = original_url.replace(f"-{size_marker}.", f"-{preferred_size}.")
                logger.debug(f"_get_safe_artwork_url_soundcloud: Replaced marker '{size_marker}' in '{original_url}' to '{new_url}'.")
                return new_url
        if original_url.startswith('http'):
            logger.debug(f"_get_safe_artwork_url_soundcloud: URL '{original_url}' has no recognized size markers but starts with http. Returning as is.")
            return original_url
        logger.warning(f"_get_safe_artwork_url_soundcloud: URL '{original_url}' is not recognized after checks (no markers, not http). Returning None.")
        return None
    except Exception as e:
        logger.warning(f"_get_safe_artwork_url_soundcloud: Could not process SoundCloud artwork URL '{original_url}': {e}")
        return original_url

def format_soundcloud_track(track_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Formats SoundCloud track data into a common application format."""
    if not track_data or not isinstance(track_data, dict):
        return None
    try:
        track_id = track_data.get('id')
        if not track_id:
            logger.warning("SoundCloud track data missing ID.")
            return None
        has_progressive_stream = False
        is_streamable_api_flag = track_data.get('streamable', False)
        media = track_data.get('media', {})
        transcodings = media.get('transcodings', [])
        for transcoding in transcodings:
            if (transcoding.get('format', {}).get('protocol') == 'progressive' and transcoding.get('url')):
                has_progressive_stream = True
                break
        if not has_progressive_stream and not is_streamable_api_flag:
            logger.debug(f"Track '{track_data.get('title')}' (ID: {track_id}) is not streamable or has no progressive transcodings. Skipping.")
            return None
        if not has_progressive_stream and is_streamable_api_flag:
            logger.debug(f"Track '{track_data.get('title')}' (ID: {track_id}) is marked streamable but no direct progressive transcoding found. May rely on API for playback.")
        duration_ms = track_data.get('duration', 0)
        duration_seconds = duration_ms // 1000
        formatted_track = {
            'id': str(track_id),
            'title': track_data.get('title', 'Unknown Title'),
            'artist': track_data.get('user', {}).get('username', 'Unknown Artist'),
            'duration': duration_seconds,
            'durationString': _format_duration_soundcloud(duration_ms),
            'source': 'soundcloud',
            'streamable': has_progressive_stream or is_streamable_api_flag,
            'coverArt': None,
            'genre': track_data.get('genre'),
            'permalinkUrl': track_data.get('permalink_url')
        }
        artwork_url = track_data.get('artwork_url')
        user_avatar_url = track_data.get('user', {}).get('avatar_url')
        final_cover_art = _get_safe_artwork_url_soundcloud(artwork_url)
        if not final_cover_art:
            final_cover_art = _get_safe_artwork_url_soundcloud(user_avatar_url)
        formatted_track['coverArt'] = final_cover_art
        return formatted_track
    except Exception as e:
        logger.error(f"Error formatting SoundCloud track data (ID: {track_data.get('id', 'N/A')}): {e}", exc_info=True)
        return None

def search_soundcloud(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Searches tracks on SoundCloud."""
    client_id = get_soundcloud_client_id()
    if not client_id:
        logger.error('SoundCloud Client ID not found, cannot search.')
        return []
    actual_limit = min(max(1, int(limit)), 50)
    params = {
        'q': query,
        'client_id': client_id,
        'limit': actual_limit,
        'offset': 0,
        'app_version': SOUNDCLOUD_APP_VERSION,
        'app_locale': 'en'
    }
    headers = {'User-Agent': SOUNDCLOUD_USER_AGENT, 'Accept': 'application/json'}
    try:
        response = requests.get(f'{SOUNDCLOUD_API_V2_URL}/search/tracks', params=params, headers=headers, timeout=10)
        response.raise_for_status()
        search_data = response.json()
        tracks = []
        for item_data in search_data.get('collection', []):
            formatted_track = format_soundcloud_track(item_data)
            if formatted_track:
                tracks.append(formatted_track)
        logger.info(f"Found {len(tracks)} SoundCloud tracks for query: '{query}'")
        return tracks
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during SoundCloud search request for '{query}': {e}", exc_info=True)
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from SoundCloud search for '{query}': {e}. Response text: {response.text[:200] if response else 'N/A'}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during SoundCloud search for '{query}': {e}", exc_info=True)
        return []

def get_soundcloud_stream_url(track_id: Union[str, int], track_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
    """Gets the direct stream URL for a SoundCloud track. Can accept pre-fetched track_data."""
    client_id = get_soundcloud_client_id()
    if not client_id:
        logger.error('SoundCloud Client ID not found, cannot get stream URL.')
        return None
    headers = {
        'User-Agent': SOUNDCLOUD_USER_AGENT,
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://soundcloud.com/'
    }
    if track_data is None:
        logger.debug(f"No pre-fetched track data for {track_id}, fetching from API.")
    try:
        track_info_url = f'{SOUNDCLOUD_API_V2_URL}/tracks/{track_id}?client_id={client_id}&app_version={SOUNDCLOUD_APP_VERSION}'
        logger.debug(f"Fetching SoundCloud track metadata from: {track_info_url}")
        track_response = requests.get(track_info_url, headers=headers, timeout=10)
        track_response.raise_for_status()
        track_data = track_response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching SoundCloud track metadata for ID {track_id}: {e}", exc_info=True)
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from SoundCloud track metadata for ID {track_id}: {e}. Response: {track_response.text[:200] if track_response else 'N/A'}")
        return None
    if not track_data:
        logger.warning(f"get_soundcloud_stream_url called for track {track_id} but track_data is missing/empty after fetch attempt.")
        return None
    progressive_stream_info_url: Optional[str] = None
    transcodings = track_data.get('media', {}).get('transcodings', [])
    for transcoding in transcodings:
        if transcoding.get('format', {}).get('protocol') == 'progressive' and transcoding.get('url'):
            progressive_stream_info_url = transcoding['url']
            logger.debug(f"Found progressive stream info URL for track {track_id}: {progressive_stream_info_url}")
            break
    if not progressive_stream_info_url:
        logger.warning(f"No progressive stream transcoding URL found for SoundCloud track {track_id}.")
        return None
    try:
        final_request_url = progressive_stream_info_url
        if 'client_id=' not in final_request_url:
            final_request_url += ('&' if '?' in final_request_url else '?') + f'client_id={client_id}'
        logger.debug(f"Fetching final SoundCloud stream data from: {final_request_url}")
        stream_response = requests.get(final_request_url, headers=headers, timeout=10, allow_redirects=True)
        stream_response.raise_for_status()
        stream_data = stream_response.json()
        final_audio_url = stream_data.get('url')
        if not final_audio_url:
            logger.error(f"Final audio URL missing in SoundCloud stream data for track {track_id}. Response: {json.dumps(stream_data, indent=2)}")
            return None
        logger.info(f"Successfully obtained final audio stream URL for SoundCloud track {track_id}")
        return {'url': final_audio_url, 'type': 'audio', 'source': 'soundcloud'}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching final SoundCloud stream URL for track {track_id} from {progressive_stream_info_url}: {e}", exc_info=True)
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from final SoundCloud stream response for track {track_id}: {e}. Response: {stream_response.text[:500] if stream_response else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting final SoundCloud stream for track {track_id}: {e}", exc_info=True)
        return None

def get_soundcloud_track_details(track_id: Union[str, int]) -> Optional[Dict[str, Any]]:
    """Gets raw details for a single SoundCloud track from the API."""
    client_id = get_soundcloud_client_id()
    if not client_id:
        logger.error('SoundCloud Client ID not found, cannot get track details.')
        return None
    params = {'client_id': client_id, 'app_version': SOUNDCLOUD_APP_VERSION}
    headers = {'User-Agent': SOUNDCLOUD_USER_AGENT, 'Accept': 'application/json'}
    try:
        response = requests.get(f'{SOUNDCLOUD_API_V2_URL}/tracks/{track_id}', params=params, headers=headers, timeout=10)
        response.raise_for_status()
        track_data = response.json()
        logger.info(f"Raw details fetched for SoundCloud track {track_id} via API: {track_data}")
        return track_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching SoundCloud track details for ID {track_id}: {e}", exc_info=True)
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON for SoundCloud track details {track_id}: {e}. Response: {response.text[:200] if response else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting SoundCloud track details for ID {track_id}: {e}", exc_info=True)
        return None