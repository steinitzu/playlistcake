SECRET_KEY = 'v38j8cmdk0aw9asidnsdajd2d'

auth_scopes = [
    'user-library-read',
    'user-top-read',
    'user-follow-read',
    'playlist-modify-public',
    'user-read-private'
    ]

SPOTIFY_AUTHORIZATION_SCOPE = ' '.join(auth_scopes)
