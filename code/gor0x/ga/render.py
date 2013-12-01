import random

import music21

from markov import MarkovChain
from model import artist_song_pair, cache_get, cache_set

MIDI_PATH = './midi_files'


def render_artist_pairs():
    """Return a mapping of artist to song for every artist/song pair in
    the redis list of artist pairs"""
    pairs = []
    for key in artist_song_pair():
        artist, song = key.split(':')
        pairs.append([artist, song])
    return pairs


def random_sampling(min, max, nt):
    """Return a starting index and a stopping index for a random
    consecutive sampling from a population"""
    start_idx = random.randrange(min, max)
    stop_idx = start_idx + nt
    if stop_idx > max:
        return random_sampling(min, max, nt)
    return start_idx, stop_idx


def render_individual(notes=None, _id=None, generation=None):
    return {
        'id': _id,
        'notes': notes,
        'generation': generation
    }


def render_population(**kwargs):
    """Kwargs contains size of initial population, size of individual,
    artist, and song, which are used to generate a markov chain
    """
    population = []
    mpath = map(kwargs.pop, ['artist', 'song'])
    path = "{}/{}/{}.mid".format(MIDI_PATH, *mpath)
    name = '{}:{}'.format(*mpath)
    _name = name + ":generation:{}".format(1)
    psize = kwargs['psize']
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

    # need to start at one to ensure ids and population size sync up
    for idx in range(1, psize + 1):
        _kwargs = kwargs.copy()
        _kwargs['_id'] = idx
        start, stop = random_sampling(1, len(markov), kwargs['isize'])
        notes = markov[start: stop]
        individual = render_individual(notes=notes, generation=1, _id=idx)
        print "indivudal is in RENDER POP  ", individual
        cache_set(_name, idx, individual, serialize=True)
        population.append(individual)
    return population


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

