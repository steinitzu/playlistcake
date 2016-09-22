import itertools

import pytest
import requests_cache


class DumbConnection(object):
    def __init__(self, parent):
        self.parent = parent

    def close(self):
        self.parent.close()


class DumbCachedSession(requests_cache.CachedSession):
    """
    Spotipy calls connection.close() after an API request
    but regular CachedSession's response object doesn't
    have a connection attribute.
    Too dumb to figure it out so here's a hack ...
    """
    def send(self, request, **kwargs):
        response = super(DumbCachedSession, self).send(request, **kwargs)
        response.connection = DumbConnection(self)
        return response


@pytest.fixture(scope='session')
def spotify():
    import os
    from playlistcake import sessionenv
    from playlistcake import spotifystuff
    token = eval(os.getenv('PLAYLISTCAKE_TEST_TOKEN'))
    sessionenv.set('spotify_token', token)
    sessionenv.set('spotify_kwargs',
                   {'requests_session': DumbCachedSession()})
    return spotifystuff.get_spotify()


@pytest.fixture(scope='session')
def some_artists(spotify):
    from playlistcake.sources import find_artist
    artists = [
        find_artist('Tom Waits'),
        find_artist('The Beatles'),
        find_artist('Bright Eyes'),
        find_artist('Howlin Wolf'),
        find_artist('Led Zeppelin'),
        find_artist('Pink Floyd'),
        find_artist('Eels'),
        find_artist('The Who'),
        find_artist('Eminem'),
        find_artist('Rihanna'),
        find_artist('Jimi Hendrix'),
        find_artist('Aesop Rock'),
        find_artist('The Album Leaf'),
        find_artist('Ezra Furman'), ]
    return artists


@pytest.fixture(scope='session')
def some_albums(spotify):
    from playlistcake.sources import find_album
    albums = [
        find_album('Tom Waits', 'Swordfishtrombones'),  # 1983
        find_album('Ezra Furman', 'Day of the dog'),  # 2013
        find_album('Sonic Youth', 'Goo'),  # 1990
        find_album('The Beatles', 'Revolver'),  # 1966
        find_album('Eels', 'Shootenanny'),
        find_album('The Album Leaf', 'In a safe place'),
        find_album('Eminem', 'Relapse'), ]
    return albums


@pytest.fixture(scope='session')
def some_tracks(some_albums):
    from random import shuffle
    from playlistcake.sources import tracks_from_albums
    tracks = list(tracks_from_albums(some_albums))
    shuffle(tracks)
    return tracks


def test_sort_by_audio_feature(some_tracks):
    from playlistcake.sources import tracks_sort_by_audio_feature

    sortedt = list(tracks_sort_by_audio_feature(
        some_tracks, 'energy', order='asc'))

    for i, track in enumerate(sortedt):
        energy = track['audio_features']['energy']
        print('Track {}: energy:{}'.format(i, energy))
        if i == 0:
            continue
        prevtrack = sortedt[i-1]
        assert energy >= prevtrack['audio_features']['energy']


def test_sort_by_multiple(some_tracks):
    from playlistcake.sources import items_sorted_by_attributes
    sortedt = items_sorted_by_attributes(
        some_tracks,
        sort_func=lambda x: (x['artists'][0]['name'], x['popularity']))
    # sortedt = items_sorted_by_attributes(
    #     some_tracks,
    #     sort_func=lambda x: x['popularity'])
    sortedt = list(sortedt)
    for track in sortedt:
        print('{}:{} - {}'.format(
            track['popularity'], track['artists'][0]['name'], track['name']))
    assert 1==2


def test_filter_album_release_year(some_albums):
    import isodate
    from playlistcake.sources import albums_filter_release_year

    start, end = 1980, 1990
    filtered = list(albums_filter_release_year(
        some_albums, start=start, end=end))

    for album in some_albums:
        rdate = isodate.parse_date(album['release_date'])
        if start <= rdate.year <= end:
            assert album in filtered
        else:
            assert album not in filtered


def test_filter_tracks_release_year(some_tracks):
    import isodate
    from playlistcake.sources import (tracks_filter_release_year,
                                      full_album)

    start, end = 1980, 1990
    filtered = list(tracks_filter_release_year(
        some_tracks, start=start, end=end))

    for track in some_tracks:
        album = full_album(track['album']['id'])
        rdate = isodate.parse_date(album['release_date'])
        if start <= rdate.year <= end:
            assert track in filtered
        else:
            assert track not in filtered


def test_filter_artist_variety(some_tracks):
    from playlistcake.sources import (tracks_filter_artist_variety)

    filtered = list(tracks_filter_artist_variety(
        some_tracks, 1))
    seen_before = set()
    for track in filtered:
        aid = track['artists'][0]['id']
        assert aid not in seen_before
        seen_before.add(aid)

    filtered = list(tracks_filter_artist_variety(
        some_tracks, 3))
    seen_count = {}
    for track in filtered:
        aid = track['artists'][0]['id']
        if aid in seen_count:
            seen_count[aid] += 1
        else:
            seen_count[aid] = 1
        assert seen_count[aid] <= 3
    assert len(seen_count) > 0


def test_filter_unique(some_tracks):
    from playlistcake.sources import tracks_filter_unique
    t1 = some_tracks.copy()
    t2 = some_tracks.copy()
    tracks = t1 + t2
    filtered = list(tracks_filter_unique(tracks))
    assert len(filtered) == len(tracks)/2




def test_filter_audio_features(some_tracks):
    raise NotImplementedError


def test_decorators():
    from playlistcake import library, sources, filters
    from playlistcake.genutils import content_type
    artists = library.saved_artists()
    albums = sources.artists_albums(artists)
    tracks = sources.artists_top_tracks(artists, 1)
    assert content_type(artists) == 'artists'
    assert content_type(albums) == 'albums'
    assert content_type(tracks) == 'tracks'

    filtered = filters.filter_release_years(tracks)
    assert content_type(filtered) == 'tracks'
    filtered = filters.filter_release_years(albums)
    assert content_type(filtered) == 'albums'
