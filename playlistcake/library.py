from datetime import datetime
import itertools

import isodate

from .util import get_limit
from .spotify import iterate_results
from .genutils import yields, infer_content


"""
Methods dealing with the user library.
"""


@yields('albums')
def saved_albums(max_results=None, album_only=False):
    """
    Yields saved album objects.
    {'album' full album, 'added_at': timestamp}
    If album_only==True, yield only album.
    """
    limit = get_limit(max_results, 50)
    for item in iterate_results(
            'current_user_saved_albums',
            max_results=max_results,
            limit=limit):
        if album_only:
            yield item['album']
        else:
            yield item


@yields('tracks')
def saved_tracks(max_results=None, track_only=False):
    """
    Yields saved track objects.
    {'track' full track, 'added_at': timestamp}
    If track_only==True, yield only track.
    """
    limit = get_limit(max_results, 50)
    for item in iterate_results(
            'current_user_saved_tracks',
            max_results=max_results,
            limit=limit):
        if track_only:
            yield item['track']
        else:
            yield item


@yields('artists')
def followed_artists(max_results=None):
    limit = get_limit(max_results, 50)
    yield from iterate_results(
        'current_user_followed_artists',
        items_path=['artists', 'items'],
        next_path=['artists', 'next'],
        max_results=max_results,
        limit=limit)


@yields('artists')
def saved_artists(max_results=None):
    """
    Return all artists from saved_albums,
    saved_tracks and followed_artists.
    Each unique artist is returned only once.
    """
    albums = saved_albums(album_only=True)
    tracks = saved_tracks(track_only=True)

    def artists_from_items(s):
        for item in s:
            for artist in item['artists']:
                yield artist

    artists = itertools.chain(
        artists_from_items(itertools.chain(albums, tracks)),
        followed_artists())

    used = set()
    for artist in artists:
        aid = artist['id']
        if max_results and len(used) >= max_results:
            return
        if aid in used:
            continue
        used.add(aid)
        yield artist


@yields('artists')
def user_top_artists(time_range='medium_term',
                     max_results=None):
    limit = get_limit(max_results, 50)
    yield from iterate_results(
        'current_user_top_artists',
        time_range=time_range,
        max_results=max_results,
        limit=limit)


@yields('artists')
def user_top_tracks(time_range='medium_term',
                    max_results=None):
    limit = get_limit(max_results, 50)
    yield from iterate_results(
        'current_user_top_tracks',
        time_range=time_range,
        max_results=max_results,
        limit=limit)


@infer_content
def library_filter_added_at(items, start=datetime.utcnow(),
                            end=datetime.utcnow()):
    for item in items:
        added = isodate.parse_datetime(item['added_at'])
        added = added.replace(tzinfo=None)

        if start <= added <= end:
            if 'track' in item:
                yield item['track']
            elif 'album' in item:
                yield item['album']
            else:
                yield item
