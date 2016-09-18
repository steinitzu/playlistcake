import os

from playlistcake import sessionenv
from playlistcake.spotifystuff import get_spotify

token = eval(os.getenv('PLAYLISTCAKE_TEST_TOKEN'))
sessionenv.set('spotify_token', token)
