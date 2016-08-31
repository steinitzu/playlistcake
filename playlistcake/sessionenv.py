SESSION = {}


def set(key, value):
    SESSION[key] = value


def get(key, default=None):
    return SESSION.get(key, default)
