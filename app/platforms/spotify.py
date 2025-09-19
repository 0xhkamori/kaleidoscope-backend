import logging
import os
import json
import time
from typing import Optional, Dict, List, Any
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from .soundcloud import search_soundcloud, get_soundcloud_stream_url
from .youtube import search_youtube, get_stream_url as get_youtube_stream_url, get_youtube_track_details

logger = logging.getLogger(__name__)

_spotify_client: Optional[spotipy.Spotify] = None

def get_spotify_client() -> Optional[spotipy.Spotify]:
    """Initializes and returns the Spotipy client."""
    global _spotify_client
    if _spotify_client is not None:
        return _spotify_client

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

    if not client_id or not client_secret:
        logger.error('SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not configured.')
        return None

    try:
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        _spotify_client = spotipy.Spotify(auth_manager=auth_manager)
        logger.info('Spotipy client initialized successfully.')
        return _spotify_client
    except Exception as e:
        logger.error(f'Error initializing Spotipy client: {e}', exc_info=True)
        _spotify_client = None
        return None

def _format_spotify_track(track_data: Optional[Dict[str, Any]], simplify_for_stream_search: bool = False) -> Optional[Dict[str, Any]]:
    if not track_data or not isinstance(track_data, dict) or track_data.get('type') != 'track':
        return None

    track_id = track_data.get('id')
    if not track_id:
        return None

    name = track_data.get('name', 'Unknown Title')
    artists_data = track_data.get('artists', [])
    artist_names = sorted([artist.get('name', '') for artist in artists_data if artist.get('name')])
    main_artist = artist_names[0] if artist_names else "Unknown Artist"
    all_artists_str = ", ".join(artist_names)

    if simplify_for_stream_search:
        return {
            'id': track_id,
            'name': name,
            'artist': main_artist,
            'duration_ms': track_data.get('duration_ms', 0)
        }

    album_data = track_data.get('album', {})
    cover_art = None
    if album_data.get('images'):
        cover_art = album_data['images'][0].get('url')

    duration_ms = track_data.get('duration_ms', 0)
    duration_s = duration_ms // 1000
    duration_str = f"{duration_s // 60}:{duration_s % 60:02d}"

    return {
        'id': track_id,
        'title': name,
        'artist': all_artists_str,
        'album': album_data.get('name', 'Unknown Album'),
        'duration': duration_s,
        'durationString': duration_str,
        'durationMs': duration_ms,
        'coverArt': cover_art,
        'source': 'spotify',
        'spotifyId': track_id,
        'previewUrl': track_data.get('preview_url'),
        'externalUrl': track_data.get('external_urls', {}).get('spotify'),
        'popularity': track_data.get('popularity')
    }

def get_spotify_track_details(track_id: str) -> Optional[Dict[str, Any]]:
    """Fetches track details from Spotify API by track ID."""
    sp = get_spotify_client()
    if not sp:
        logger.error('Spotify client not initialized or misconfigured.')
        return None

    try:
        track_data = sp.track(track_id)
        if not track_data:
            logger.warning(f'No track data found for Spotify track ID: {track_id}')
            return None

        return _format_spotify_track(track_data)
    except spotipy.SpotifyException as e:
        logger.error(f"Spotify API error fetching track {track_id}: {e.http_status} - {e.msg}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching Spotify track {track_id}: {e}", exc_info=True)
        return None

