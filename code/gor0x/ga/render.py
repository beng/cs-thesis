import random

import music21

from markov import MarkovChain
from model import artist_song_pair, cache_get, cache_set

MIDI_PATH = '../../bin/midi'


def render_artist_pairs():
    """Return a mapping of artist to song for every artist/song pair in
    the redis list of artist pairs

    :returns: Artist, song pair
    :rtype: List of lists
    """
    pairs = []
    for key in artist_song_pair():
        artist, song = key.split(':')
        pairs.append([artist, song])
    return pairs


def random_sampling(min, max, nt):
    """Return a starting index and a stopping index for a random
    consecutive sampling from a population

    :param min: Minimum number
    :type min: Integer

    :param max: Maximum number
    :type max: Integer

    :param nt: (Number of traits), i.e. the size of the list we are sampling
    :type nt: Integer

    :returns: Start and stop indices
    :rtype: Tuple of ints
    """
    start_idx = random.randrange(min, max)
    stop_idx = start_idx + nt
    if stop_idx > max:
        return random_sampling(min, max, nt)
    return start_idx, stop_idx


def render_individual(notes=None, _id=None, generation=None):
    """Renders an individual so it can be cached in Redis

    :param notes: Notes/chords for the individual
    :type notes: List

    :param _id: The individual's ID
    :type _id: Integer

    :param _generation: The generation the individual is part of
    :type _generation: Integer

    :returns: A dictionary representing an individual
    :rtype: Dictionary
    """
    return {
        'id': _id,
        'notes': notes,
        'generation': generation,
        'fitness': 0
    }


def render_population(**kwargs):
    """Generates an initial population based on the user's preferences

    `Kwargs` contains:
        `psize`: Size of initial population
        `isize`: Size of individual (how many notes/chords to make)
        `artist`: What artist to use
        `song`: What song to use
        `mcsize`: Size of Markov chain
        `mcnodes`: Markov chain node history

    :param kwargs: The initialization settings for the GA
    :type kwargs: Dictionary

    :returns: The newly created population
    :rtype: List
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
    """Generate a Music21 object out of a MIDI file

    :param path: The path to the MIDI file
    :type path: String

    :returns: Music21 object
    :rtype: Music21
    """
    return music21.converter.parse(path)


def parse(mobj, traits=['chord'], **kwargs):
    """Given a music21 object and a list of traits,
    extract those traits from the music21 object, while:
        -preserving order
        -keeping a nested list of each trait(s) due to chords
            >> [[A4], [B5], [B5, C#4, F#3]]

    :param mobj: Music21 object
    :type mobj: Music21

    :param traits: List of characteristics to extract from the Music21 object
    :type traits: List

    :returns: A list of chords/pitches
    :rtype: List
    """
    _mobj = filter(lambda x: type(x).__name__.lower() in traits, mobj.recurse())
    elements = [[pitch for pitch in element.pitches] for element in _mobj]
    return map(lambda pitches: map(lambda pitch: pitch.nameWithOctave, pitches), elements)


def generate_markov(corpus, mc_size=None, mc_nodes=None, **kwargs):
    """Generates the Markov chain for a corpus

    :param corpus: The corpus for the Markov chain
    :type corpus: String

    :param mc_size: Size of the Markov chain
    :type mc_size: Integer

    :param mc_nodes: Markov chain node history
    :type mc_nodes: Integer

    :returns: A Markov chain
    :rtype: List
    """
    def markov_pitch():
        # we use `:` to denote grouping of pairs, ie chords, individual notes
        # we use `(empty space)` to denote separation between groupings
        return ' '.join([next(walk_corpus()) for k in xrange(mc_size)]).split(':')

    def walk_corpus():
        chain = MarkovChain(mc_nodes)
        chain.add_sequence(corpus)
        return chain.walk()

    return map(lambda x: x.split(' '), markov_pitch())
