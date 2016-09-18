from .trackutils import with_audio_features


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
        elif key.startswith('target_'):
            key = key[len('target_'):]
            margin = margins[key]
            low = value - margin
            high = value + margin
            is_match = low <= track[key] <= high
        if not is_match:
            return False
    return is_match


def tracks_filter_tuneables(tracks, **tuneables):
    for track in with_audio_features(tracks):
        if _matches_tunables(track, **tuneables):
            yield track


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
