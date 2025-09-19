import logging
import yt_dlp
from ytmusicapi import YTMusic
import re
import json
import time
from typing import Optional, Dict, List, Any, Tuple, Union
from pytube import YouTube

logger = logging.getLogger(__name__)

try:
    ytmusic = YTMusic()
except Exception as e:
    logger.error(f"Error initializing YTMusic: {e}", exc_info=True)
    ytmusic = None

MAX_DURATION_SEARCH_SECONDS = 300
MAX_DURATION_DETAILS_SECONDS = 300
YOUTUBE_WATCH_URL = "https://www.youtube.com/watch?v="
YOUTUBE_EMBED_URL = "https://www.youtube.com/embed/"
YOUTUBE_MUSIC_PLAYLIST_URL = "https://music.youtube.com/playlist?list="
YOUTUBE_MUSIC_BROWSE_URL = "https://music.youtube.com/browse/"

def _parse_duration(duration_str: Optional[str]) -> int:
    """Parses a duration string (e.g., "1:23", "1:02:03") into seconds."""
    if not duration_str or not isinstance(duration_str, str):
        return 0
    parts = list(map(int, duration_str.split(':')))
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 1:
        return parts[0]
    return 0

def _format_duration_string(seconds: int) -> str:
    """Converts seconds to MM:SS or HH:MM:SS string."""
    if seconds <= 0:
        return "0:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def _get_best_thumbnail(thumbnails: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """Extracts the best available thumbnail URL from a list."""
    if not thumbnails or not isinstance(thumbnails, list):
        return None
    quality_order = ['maxresdefault', 'sddefault', 'hqdefault', 'mqdefault', 'default']
    if all(isinstance(t, dict) and 'url' in t and 'width' in t and 'height' in t for t in thumbnails):
        try:
            return max(thumbnails, key=lambda t: t.get('width', 0) * t.get('height', 0)).get('url')
        except ValueError:
            pass
    found_qualities: Dict[str, str] = {}
    best_url: Optional[str] = None
    for thumb in reversed(thumbnails):
        if isinstance(thumb, dict):
            url = thumb.get('url')
            thumb_id = thumb.get('id', '').lower()
            if not url:
                continue
            best_url = url
            for quality_key in quality_order:
                if quality_key in url or quality_key == thumb_id:
                    if quality_key not in found_qualities:
                        found_qualities[quality_key] = url
        elif isinstance(thumb, str) and thumb.startswith('http'):
            best_url = thumb
            for quality_key in quality_order:
                if quality_key in thumb:
                    if quality_key not in found_qualities:
                        found_qualities[quality_key] = thumb
    for q_key in quality_order:
        if q_key in found_qualities:
            return found_qualities[q_key]
    return best_url

def _extract_artist_names(artists_data: Optional[List[Dict[str, str]]]) -> str:
    """Extracts and joins artist names from typical API artist list structure."""
    if not artists_data or not isinstance(artists_data, list):
        return "Unknown Artist"
    names = []
    for artist in artists_data:
        if isinstance(artist, dict) and artist.get('name'):
            names.append(artist['name'].strip())
    return ", ".join(names) if names else "Unknown Artist"

def search_youtube(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Searches tracks on YouTube Music."""
    if not ytmusic:
        logger.error("YTMusic client not initialized, cannot search YouTube.")
        return []
    try:
        logger.info(f"Request to YouTube Music: query='{query}', limit={limit}")
        search_results = ytmusic.search(query, filter='songs', limit=limit)
        if not search_results:
            logger.warning(f"No YouTube Music search results for query: '{query}'")
            return []
        tracks = []
        for item in search_results:
            video_id = item.get('videoId')
            if not video_id:
                logger.warning(f"Skipping track due to missing videoId: {item.get('title', 'N/A')}")
                continue
            duration_seconds = _parse_duration(item.get('duration'))
            if MAX_DURATION_SEARCH_SECONDS > 0 and duration_seconds > MAX_DURATION_SEARCH_SECONDS:
                logger.info(f"Track '{item.get('title')}' ({_format_duration_string(duration_seconds)}) skipped due to duration > {MAX_DURATION_SEARCH_SECONDS // 60} mins in search.")
                continue
            artist_display_name = _extract_artist_names(item.get('artists'))
            if artist_display_name == "Unknown Artist" and isinstance(item.get('artist'), str):
                artist_display_name = item['artist']
            track = {
                'id': video_id,
                'videoId': video_id,
                'title': item.get('title', 'Unknown Title'),
                'artist': artist_display_name,
                'album': item.get('album', {}).get('name', '') if item.get('album') else '',
                'duration': duration_seconds,
                'durationString': _format_duration_string(duration_seconds),
                'coverArt': _get_best_thumbnail(item.get('thumbnails')),
                'source': 'youtube'
            }
            tracks.append(track)
        logger.info(f"Found {len(tracks)} tracks on YouTube for query: '{query}'")
        return tracks
    except Exception as e:
        logger.error(f"Error searching YouTube Music: {e}", exc_info=True)
        return []

