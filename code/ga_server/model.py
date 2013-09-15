"""Models file"""

from collections import defaultdict

from config import HOST, PORT, COMMUNITY_DB

from pymongo import Connection

CONNECTION = Connection(HOST, PORT)
DB = CONNECTION[COMMUNITY_DB]
PARAMS_DB = DB['params']
POP_COLL = DB['pop_coll']


def params_clear_conn():
    """Remove all GA initialization settings"""
    PARAMS_DB.remove()


def params_save(init):
    """Save all GA initialization settings"""
    PARAMS_DB.save(init)


def params_max_gen():
    """Find the max # of generations"""
    return PARAMS_DB.find_one({"max_gen": {"$type": 16}})


def params_num_indi():
    """Find the max # of individuals per population"""
    return PARAMS_DB.find_one({"num_indi": {"$type": 16}})

# def params_mutation_rate():
    # return PARAMS_DB.find_one({"mutation_rate": {"$type": 1}})


def pop_clear_conn():
    """Clear settings on new connect"""
    POP_COLL.remove()


def pop_save_individual(information):
    """Information is a dictionary containing
    individual id, artist, song, note, duration, fitness"""
    POP_COLL.save(information)


def pop_find_individual(indi_id):
    """Find an individual given an ID"""
    return POP_COLL.find({'indi_id': indi_id})


def pop_find_all():
    """Find all individuals in the collection"""
    return [indi for indi in POP_COLL.find()]


def pop_update_user_note(spec, user_note):
    """Update a specific note for an individual"""
    POP_COLL.update(spec, user_note)


def pop_update_indi(indi_id, note):
    """Update an inidivudals note"""
    POP_COLL.update({"indi_id": indi_id}, {"$set": {"note": note}})


def pop_update_indi_fitness(indi_id, score):
    """Update the fitness score for an individual"""
    POP_COLL.update({"indi_id": indi_id}, {"$set": {"fitness": score}})


def pop_max_indi(generation):
    """Get max indi of current generation"""
    return POP_COLL.find(
        {"generation": generation},
        limit=1
    ).sort("indi_id", -1)


def pop_current_generation(indi_id):
    """Find a specific individual in the current generation"""
    return POP_COLL.find_one({"indi_id":indi_id})


def pop_find_trait(indi_id, t_id):
    """Find a specific trait for an individual"""
    return POP_COLL.find_one({"indi_id": indi_id, "trait_id": t_id})


def pop_update_user_trait(saved_traits, fn):
    """Update something..."""
    POP_COLL.update(saved_traits, fn)


def pop_population_by_generation(current_generation):
    """Used for tournament selection"""
    return [individual for individual in POP_COLL.find(
        {"generation":current_generation, "trait_id":0})]


def find_top_individuals():
    """Return best individual from each generation"""
    max_gen = params_max_gen()['max_gen']
    individuals = {}
    best_individuals = defaultdict(list)
    for current_gen in range(0, int(max_gen)):
        individuals[current_gen] = POP_COLL.find(
            {"generation": current_gen},
            limit=1
        ).sort("fitness", 1)

    for gen, cursor in individuals.items():
        for indi in cursor:
            best_individuals[gen].append(
                [indi for indi in pop_find_individual(indi['indi_id'])]
            )
    return best_individuals


def current_best_indi(indi_id, generation):
    indi = POP_COLL.find({
        'indi_id': {
            '$lt': indi_id
        },
        'trait_id': 0,
        'generation': generation
    }, limit=1).sort("fitness", -1)
    best = [i for i in indi]
    return best[0] if best else []


def find_indis_less_than(lookup_id):
    """Return all indivduals with an id less than param"""
    return POP_COLL.find({'indi_id': {'$lt': lookup_id}, 'trait_id': 0})
