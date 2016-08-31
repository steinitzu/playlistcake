from .util import dict_get_nested
from .spotifystuff import get_spotify


TUNEABLE_ATTRIBUTES = [
    'acousticness',
    'danceability',
    'duration_ms',
    'energy',
    'instrumentalness',
    'key',
    'liveness',
    'loudness',
    'mode',
    'popularity',
    'speechiness',
    'tempo',
    'time_signature',
    'valence',
]


def single_result(endpoint, *args, **kwargs):
    sp = get_spotify()
    func = getattr(sp, endpoint)
    result = func(*args, **kwargs)
    return iter([result])


def iterate_results(endpoint, *args, **kwargs):
    sp = get_spotify()
    func = getattr(sp, endpoint)
    # try:
    #     single_result = kwargs.pop('single_result')
    # except KeyError:
    #     single_result = False
    target_key = kwargs.pop('target_key', 'items')
    next_key = kwargs.pop('next_key', 'next')
    max_results = kwargs.pop('max_results', None)

    result = func(*args, **kwargs)
    # if single_result:
    #     return iter([result])
    count = 0
    while True:
        if target_key:
            itemlist = dict_get_nested(target_key, result)
        else:
            itemlist = result
        for item in itemlist:
            if max_results and count >= max_results:
                break
            count += 1
            yield item
        if max_results and count >= max_results:
            break
        if next_key:
            try:
                next_url = dict_get_nested(next_key, result)
            except KeyError:
                break
        else:
            next_url = None
        if next_url:
            result = sp._get(next_url)
        else:
            break


""""
Plugin types:

artist_source:
------------------
provides one or more artist

track_source:
------------------
provides one or more track

filter
------------------
filters results from track sources
"""


class Source(object):
    endpoint = None
    target_key = None
    next_key = None
    single_result = False

    def __init__(self, *args, **kwargs):
        try:
            self.fetch_kwargs = kwargs.pop('fetch_kwargs', {})
        except KeyError:
            self.fetch_kwargs = {}
        self.fetch_kwargs.update(kwargs)
        self._data = None

    def __iter__(self):
        if not self._data:
            self.fetch()
        yield from self._data

    def __next__(self):
        return next(iter(self))

    def fetch(self):
        if self.single_result:
            self._data = single_result(
                endpoint=self.endpoint,
                **self.fetch_kwargs)
        else:
            self._data = iterate_results(
                endpoint=self.endpoint,
                target_key=self.target_key,
                next_key=self.next_key,
                **self.fetch_kwargs)


class ArtistSource(Source):
    pass


class SingleArtistSource(ArtistSource):
    endpoint = 'artist'
    single_result = True

    def __init__(self, name=None, uri=None, **kwargs):
        if not name and not uri:
            raise ValueError('Either name or uri required')
        # TODO: iterate_results for a single source
        if not uri:
            uri = next(
                iterate_results('search',
                                name,
                                target_key=['artists', 'items'],
                                limit=1,
                                type='artist'))['uri']
        ArtistSource.__init__(self, fetch_kwargs={'artist_id': uri}, **kwargs)


class FollowedArtistSource(ArtistSource):
    endpoint = 'current_user_followed_artists'
    target_key = ['artists', 'items']
    next_key = ['artists', 'next']

    def __init__(self, **kwargs):
        kwargs['limit'] = 50
        ArtistSource.__init__(self, **kwargs)


class SavedAlbumArtistSource(ArtistSource):
    """
    Returns all artists from a user's saved albums.
    """
    def __init__(self, **kwargs):
        ArtistSource.__init__(self, **kwargs)

    def _get_album_artists(self):
        # Temporarily pluck max results out of fetch_kwargs
        # so it isn't applied to albums fetch
        try:
            max_results = self.fetch_kwargs.pop('max_results')
        except KeyError:
            max_results = None
        albums = iterate_results('current_user_saved_albums',
                                 limit=50,
                                 **self.fetch_kwargs)
        self.fetch_kwargs['max_results'] = max_results
        done = set()
        for album in albums:
            for artist in album['album']['artists']:
                if max_results and len(done) >= max_results:
                    break
                if artist['uri'] in done:
                    continue
                done.add(artist['uri'])
                yield artist

    def fetch(self):
        self._data = self._get_album_artists()


