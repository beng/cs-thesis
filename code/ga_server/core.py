from collections import defaultdict
from itertools import chain

import requests
from model import Cache
from redis import Redis

from config import REST_SERVER


class RestServer(object):
    """Interface for querying REST server"""

    def __init__(self, path):
        self.path = path

    def request(self, **kwargs):
        url = REST_SERVER + self.path
        req = requests.get(url, params=kwargs)
        return req.json()


class GAInitialization(object):
    def __init__(self, *args, **kwargs):
        self.cache = Cache()

    def reset_ga(self):
        return self.cache.delete('init:settings')

    def user_property(self, name):
        """Return the value for the requested property"""
        return self.cache.hget('init:settings', name)

    def save_properties(self, settings):
        return self.cache.hmset('init:settings', settings)

    def music_collection(self, pattern):
        """Return dict of songs for requested artist(s)"""
        keys = self.cache.keys(pattern=pattern)
        listings = defaultdict(list)
        for key in keys:
            artist = key.split(':')[-1]
            songs = self.cache.smembers(key)
            listings[artist].append(songs)
        return listings
