from .spotify import iterate_results
from .util import get_id, get_ids, get_limit
from .genutils import yields, content_type


def _generate_seeds(objects, seed_size=5):
    """
    Convenience method to chunk iterables of artist or track
    object into lists of `seed_size` length of item ids.
    Has the added bonus of guaranteeing each item appears only
    once in the resulting set of seeds.
    """
    if seed_size > 5 or seed_size < 1:
        raise ValueError('Seed size must be between 1 and 5')
    been_used = set()
    chunk = []
    for item in objects:
        iid = get_id(item)
        if iid in been_used:
            continue
        been_used.add(iid)
        chunk.append(iid)
        if len(chunk) == seed_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


@yields('tracks')
def recommendations(seed_artists=(),
                    seed_tracks=(),
                    seed_genres=(),
                    max_results=50,
                    **tuneables):
    limit = get_limit(max_results, 50)
    yield from iterate_results(
        'recommendations',
        items_path='tracks',
        seed_artists=seed_artists,
        seed_tracks=seed_tracks,
        seed_genres=seed_genres,
        max_results=max_results,
        limit=limit,
        **tuneables)


@yields('tracks')
def batch_recommendations(seed_gen=None, seed_size=5,
                          suppl_artists=(),
                          suppl_tracks=(),
                          seed_genres=(),
                          max_results=None,
                          max_per_seed=50,
                          **tuneables):
    """
    Gets recommendations using artists or tracks from
    a generator. Unique seeds are created from generator
    by splitting it up into `seed_size` sized chunks.

    seed_gen: A generator with content_type of 'tracks' or 'artists'
    seed_size: the number of items from seed_gen to use for
               each iteration
    suppl_artists: list of artist ids to supplement each
                  iteration of seed_gen
    suppl_tracks: list of track ids to supplement each
                  iteration of seed_ge
    seed_genres: list of genres to supplement each
                  iteration of seed_gen
    max_results: total maximum results
    limit: max number of tracks per seed_gen iteration
    **tuneables: any number of tuneable audio attributes
    """
    seed_type = content_type(seed_gen)
    result_count = 0
    for seed in _generate_seeds(seed_gen, seed_size):
        seed_artists = []
        seed_tracks = []
        if seed_type == 'artists':
            seed_artists += get_ids(seed)
        elif seed_type == 'tracks':
            seed_tracks += get_ids(seed)
        seed_artists += get_ids(suppl_artists)
        seed_tracks += get_ids(suppl_tracks)
        recs = recommendations(seed_artists=seed_artists,
                               seed_tracks=seed_tracks,
                               seed_genres=seed_genres,
                               max_results=max_per_seed,
                               **tuneables)
        for track in recs:
            yield track
            result_count += 1
        if max_results and result_count >= max_results:
            return


@yields('albums')
def recommended_albums(seed_gen=None, seed_size=5,
                       suppl_artists=(),
                       suppl_tracks=(),
                       seed_genres=(),
                       max_results=None,
                       **tuneables):
    batch = batch_recommendations(
        seed_gen, seed_size,
        suppl_artists, suppl_tracks,
        seed_genres,
        **tuneables)
    seen = set()
    for track in batch:
        if max_results and len(seen) >= max_results:
            return
        album = track['album']
        if album['id'] in seen:
            continue
        seen.add(album['id'])
        yield album