def get_stream_url(video_id: str = None, track_title: Optional[str] = None, track_artist: Optional[str] = None, search_query_override: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Gets the audio stream URL for a YouTube video. If video_id is None, searches for the track first."""
    if video_id is None:
        if search_query_override:
            query = search_query_override
        elif track_title and track_artist:
            query = f"{track_artist} - {track_title}"
        else:
            logger.error("No video_id, search_query_override, or track info provided for YouTube stream.")
            return None
        logger.info(f"Searching YouTube for stream: '{query}'")
        search_results = search_youtube(query, limit=1)
        if search_results:
            video_id = search_results[0]['id']
            logger.info(f"Found YouTube video ID: {video_id}")
        else:
            logger.error(f"No YouTube search results for '{query}'")
            return None

    logger.info(f"Requesting stream for YouTube video: {video_id}")
    youtube_video_url = f"{YOUTUBE_WATCH_URL}{video_id}"
    youtube_embed_fallback_url = f"{YOUTUBE_EMBED_URL}{video_id}?autoplay=1"
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'concurrent_fragment_downloads': 5,
        'retries': 1,
        'fragment_retries': 1,
        'continuedl': True,
        'nocheckcertificate': True,
        'skip_download': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_video_url, download=False)
            if info and 'url' in info:
                return {'url': info['url'], 'type': 'audio', 'source': 'youtube'}
            return {'url': youtube_embed_fallback_url, 'type': 'embed', 'source': 'youtube'}
    except Exception as e:
        logger.error(f"Error getting stream for {video_id}: {e}", exc_info=True)
        return {'url': youtube_embed_fallback_url, 'type': 'embed', 'source': 'youtube'}

def get_youtube_track_details(video_id: str) -> Optional[Dict[str, Any]]:
    """Gets detailed information for a YouTube video using YTMusic API and yt-dlp as fallback."""
    logger.info(f"Requesting details for YouTube ID: {video_id}")
    track_details: Optional[Dict[str, Any]] = None
    if ytmusic:
        try:
            song_info = ytmusic.get_song(videoId=video_id)
            if song_info and song_info.get('videoDetails'):
                details = song_info['videoDetails']
                duration_seconds = int(details.get('lengthSeconds', 0))
                if MAX_DURATION_DETAILS_SECONDS > 0 and duration_seconds > MAX_DURATION_DETAILS_SECONDS:
                    logger.info(f"Track '{details.get('title')}' ({_format_duration_string(duration_seconds)}) skipped from YTMusic details due to duration > {MAX_DURATION_DETAILS_SECONDS // 60} mins.")
                else:
                    artist_name = details.get('author', 'Unknown Artist')
                    if 'artists' in song_info and song_info['artists']:
                        parsed_artists = _extract_artist_names(song_info['artists'])
                        if parsed_artists != "Unknown Artist":
                            artist_name = parsed_artists
                    album_name = None
                    if 'album' in song_info and song_info['album'] and isinstance(song_info['album'], dict):
                        album_name = song_info['album'].get('name')
                    track_details = {
                        'id': video_id,
                        'videoId': video_id,
                        'title': details.get('title', 'Unknown Title'),
                        'artist': artist_name,
                        'album': album_name,
                        'duration': duration_seconds,
                        'durationString': _format_duration_string(duration_seconds),
                        'coverArt': _get_best_thumbnail(details.get('thumbnail', {}).get('thumbnails')),
                        'source': 'youtube'
                    }
                    logger.info(f"Initial details obtained via YTMusic API for {video_id}")
        except Exception as e_ytmusic:
            logger.warning(f"Error getting details via YTMusic API for {video_id}: {e_ytmusic}. Trying yt-dlp.")
    if not track_details:
        try:
            ydl_opts = {
                'quiet': True, 'no_warnings': True, 'skip_download': True,
                'noplaylist': True, 'forcejson': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"{YOUTUBE_WATCH_URL}{video_id}", download=False)
                if info:
                    title = info.get('title', 'Unknown Title')
                    artist = info.get('artist') or info.get('uploader') or info.get('channel')
                    if not artist and ' - ' in title:
                        parts = title.split(' - ', 1)
                        if len(parts) == 2 and len(parts[0]) < len(parts[1]) and len(parts[0]) < 40:
                            artist, title = parts
                    if not artist:
                        artist = "Unknown Artist"
                    duration_seconds = int(info.get('duration', 0))
                    if MAX_DURATION_DETAILS_SECONDS > 0 and duration_seconds > MAX_DURATION_DETAILS_SECONDS:
                        logger.info(f"Track '{title}' ({_format_duration_string(duration_seconds)}) skipped from yt-dlp details due to duration > {MAX_DURATION_DETAILS_SECONDS // 60} mins.")
                        if not track_details:
                            return None
                    track_details = {
                        'id': video_id,
                        'videoId': video_id,
                        'title': title,
                        'artist': artist,
                        'album': info.get('album'),
                        'duration': duration_seconds,
                        'durationString': _format_duration_string(duration_seconds),
                        'coverArt': _get_best_thumbnail(info.get('thumbnails')),
                        'source': 'youtube'
                    }
                    logger.info(f"Details (re)populated via yt-dlp for {video_id}")
        except Exception as e_ytdlp:
            logger.error(f"Error getting details via yt-dlp for {video_id}: {e_ytdlp}", exc_info=True)
            if not track_details:
                logger.error(f"Failed to get any details for YouTube ID {video_id} using all methods.")
                return None
    if not track_details:
        logger.error(f"Completely failed to get details for YouTube ID {video_id}.")
        return None
    return track_details