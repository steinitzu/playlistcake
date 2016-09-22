"""
This module is for adding and keeping track of faux attributes
on generator objects.
"""

from functools import wraps
import weakref

content_types = weakref.WeakKeyDictionary()


def content_type(genobj):
    """
    Returns the stored content type of
    given generator.
    """
    return content_types[genobj]


def yields(item_type):
    """
    Set the content type of a generator function.
    """
    def decorator(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            gen = func(*args, **kwargs)
            item_types[gen] = item_type
            return gen
        return func_wrapper
    return decorator


def infer_content(func):
    """
    Infers the content_type of the generator
    passed as first argument to the function.
    """
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        # First arg should be parent generator (items)
        item_type = content_type(args[0])
        gen = func(*args, **kwargs)
        item_types[gen] = item_type
        return gen
    return func_wrapper
