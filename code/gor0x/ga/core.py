import random
from operator import itemgetter

from model import cache_get, cache_set
from render import random_sampling, render_individual, generate_markov


from ..ga import logger


def m_pipe(val, *fns, **kwargs):
    """Utility function to pipe an infinite number of functions by passing
    the return value of the previous function as a parameter into the next function

    :param val: The initial parameter needed for the first function call
    :type val: An unknown Python object

    :returns: The output of the final function call
    :rtype: An unknown Python object
    """
    kw = kwargs
    _val = val
    for fn in fns:
        _val = fn(val, **kw)
    return _val


def begin_ga(key):
    """Runs the genetic algorithm `pipeline`, i.e. generates the next generation
    by running genetic operators on the current generation.

    This pipeline includes
        -Tournament selection
        -Single point crossover
        -Mutation

    :param key: The base key of the population
    :type key: String

    :returns: The value of the next generation
    :rtype: Integer
    """
    _population = cache_get(key)
    population = [_population[idx] for idx in _population]
    base_key = cache_get('settings')['base_key']
    next_generation = population[0]['generation'] + 1
    name = '{}:{}'.format(base_key, next_generation)

    # need to convert the population dictionary to a tuple of tuples so we can
    # take the set of it. even though notes are a list of lists, python throws
    # and unhasable error if everything isnt of the same type
    for individual in population:
        individual['notes'] = tuple(tuple(x) for x in individual['notes'])

    _future_population = m_pipe(population, tournament, crossover, mutation)
    for idx, notes in enumerate(_future_population, start=1):
        individual = render_individual(notes=notes, _id=idx, generation=next_generation)
        logger.debug("Individual << %s >> for generation << %s >>:\n%s", idx, next_generation, individual)
        cache_set(name, idx, individual, serialize=True)
    return next_generation


def crossover(population, kw=None, **kwargs):
    """Single point crossover

    NEED `kw` argument due to python bug which strips out named parameters
    from **kwargs. `kw` is to ensure we don't lose anything!

    :param population: The population
    :type population: List

    :returns: The next generation of individuals
    :rtype: List
    """
    future_population = []
    while len(future_population) < len(population):
        p1, p2 = random.choice(population)['notes'], random.choice(population)['notes']
        split = random.randint(1, len(p1) - 1)
        map(future_population.append, [p1[:split] + p2[split:], p2[:split] + p1[split:]])
    return future_population


def tournament(population, k=3, elitism=0, kw=None, **kwargs):
    """Tournament based selection. We avoid selecting the same winner multiple
    times by immediately taking the set of the pool after an individual is added to it

    NEED `kw` argument due to python bug which strips out named parameters
    from **kwargs. `kw` is to ensure we don't lose anything!

    :param population: The population
    :type population: List

    :returns: The pool of individuals that were `selected` for crossover
    :rtype: List
    """
    _population = sorted(population, reverse=True, key=itemgetter('fitness'))

    # pop off the N best individuals where N is elitism
    pool = map(_population.pop, [0] * elitism)

    # update the value of k to reflect the elitism count
    _k = min(k, len(_population)) + elitism

    while len(pool) < _k:
        pool.append(random.choice(_population))
        pool = [dict(t) for t in set([tuple(d.items()) for d in pool])]
    return sorted(pool, key=lambda x: x['fitness'], reverse=True)


def mutation(population, m_rate=.5, kw=None, **kwargs):
    """This mutation process mutates random subsets of an individuals chromosome

    NEED `kw` argument due to python bug which strips out named parameters
    from **kwargs. `kw` is to ensure we don't lose anything!

    :param population: The population
    :type population: List

    :returns: The population with mutated individuals
    :rtype: List
    """
    _population = []
    for individual in population:
        rnd_rate = random.uniform(0, 1)
        if rnd_rate > m_rate:
            logger.debug("Mutating Individual!\nRandom rate is: %s\nM Rate is: %s", rnd_rate, m_rate)
            split_point = random.randint(1, len(individual['notes']) - 1)
            start, stop = random_sampling(0, len(individual['notes']), split_point)

            # generate a new corpus via cached markov chain
            settings = cache_get('settings')
            key = "{}:{}".format(settings['artist'], settings['song'])
            new_corpus = cache_get(key)['markov'][start:stop]
            logger.debug("New corpus is %s", new_corpus)

            # tuples are immuteable so we need to remake the tuple of notes/chords
            individual['notes'] = individual['notes'][:start] + tuple(map(tuple, new_corpus)) + individual['notes'][stop:]
            _population.append(individual['notes'])
        else:
            logger.debug("Not mutating\nRandom rate is: %s\nM Rate is: %s", rnd_rate, m_rate)
            _population.append(individual['notes'])
    return _population


def export_phenotype(chords):
    """This does not work correctly at the moment!"""
    import music21
    partupper = music21.stream.Part()
    m = music21.stream.Measure()
    for _chord in chords:
        c = music21.chord.Chord(_chord)
        m.append(c)
    partupper.append(m)
    partupper.write('midi', './sample.mid')
