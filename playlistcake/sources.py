import random
from collections import OrderedDict
from datetime import datetime

import isodate

from .spotifystuff import get_spotify, iterate_results
from .util import get_id, get_ids, get_limit, iter_chunked, reservoir_sample
from .genutils import content, parent_content


@content('albums')
def several_albums(albums):
    s = get_spotify()
    for chunk in iter_chunked(albums, 20):
        aids = get_ids(chunk)
        yield from s.albums(aids)['albums']


@content('tracks')
def several_tracks(tracks):
    s = get_spotify()
    for chunk in iter_chunked(tracks, 50):
        tids = get_ids(chunk)
        yield from s.tracks(tids)['tracks']


@content('tracks')
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


@content('albums')
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


@content('tracks')
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


@content('tracks')
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


@parent_content()
def items_sorted(items, sort_func, order='asc'):
    """
    Sorts the stream of items using given sort_func as key.
    """
    reverse = order == 'desc'
    items = with_audio_features(items)
    items = sorted(items, key=sort_func, reverse=reverse)
    yield from items


@parent_content()
def items_shuffled(items):
    """
    Shuffles the stream.
    """
    items = list(items)
    random.shuffle(items)
    yield from items


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
