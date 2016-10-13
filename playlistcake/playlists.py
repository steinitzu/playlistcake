from .spotify import iterate_results, get_spotify
from .util import get_limit, get_ids, iter_chunked
from .genutils import yields


@yields('playlists')
def user_playlists(max_results=None):
    limit = get_limit(max_results, 50)
    s = get_spotify()
    user = s.current_user()['id']
    yield from iterate_results(
        'user_playlists',
        user,
        limit=limit,
        max_results=max_results)


@yields('tracks')
def playlists_tracks(playlists):
    """
    Given a list/generator of simplified playlist
    objects, yield the tracks from them.
    Get tracks from a list of playlists.

    """
    for playlist in playlists:
        user = playlist['owner']['id']
        yield from iterate_results(
            'user_playlist_tracks',
            user,
            playlist_id=playlist['id'],
            limit=100)


def create_playlist(name='Generated playlist', public=True):
    s = get_spotify()
    return s.user_playlist_create(
        s.me()['id'],
        name,
        public=public)


def add_to_playlist(tracks, playlist):
    if isinstance(playlist, str):
        playlist = create_playlist(playlist)
    s = get_spotify()
    for chunk in iter_chunked(tracks, 50):
        tids = get_ids(chunk)
        s.user_playlist_add_tracks(
            playlist['owner']['id'],
            playlist['id'],
            tids)
