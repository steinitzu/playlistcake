import os

from playlistcake import sessionenv

token = eval(os.getenv('PLAYLISTCAKE_TEST_TOKEN'))
sessionenv.set('spotify_token', token)