class TrackSource(Source):
    pass


class SingleTrackSource(TrackSource):
    """
    Provides a single track given a track uri or id.
    """
    endpoint = 'track'
    single_result = True

    def __init__(self, uri, **kwargs):
        self.uri = uri
        super(SingleTrackSource, self).__init__(
            fetch_kwargs={'track_id': self.uri})


class AlbumSource(TrackSource):
    """
    Provides tracks from a single album
    given album uri
    """
    endpoint = 'album'
    target_key = ['tracks', 'items']

    def __init__(self, uri=None, artist=None, album_name=None, **kwargs):
        if not uri and not artist and not album_name:
            raise ValueError(
                'Must provide uri or artist+album_name combination')
        if not uri:
            uri = next(
                iterate_results('search',
                                'artist:{} album:{}'.format(
                                    artist, album_name),
                                target_key=['albums', 'items'],
                                limit=1,
                                type='album'))['uri']
        TrackSource.__init__(self, fetch_kwargs={'album_id': uri}, **kwargs)


class RecommendationsSource(TrackSource):
    """
    Recommendations API accepts up to 5 seed values
    of combined seed_artists, seed_tracks and seed_genres.
    """
    endpoint = 'recommendations'
    target_key = 'tracks'

    def __init__(self, seed_artists=[], seed_tracks=[],
                 seed_genres=[], audio_attribute_filters=[],
                 **kwargs):
        self.seed_artists = [a['uri'] if isinstance(a, dict) else a
                             for a in seed_artists]
        self.seed_tracks = [a['uri'] if isinstance(a, dict) else a
                            for a in seed_tracks]
        self.seed_genres = seed_genres
        self.tuneables = {a.attribute: a.value
                          for a in audio_attribute_filters}

        seed_len = len(seed_artists + seed_tracks + seed_genres)
        if seed_len > 5:
            raise ValueError(
                'Too many seeds, maximum of 5 total seeds allowed.')
        fetch_kwargs = {'seed_artists': self.seed_artists,
                        'seed_tracks': self.seed_tracks,
                        'seed_genres': self.seed_genres}
        fetch_kwargs.update(self.tuneables)
        fetch_kwargs.update(kwargs)
        fetch_kwargs['limit'] = 50

        TrackSource.__init__(self, fetch_kwargs=fetch_kwargs)


class Filter(object):
    pass


class GenreFilter(Filter):
    def __init__(self, genre):
        self.genre = genre


class AudioAttributeFilter(Filter):
    def __init__(self, attribute, value):
        self.attribute = attribute.lower()
        self.value = value

    def __str__(self):
        return 'AudioAttributeFilter:{}:{}'.format(
            self.attribute, self.value)


class TracksToAudioAttributeFilters(Source):
    """
    Given up to a 100 tracks, returns lists of
    AudioAttributeFilter objects.
    """
    endpoint = 'audio_features'

    def __init__(self, tracks=[]):
        tracks = [track['uri'] if isinstance(track, dict) else track
                  for track in tracks]
        super(TracksToAudioAttributeFilters, self).__init__(
            self, fetch_kwargs={'tracks': tracks})

    def __iter__(self):
        sup = super(TracksToAudioAttributeFilters, self).__iter__()
        for item in sup:
            result = []
            for key, value in item.items():
                if key in TUNEABLE_ATTRIBUTES:
                    result.append(AudioAttributeFilter(
                        'target_'+key, value))
                yield result


class PlaylistBuilder(object):

    def __init__(self):
        self.plugins = []

    def add_plugin(self, plugin):
        self.plugins.append(plugin)

    def run(self):
        for plugin in plugins:
            pass
