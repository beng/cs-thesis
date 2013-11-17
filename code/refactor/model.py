import pickle

from redis import Redis

r = Redis(db=2)


def clear_cache():
    """Deletes everything in cache except the music 21 object"""
    map(r.delete, filter(lambda key: ':generation' in key or 'settings' in key, r.keys()))


def cache_set(name, key, value, serialize=None):
    if serialize:
        value = pickle.dumps(value)
    return r.hset(name, key, value)


def cache_hmset(name, mapping, serialize=None):
    return r.hmset(name, mapping)


def cache_get(name):
    cache = r.hgetall(name)
    mapping = {}
    for k, v in cache.items():
        try:
            mapping[k] = pickle.loads(v)
        except Exception:
            mapping[k] = v
    return mapping
