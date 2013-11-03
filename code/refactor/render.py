import pickle
import random

import music21
from redis import Redis

from markov import MarkovChain


r = Redis(db=2)
MIDI_PATH = './midi_files'


def random_sampling(min, max, nt):
    """Return a starting index and a stopping index for a random
    consecutive sampling from a population"""
    start_idx = random.randrange(min, max)
    stop_idx = start_idx + nt

    if stop_idx > max:
        return random_sampling(min, max, nt)
    return start_idx, stop_idx


def render_individual(markov, tsize=None, isize=None, psize=None, **kwargs):
    population = []
    for idx, x in enumerate(range(psize)):
        start, stop = random_sampling(1, len(markov), isize)
        population.append({
            'generation': 0,
            'id': idx,
            'note': markov[start:stop]
        })
    return population

def render_population(**kwargs):
    """Kwargs contains size of initial population, size of individual,
    artist, and song, which are used to generate a markov chain
    """
    mpath = map(kwargs.pop, ['artist', 'song'])
    path = "{}/{}/{}.mid".format(MIDI_PATH, *mpath)
    name = '{}:{}'.format(*mpath)
    notes = cache_get(name).get('original_notes')
    if not notes:
        print "cache not set. parsing music object and saving to redis"
        mobj = music_obj(path)
        notes = parse(mobj, **kwargs)
        print "setting cache of original notes"
        cache_set(name, 'original_notes', notes, serialize=True)
    markov = generate_markov(notes, **kwargs)
    print "caching markov"
    cache_set(name, 'markov', markov, serialize=True)
    return render_individual(markov, **kwargs)


def music_obj(path):
    return music21.converter.parse(path)


def parse(mobj, traits=['chord'], **kwargs):
    """Given a music21 object and a list of traits,
    extract those traits from the music21 object, while:
        -preserving order
        -keeping a nested list of each trait(s) due to chords
            >>> [[A4], [B5], [B5, C#4, F#3]]
    """
    _mobj = filter(lambda x: type(x).__name__.lower() in traits, mobj.recurse())
    elements = [[pitch for pitch in element.pitches] for element in _mobj]
    return map(lambda pitches: map(lambda pitch: pitch.nameWithOctave, pitches) , elements)


def generate_markov(corpus, mc_size=None, mc_nodes=None, **kwargs):
    def markov_pitch():
        # we use `:` to denote grouping of pairs, ie chords, individual notes
        # we use `(empty space)` to denote separation between groupings
        return ' '.join([next(walk_corpus()) for k in xrange(mc_size)]).split(':')

    def walk_corpus():
        chain = MarkovChain(mc_nodes)
        chain.add_sequence(corpus)
        return chain.walk()

    return map(lambda x: x.split(' '), markov_pitch())


def cache_set(name, key, value, serialize=None):
    if serialize:
        value = pickle.dumps(value)
    return r.hset(name, key, value)


def cache_get(name):
    cache = r.hgetall(name)
    mapping = {}
    for k, v in cache.items():
        try:
            mapping[k] = pickle.loads(v)
        except Exception:
            print "can de-pickle, loading as is"
            mapping[k] = v
    return mapping

