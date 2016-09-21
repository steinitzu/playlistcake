from .spotifystuff import iterate_results
from .util import get_id, get_ids, get_limit
from .genutils import content


def generate_seeds(objects, seed_size=5):
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


@content('tracks')
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


@content('tracks')
def batch_recommendations(seed_gen=(),
                          seed_gen_type='artist',
                          suppl_artists=(),
                          suppl_tracks=(),
                          seed_genres=(),
                          max_results=None,
                          max_per_seed=50,
                          **tuneables):
    """
    Provided a seed generator object (like the
    one returned by `items_to_seeds`, yields
    recommendations based on those seeds + any
    static seeds provided (artists/tracks/genres)

    seed_gen: A seed generator (like returned by `items to seeds`)
    seed_gen_type: The type of seeds yielded by seed_gen (
                   'artist' or 'track')
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
    if seed_gen_type not in ('artist', 'track'):
        raise ValueError('Invalid seed_gen_type, use "artist" or "track"')
    result_count = 0
    for seed in seed_gen:
        seed_artists = []
        seed_tracks = []
        if seed_gen_type == 'artist':
            seed_artists += seed
        elif seed_gen_type == 'track':
            seed_tracks += seed
        seed_artists += get_ids(suppl_artists)
        seed_tracks += get_ids(suppl_tracks)
        for track in recommendations(
                seed_artists=seed_artists,
                seed_tracks=seed_tracks,
                seed_genres=seed_genres,
                max_results=max_per_seed,
                **tuneables):
            yield track
            result_count += 1
        if max_results and result_count >= max_results:
            return
