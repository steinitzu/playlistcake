from collections import Iterable
import random


def get_ids(objects):
    l = [o['id'] if isinstance(o, dict) else o
         for o in objects]
    return l


def get_id(item):
    return item['id'] if isinstance(item, dict) else item


def get_limit(max_results, max_limit):
    if max_results and max_results < max_limit:
        limit = max_results
    else:
        limit = max_limit
    return limit


def is_iterable(obj):
    """
    Check whether obj is iterable and NOT a string.
    """
    if isinstance(obj, Iterable):
        if isinstance(obj, str):
            return False
        else:
            return True
    else:
        return False


def dict_get_nested(key, dict_):
    """
    Pass a key or a list of keys to get
    items from a nested dict.
    """
    if not is_iterable(key):
        return dict_[key]
    for k in key:
        if k is None:
            continue
        dict_ = dict_[k]
    return dict_


def iter_chunked(iterator, n):
    """
    Effectively splits generator into n sized chunks.
    Yields a list of n items from the generator.
    Last chunk yielded may have len <= n.
    """
    chunk = []
    for item in iterator:
        chunk.append(item)
        if len(chunk) == n:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def reservoir_sample(source, n):
    """
    Yield n randomally selected items
    from source.
    """
    result = []
    for i, item in enumerate(source):
        if len(result) < n:
            result.append(item)
        else:
            r = random.randint(0, i)
            if r < n:
                result[r] = item
    yield from result
