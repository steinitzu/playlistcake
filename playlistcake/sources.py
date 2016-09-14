from collections import OrderedDict
from datetime import datetime

import isodate
from .spotifystuff import get_spotify, iterate_results
from .util import iter_chunked, get_ids, get_id, get_limit
from .util import reservoir_sample


def several_albums(albums):
    s = get_spotify()
    for chunk in iter_chunked(albums, 20):
        aids = get_ids(chunk)
        yield from s.albums(aids)['albums']


def several_tracks(tracks):
    s = get_spotify()
    for chunk in iter_chunked(tracks, 50):
        tids = get_ids(chunk)
        yield from s.tracks(tids)['tracks']


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


def artists_albums(artists, album_type='album'):
    """
    Get all albums from given artists.
    """
    country = user_country()
    s = get_spotify()

    def _simple_albums(artists):
        for artist in artists:
            yield from s.artist_albums(
                artist['id'],
                country=country,
                album_type=album_type,
                limit=50)['items']

    for chunk in iter_chunked(_simple_albums(artists), 20):
        yield from several_albums(chunk)


def artists_top_tracks(artists, max_per_artist=10):
    """
    Get top tracks from several artists.
    If max_per_artist is set a random sample is used.
    """
    s = get_spotify()
    country = user_country()
    for artist in artists:
        aid = get_id(artist)
        yield from reservoir_sample(
            s.artist_top_tracks(
                aid, country=country)['tracks'], max_per_artist)


def tracks_from_albums(albums):
    chunk = []
    for album in albums:
        if len(chunk) == 50:
            yield from several_tracks(chunk)
            chunk = []
        for track in album['tracks']['items']:
            chunk.append(track)
    if chunk:
        yield from several_tracks(chunk)


def albums_filter_release_year(albums, start=1990, end=2000):
    for album in albums:
        rdate = isodate.parse_date(album['release_date'])
        if start <= rdate.year <= end:
            yield album


def tracks_filter_release_year(tracks, start=1990, end=2000):
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


def items_to_seeds(objects, seed_size=5):
    """
    Convenience method to chunk iterables of artist or track
    object into lists of `seed_size` length of item ids.
    Has the added bonus of guaranteeing each item appears only
    once in the resulting set of seeds.
    """
    if seed_size > 5 or seed_size < 1:
        raise ValueError('Seed size must be between 1 and 5')
    been_used = set()
    chunk = []
    for item in objects:
        iid = get_id(item)
        if iid in been_used:
            continue
        been_used.add(iid)
        chunk.append(iid)
        if len(chunk) == seed_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def recommendations(seed_artists=(),
                    seed_tracks=(),
                    seed_genres=(),
                    max_results=50,
                    **tuneables):
    limit = get_limit(max_results, 50)
    yield from iterate_results(
        'recommendations',
        items_path='tracks',
        seed_artists=seed_artists,
        seed_tracks=seed_tracks,
        seed_genres=seed_genres,
        max_results=max_results,
        limit=limit,
        **tuneables)


def batch_recommendations(seed_gen=(),
                          seed_gen_type='artist',
                          suppl_artists=(),
                          suppl_tracks=(),
                          seed_genres=(),
                          max_results=None,
                          max_per_seed=50,
                          **tuneables):
    """
    Provided a seed generator object (like the
    one returned by `items_to_seeds`, yields
    recommendations based on those seeds + any
    static seeds provided (artists/tracks/genres)

    seed_gen: A seed generator (like returned by `items to seeds`)
    seed_gen_type: The type of seeds yielded by seed_gen (
                   'artist' or 'track')
    suppl_artists: list of artist ids to supplement each
                  iteration of seed_gen
    suppl_tracks: list of track ids to supplement each
                  iteration of seed_ge
    seed_genres: list of genres to supplement each
                  iteration of seed_gen
    max_results: total maximum results
    limit: max number of tracks per seed_gen iteration
    **tuneables: any number of tuneable audio attributes
    """
    if seed_gen_type not in ('artist', 'track'):
        raise ValueError('Invalid seed_gen_type, use "artist" or "track"')
    result_count = 0
    for seed in seed_gen:
        seed_artists = []
        seed_tracks = []
        if seed_gen_type == 'artist':
            seed_artists += seed
        elif seed_gen_type == 'tracks':
            seed_tracks += seed
        seed_artists += get_ids(suppl_artists)
        seed_tracks += get_ids(suppl_tracks)
        for track in recommendations(
                seed_artists=seed_artists,
                seed_tracks=seed_tracks,
                seed_genres=seed_genres,
                max_results=max_per_seed,
                **tuneables):
            yield track
            result_count += 1
        if max_results and result_count >= max_results:
            return


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
    Filter that yields each unique track only once.
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


def tracks_sort_by_audio_feature(tracks, sort_key, order='asc'):
    tracks = with_audio_features(tracks)
    tracks = list(tracks)
    reverse = order == 'desc'
    tracks.sort(key=lambda k: k['audio_features'][sort_key], reverse=reverse)
    yield from tracks


def items_sorted_by_attributes(items, sort_func, order='asc'):
    reverse = order == 'desc'
    items = with_audio_features(items)
    items = sorted(items, key=sort_func, reverse=reverse)
    yield from items
    #tracks = list(tracks)
    #tracks.sort(key=sort_func)
    # yield from tracks
    # s = sorted(s, key = lambda x: (x[1], x[2])


def full_album(album_or_uri):
    """
    Given a partial album object or album uri,
    return a full album object from the spotify api.
    """
    a = album_or_uri
    if isinstance(a, dict):
        if 'tracks' in a:
            # already a full object
            return a
        else:
            a = a['uri']
    s = get_spotify()
    return s.album(a)


def full_track(track_or_uri):
    """
    Given a partial track object or track uri,
    return a full track object from the spotify api.
    """
    a = track_or_uri
    if isinstance(a, dict):
        if 'album' in a:
            # already a full object
            return a
        else:
            a = a['uri']
    s = get_spotify()
    return s.track(a)


def find_artist(name):
    """
    Given an artist name, return an artist object
    from search results.
    returns None if no artist is found.
    """
    q = 'artist:{}'.format(name)
    s = get_spotify()
    result = s.search(q, limit=1, type='artist', market=user_country())
    items = result['artists']['items']
    return items[0] if items else None


def find_album(artist, name):
    s = get_spotify()
    q = 'artist:{} album:{}'.format(artist, name)
    result = s.search(q, limit=1, type='album', market=user_country())
    items = result['albums']['items']
    return full_album(items[0]) if items else None


def find_track(artist, name):
    q = 'artist:{} track:{}'.format(artist, name)
    s = get_spotify()
    result = s.search(q, limit=1, type='track', market=user_country())
    items = result['tracks']['items']
    return items[0] if items else None


def user_country():
    s = get_spotify()
    return s.current_user()['country']


def create_playlist(name='Generated playlist', public=True):
    s = get_spotify()
    return s.user_playlist_create(
        s.me()['id'],
        name,
        public=public)


def add_to_playlist(tracks, playlist):
    s = get_spotify()
    for chunk in iter_chunked(tracks, 50):
        tids = get_ids(chunk)
        s.user_playlist_add_tracks(
            playlist['owner']['id'],
            playlist['id'],
            tids)
