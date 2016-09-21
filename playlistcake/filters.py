import isodate

from .trackutils import with_audio_features
from .util import iter_chunked
from .sources import several_albums


def _matches_tunables(track, **tuneables):
    margins = {
        'acousticness': 0.1,
        'danceability': 0.1,
        'duration_ms': 10000,
        'energy': 0.1,
        'instrumentalness': 0.1,
        'key': 0,
        'liveness': 0.1,
        'loudness': 1,
        'mode': 0,
        'popularity': 5,
        'speechiness': 0.1,
        'tempo': 8,
        'time_signature': 0,
        'valence': 0.1
        }
    _track = track
    is_match = True
    for key, value in tuneables.items():
        track = _track['audio_features']
        if key.endswith('popularity'):
            # Popularity is not under audio_features, but include it anyway
            track = _track
        if key.startswith('min_'):
            key = key[len('min_'):]
            is_match = track[key] >= value
        elif key.startswith('max_'):
            key = key[len('max_'):]
            is_match = track[key] <= value
        elif key.startswith('target_') or key in margins:
            key = key[len('target_'):]
            margin = margins[key]
            low = value - margin
            high = value + margin
            is_match = low <= track[key] <= high
        if not is_match:
            return False
    return is_match


def tracks_filter_tuneables(tracks, invert=False, **tuneables):
    """
    Filter tracks by audio_features (**tuneables).
    Tuneables may be prefixed by min_/max_/target_
    """
    for track in with_audio_features(tracks):
        if _matches_tunables(track, **tuneables):
            yield track
        elif invert:
            yield track


def albums_filter_release_years(albums, start=1990, end=2000, invert=False):
    for album in albums:
        rdate = isodate.parse_date(album['release_date'])
        if start <= rdate.year <= end:
            yield album
        elif invert:
            yield album


def tracks_filter_release_years(tracks, start=1990, end=2000, invert=False):
    """
    Assumes full track objects.
    """

    for chunk in iter_chunked(tracks, 20):
        aids = [track['album']['id'] for track in chunk]
        albums = several_albums(aids)
        for i, album in enumerate(albums):
            rdate = isodate.parse_date(album['release_date'])
            if start <= rdate.year <= end:
                yield chunk[i]
            elif invert:
                yield album


def tracks_filter_unique(tracks):
    """
    Filter that yields each unique item only once.
    """
    used = set()
    for track in tracks:
        if track['id'] in used:
            continue
        used.add(track['id'])
        yield track


def tracks_filter_artist_variety(tracks, limit=1):
    """
    Goes through the track stream and yields no more
    than limit tracks by each unique artist.
    """
    # artist_id: track_count
    track_count = {}
    for track in tracks:
        aid = track['artists'][0]['id']
        if aid in track_count:
            if track_count[aid] >= limit:
                continue
            track_count[aid] += 1
        else:
            track_count[aid] = 1
        yield track


# TODO: Use partials
# tracks original
# pipedthrough(partial_filter(args), partial_blablah(args) ...)
