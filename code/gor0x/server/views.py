import json

from flask import Blueprint, request, jsonify, render_template, redirect, url_for

from ..ga.render import render_population, render_artist_pairs, generate_markov, random_sampling
from ..ga.core import begin_ga
from ..ga.model import cache_get, cache_set, cache_hmset, clear_cache


mod = Blueprint('gor0x', __name__, template_folder='templates', static_folder='static')


def parse_params(params):
    _params = {}
    for k, v in params.items():
        try:
            _params[k] = int(v)
        except Exception:
            print "not a number. converting unicode to string"
            _params[k] = str(v)
    return _params


def validate_params(required=None, supplied=None):
    def render_error(missing):
        prefix = "Missing required parameters: {}".format("{}" * len(missing))
        message = prefix.format(*missing)
        return dict(message=message)
    missing = set(required) - set(supplied)
    return False if not set(required).issubset(set(supplied)) else True


@mod.route('/', methods=['GET', 'POST'])
def initialize():
    clear_cache()

    if request.method == 'POST':
        params = parse_params(request.form.copy())
        artist, song = params['artist_song_pairs'].split(' - ')
        params['artist'] = artist
        params['song'] = song
        params['base_key'] = '{}:{}:generation'.format(params['artist'], params['song'])
        if params['mc_nodes'] > params['mc_size']:
            return jsonify({'msg': "mc nodes MUST be smaller than mc size!"})
        cache_hmset('settings', params)
        population = render_population(**params)
        return redirect(url_for('.fitness', generation=population[0]['generation'], id=population[0]['id']))
    return render_template('gor0x/index.html', artist_pairs=render_artist_pairs())


@mod.route('/markov', methods=['POST'])
@mod.route('/markov/<key>', methods=['GET', 'POST'])
def markov(key=None):
    """GET: return the saved markov chain for a given id
    """
    if request.method == 'POST':
        """POST: given a song and artist, return a markov chain
        """
        pass
    return jsonify(cache_get(key))


@mod.route('/fitness/<generation>/<id>', methods=['GET', 'POST'])
def fitness(generation, id, individual=None):
    cache_set('settings', 'current_generation', generation)
    settings = cache_get('settings')
    key = "{}:{}".format(settings['base_key'], generation)
    artist = settings['artist']
    song = settings['song']
    tgen = settings['tgen']
    individual = cache_get(key)[id]
    kwargs = {
        'song': song,
        'artist': artist,
        'tgen': tgen,
        'individual': individual,
    }

    if request.method == 'POST':
        """Use the individual that was just evaluated to determine
        where we are in the grand scheme of things. How many more individuals
        of the current generation need to be evaluated? Are the termination
        requirements met? Are we ready to move to the next generation? Etc..."""
        tgen = int(settings['tgen'])
        psize = int(settings['psize'])
        id = int(id)
        generation = int(generation)

        if id == psize:
            # termination requirements met?
            if generation >= tgen:
                return redirect(url_for('.stats'))
            next_gen = begin_ga(key)
            return redirect(url_for('.fitness', generation=next_gen, id=1))
        elif id < psize:
            return redirect(url_for('.fitness', generation=generation, id=id+1))
        return redirect(url_for('.stats'))
    return render_template('gor0x/fitness.html', **kwargs)


@mod.route('/population', methods=['GET'])
@mod.route('/population/<generation>', methods=['GET'])
@mod.route('/population/<generation>/<id>', methods=['GET', 'POST'])
def population(generation=None, id=None):
    settings = cache_get('settings')
    entire_population = []
    if not generation:
        all_generations = settings['current_generation']
        for gen in xrange(1, int(all_generations) + 1):
            name = "{}:{}".format(settings['base_key'], gen)
            entire_population.append(cache_get(name))
    else:
        name = "{}:{}".format(settings['base_key'], generation)
        population = cache_get(name)

    if request.method == 'POST':
        # POST will always be referencing an individual
        params = parse_params(request.form.copy())
        individual = cache_get(name).get(id)
        individual['fitness'] = params['fitness']
        if params.get('adjusted_notes'):
            individual['notes'] = json.loads(params['adjusted_notes'])
        elif individual['fitness'] == 100:
            # trash this guy and create a new one
            # generate a new corpus by using the cached markov chain
            key = "{}:{}".format(settings['artist'], settings['song'])
            markov = cache_get(key)['markov']
            start, stop = random_sampling(1, len(markov), int(settings['isize']))
            individual['notes'] = markov[start:stop]
        cache_set(name, id, individual, serialize=True)
        return jsonify(individual)

    if entire_population:
        # TODO: turn entire_population into dictioanry
        return jsonify(entire_population[0])
    return jsonify(population.get(id) or population)


@mod.route('/settings/<option>', methods=['GET'])
def settings(option):
    return jsonify({option: cache_get('settings').get(option)})


@mod.route('/population/export/<generation>/<id>', methods=['GET'])
def export(generation, id):
    """Generate a MIDI file out of the requested individual and save to ./tmp"""
    file_name = '{}_{}.mid'.format(generation, id)
    return jsonify({'file_name': file_name})


@mod.route('/population/stats', methods=['GET'])
def stats(**kwargs):
    settings = cache_get('settings')
    base_key = settings['base_key']
    all_indis = {}
    stats = {}
    total_score = 0
    total_indis = 0
    generations = range(1, int(settings['tgen']) + 1)

    for gen in generations:
        key = "{}:{}".format(base_key, gen)
        individuals = cache_get(key)
        all_indis[gen] = individuals
        for indi, indi_info in individuals.items():
            total_score += float(indi_info['fitness'])
            total_indis += 1
        stats[gen] = {
            'best': sorted(individuals.items(), key=lambda x: x[1]['fitness'])[0][1]['fitness'],
            'mean': total_score / total_indis,
            'worst': sorted(individuals.items(), key=lambda x: x[1]['fitness'])[-1][1]['fitness']
        }
    return render_template('gor0x/stats.html', stats=stats, all_indis=all_indis, **kwargs)
