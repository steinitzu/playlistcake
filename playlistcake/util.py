from collections import Iterable


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
