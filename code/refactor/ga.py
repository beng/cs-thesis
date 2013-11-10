import random
from operator import itemgetter

from render import random_sampling, cache_get, cache_set, cache_hmset, render_individual


def m_pipe(val, *fns, **kwargs):
    kw = kwargs
    _val = val
    for fn in fns:
        _val = fn(val, **kw)
    return _val


def begin_ga(key):
    _population = cache_get(key)
    population = [_population[idx] for idx in _population]
    future_population = []
    base_key = cache_get('settings')['base_key']
    next_generation = population[0]['generation'] + 1
    name = '{}:{}'.format(base_key, next_generation)

    # need to convert the population dictionary to a tuple of tuples so we can
    # take the set of it. even though notes are a list of lists, python throws
    # and unhasable error if everything isnt of the same type
    for individual in population:
        individual['notes'] = tuple(tuple(x) for x in individual['notes'])

    _future_population = m_pipe(population, tournament, crossover)
    for idx, notes in enumerate(_future_population, start=1):
        individual = render_individual(notes=notes, _id=idx, generation=next_generation)
        cache_set(name, idx, individual, serialize=True)
        future_population.append(individual)
    return next_generation


# def crossover(p1, p2):
def crossover(population, kw=None, **kwargs):
    """Single point crossover

    NEED `kw` arugment due to python bug which strips out named parameters
    from **kwargs. `kw` is to ensure we don't lose anything!
    """
    future_population = []
    while len(future_population) < len(population):
        p1, p2 = random.choice(population)['notes'], random.choice(population)['notes']
        split = random.randint(1, len(p1))
        map(future_population.append, [p1[:split] + p2[split:], p2[:split] + p1[split:]])
    return future_population


def tournament(population, k=3, elitism=2, kw=None, **kwargs):
    """Avoid selecting the same winner multiple times by filtering out
    the pool immediately after we add to it

    NEED `kw` arugment due to python bug which strips out named parameters
    from **kwargs. `kw` is to ensure we don't lose anything!
    """
    _population = sorted(population, reverse=True, key=itemgetter('fitness'))
    # print "sorted pop is ", _population
    pool = map(_population.pop, [0] * elitism)
    _k = min(k, len(_population)) + elitism
    while len(pool) < _k:
        pool.append(random.choice(_population))
        # print "pool is ", pool
        pool = [dict(t) for t in set([tuple(d.items()) for d in pool])]
    return sorted(pool, key=lambda x: x['fitness'], reverse=True)


def mutation(individual, m_rate=.3):
    """This mutation mutates random subsets of an individuals genotype"""
    rnd_rate = random.uniform(0, 1)
    if rnd_rate > m_rate:
        print "Mutating Individual!\nRandom rate is: {}\nM Rate is: {}".format(rnd_rate, m_rate)
        split_point = random.randint(1, len(individual)-1)
        start, stop = random_sampling(0, len(individual), split_point)
        # generate a new corpus and markov chain
        new_corpus = [['C#4', 'A5'], ['B5', 'C#', 'F#3']]
        individual[start:stop] = new_corpus[start:stop]
        return individual
    print "Not mutating\nRandom rate is: {}\nM Rate is: {}".format(rnd_rate, m_rate)
    return individual
