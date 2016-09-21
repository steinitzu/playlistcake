import weakref

item_types = weakref.WeakKeyDictionary()


def yields(genobj):
    return item_types[genobj]


def content(item_type):
    def decorator(func):
        def func_wrapper(*args, **kwargs):
            gen = func(*args, **kwargs)
            item_types[gen] = item_type
            return gen
        return func_wrapper
    return decorator


def parent_content():
    def decorator(func):
        def func_wrapper(*args, **kwargs):
            # First arg should be parent generator (items)
            item_type = yields(args[0])
            gen = func(*args, **kwargs)
            item_types[gen] = item_type
            return gen
        return func_wrapper
    return decorator
