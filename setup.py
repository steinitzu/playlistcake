from setuptools import setup

setup(
    name='playlistcake',
    version='0.1.0.0',
    description='Spotify playlist generation library',
    author="Steinthor Palsson",
    author_email="steini90@gmail.com",
    url='',
    install_requires=[
        'isodate==0.5.4',
        'requests==2.11.1',
        'spotipy==2.3.8'],
    license='LICENSE.md',
    packages=['playlistcake'])
