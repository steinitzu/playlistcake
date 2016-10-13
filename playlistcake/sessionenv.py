import threading

session = threading.local()
session.data = {}


def set(key, value):
    session.data[key] = value


def get(key, default=None):
    return session.data.get(key, default)
