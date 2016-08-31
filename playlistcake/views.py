import os

from flask import session, redirect, url_for, request

from . import app
from .spotifystuff import get_spotify_oauth
from .generator import generate_playlist


@app.route('/')
def index():
    return 'hello'


@app.route('/app_authorize')
def app_authorize():
    token = session.get('spotify_token')
    if token:
        return redirect(url_for('app_start'))
    else:
        auth = get_spotify_oauth()
        auth_url = auth.get_authorize_url()
        return redirect(auth_url)


# Spotify oauth callback url
@app.route('/callback')
def callback():
    """
    The spotify redirect uri should lead here.
    Get an access_token and add it to session.
    """
    auth = get_spotify_oauth()
    code = auth.parse_response_code(request.url)
    token = auth.get_access_token(code)
    session['spotify_token'] = token
    return redirect(url_for('app_authorize'))


@app.route('/app_start')
def app_start():
    if not session.get('spotify_token'):
        return redirect(url_for('app_authorize'))
    return redirect(url_for('playlist_generator',))


@app.route('/playlist_generator')
def playlist_generator():
    g = generate_playlist(session.get('spotify_token'))
    print(session.get('spotify_token'))
    return g
    # print(len(g))
    # return '<br>'.join([x['name'] for x in g])
