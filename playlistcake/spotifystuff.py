import os
import time

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify

from . import app
from . import sessionenv
from .util import dict_get_nested


def _monkey_search(self, q, limit=10, offset=0, type='track', market=None):
    return self._get('search',
                     q=q, limit=limit, offset=offset, type=type, market=market)

Spotify.search = _monkey_search


class ExtendedOAuth(SpotifyOAuth):
    def __init__(self, *args, **kwargs):
        SpotifyOAuth.__init__(self, *args, **kwargs)
        self.token_info = None

    def get_access_token(self, code):
        """
        Overrides get_access_token to store
        the token in an instance variable after creation.
        """
        self.token_info = SpotifyOAuth.get_access_token(
            self, code)
        return self.token_info

    def get_stored_token(self):
        """
        Get self.token_info, refreshing the token if needed.
        """
        is_expired = self._is_token_expired(self.token_info)
        if self.token_info:
            if is_expired:
                self.token_info = self._refresh_access_token(
                    self.token_info['refresh_token'])
            return self.token_infon


def get_spotify_oauth():
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
    auth = ExtendedOAuth(
        client_id, client_secret, redirect_uri,
        scope=app.config['SPOTIFY_AUTHORIZATION_SCOPE'])
    return auth


def token_is_expired(token):
    return token['expires_at'] < time.time()


def token_is_almost_expired(token):
    return token['expires_at'] < time.time()+600


def refresh_token(token):
    if token_is_expired(token) or token_is_almost_expired(token):
        auth = get_spotify_oauth()
        return auth._refresh_access_token(token['refresh_token'])
    else:
        return token


def get_spotify():
    token = sessionenv.get('spotify_token')
    kwargs = sessionenv.get('spotify_kwargs', {})
    try:
        sessj = kwargs.pop('requests_session')
    except KeyError:
        sessj = None
    if not token:
        raise Exception('No spotify token, abort')
    token = refresh_token(token)
    s = sessionenv.get('spotify')
    if s:
        s._auth = token['access_token']
    else:
        s = Spotify(auth=token['access_token'], **kwargs)
    if sessj:
        s._session = sessj
    #s.trace = True
    s.trace_out = True
    return s


def iterate_results(endpoint, *args, **kwargs):
    s = get_spotify()
    func = getattr(s, endpoint)
    # The path to the result's list of items to be yielded
    items_path = kwargs.pop('items_path', 'items')
    # The path in result dict to the "next" url (usually result['next'])
    next_path = kwargs.pop('next_path', 'next')
    max_results = kwargs.pop('max_results',  None)

    result = func(*args, **kwargs)
    count = 0
    while True:
        if items_path:
            itemlist = dict_get_nested(items_path, result)
        else:
            itemlist = result
        for item in itemlist:
            if max_results and count >= max_results:
                return
            count += 1
            yield item
        if next_path:
            try:
                next_url = dict_get_nested(next_path, result)
            except KeyError:
                return
            if not next_url:
                return
            result = s._get(next_url)
        else:
            return
