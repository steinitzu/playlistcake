from . import sessionenv
from . import plugins


def generate_playlist(spotify_token):
    sessionenv.set('spotify_token', spotify_token)
    # p = plugins.SingleArtistSource(name='Eels')
    # print('what', p)

    a_source = plugins.SavedAlbumArtistSource(max_results=20)
    attrs = [plugins.AudioAttributeFilter('min_acousticness', '0.9'),
             plugins.AudioAttributeFilter('max_popularity', '0.6')]
    recs = []
    result = []
    for a in a_source:
        result.append(a['name'])
    #     recs.append(plugins.RecommendationsSource(
    #         seed_artists=[a], audio_attribute_filters=attrs, max_results=5))
    # result = []
    # for r in recs:
    #     for track in r:
    #         result.append(track)
    # return result
    return str(len(result))
