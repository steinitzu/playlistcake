from collections import OrderedDict
from datetime import datetime

import isodate
from .trackutils import with_audio_features
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
        elif seed_gen_type == 'track':
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