def get_spotify_stream_url(track_id: str) -> Optional[Dict[str, str]]:
    """Attempts to find a streamable equivalent for a Spotify track on SoundCloud or YouTube."""
    sp = get_spotify_client()
    if not sp:
        return {'error': 'Spotify client not configured.'}

    try:
        track_info_spotify = sp.track(track_id)
        if not track_info_spotify:
            return {'error': f'Spotify track ID {track_id} not found.'}

        simplified_track = _format_spotify_track(track_info_spotify, simplify_for_stream_search=True)
        if not simplified_track:
            return {'error': 'Could not format Spotify track details for search.'}

        track_name = simplified_track['name']
        artist_name = simplified_track['artist']
        spotify_duration_ms = simplified_track['duration_ms']

        logger.info(f"Spotify track: '{artist_name} - {track_name}'. Seeking stream on SoundCloud/YouTube.")

        sc_query = f"{artist_name} {track_name}"
        logger.debug(f"Searching SoundCloud with query: '{sc_query}'")
        sc_results = search_soundcloud(query=sc_query, limit=5)
        if sc_results:
            best_sc_match = None
            min_duration_diff = float('inf')
            for sc_track in sc_results:
                sc_duration_ms = sc_track.get('duration', 0) * 1000
                duration_diff = abs(sc_duration_ms - spotify_duration_ms)
                if duration_diff < min_duration_diff:
                    min_duration_diff = duration_diff
                    best_sc_match = sc_track
                if duration_diff <= 5000:
                    break

            if best_sc_match and min_duration_diff <= 10000:
                sc_track_id = str(best_sc_match['id'])
                logger.info(f"Found potential SoundCloud match ID {sc_track_id} (duration diff: {min_duration_diff}ms). Getting stream.")
                sc_stream_data = get_soundcloud_stream_url(sc_track_id)
                if sc_stream_data and sc_stream_data.get('url'):
                    logger.info(f"Returning SoundCloud stream for Spotify track {track_id} via SC ID {sc_track_id}.")
                    return sc_stream_data

        yt_query = f"{artist_name} - {track_name}"
        logger.debug(f"Searching YouTube with query: '{yt_query}'")
        yt_stream_data = get_youtube_stream_url(video_id=None, track_title=track_name, track_artist=artist_name, search_query_override=yt_query)

        if yt_stream_data and yt_stream_data.get('url'):
            if yt_stream_data.get('videoId'):
                yt_details = get_youtube_track_details(yt_stream_data['videoId'])
                if yt_details and yt_details.get('durationMs'):
                    yt_duration_ms = yt_details['durationMs']
                    if abs(yt_duration_ms - spotify_duration_ms) > 15000:
                        logger.warning(f"YouTube match {yt_stream_data['videoId']} duration ({yt_duration_ms}ms) differs significantly from Spotify ({spotify_duration_ms}ms). Not using.")
                    else:
                        logger.info(f"Returning YouTube stream for Spotify track {track_id} via YT ID {yt_stream_data['videoId']}.")
                        return yt_stream_data
                else:
                    logger.info(f"Returning YouTube stream (could not verify duration) for Spotify track {track_id}.")
                    return yt_stream_data
            else:
                logger.info(f"Returning YouTube stream/embed for Spotify track {track_id}.")
                return yt_stream_data

        if track_info_spotify.get('preview_url'):
            logger.info(f"No SoundCloud/YouTube stream found. Returning Spotify preview URL for track {track_id}.")
            return {
                'url': track_info_spotify['preview_url'],
                'type': 'audio_preview',
                'source': 'spotify'
            }

        logger.warning(f"Could not find any streamable source (SoundCloud, YouTube, Spotify Preview) for Spotify track {track_id}.")
        return {'error': 'No streamable source found for this Spotify track.'}

    except spotipy.SpotifyException as e:
        logger.error(f"Spotify API error processing stream for track {track_id}: {e.http_status} - {e.msg}", exc_info=True)
        return {'error': f'Spotify API error: {e.msg}'}
    except Exception as e:
        logger.error(f"Unexpected error processing stream for Spotify track {track_id}: {e}", exc_info=True)
        return {'error': f'Unexpected error: {str(e)}'}

def search_spotify(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Searches for tracks on Spotify and formats them."""
    sp = get_spotify_client()
    if not sp:
        logger.error("Spotify client not initialized. Cannot perform search.")
        return []

    logger.info(f"Searching Spotify for query: '{query}' with limit: {limit}")
    try:
        results = sp.search(q=query, limit=limit, type='track', market='US')
        tracks: List[Dict[str, Any]] = []
        if results and results.get('tracks') and results['tracks'].get('items'):
            for item in results['tracks']['items']:
                formatted_track = _format_spotify_track(item)
                if formatted_track:
                    formatted_track['streamUrl'] = None
                    tracks.append(formatted_track)
        logger.info(f"Spotify search for '{query}' found {len(tracks)} tracks.")
        return tracks
    except spotipy.SpotifyException as e:
        logger.error(f"Spotify API error during search for '{query}': {e.http_status} - {e.msg}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error during Spotify search for '{query}': {e}", exc_info=True)
        return []