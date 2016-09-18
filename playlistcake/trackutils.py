from .spotifystuff import get_spotify
from .util import iter_chunked, get_ids


def with_audio_features(tracks):
    """
    Yields the given tracks with
    audio_features (track['audio_features'])
    """
    s = get_spotify()
    for chunk in iter_chunked(tracks, 100):
        tids = get_ids(chunk)
        features = s.audio_features(tracks=tids)
        for i, item in enumerate(features):
            track = chunk[i]
            track['audio_features'] = item
            yield track
