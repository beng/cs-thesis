import json

from flask import Flask, request, jsonify, render_template, redirect, url_for

from render import render_population, render_artist_pairs
from ga import begin_ga
from model import cache_get, cache_set, cache_hmset, clear_cache

app = Flask(__name__)


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


@app.route('/', methods=['GET', 'POST'])
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
        return redirect(url_for('fitness', generation=population[0]['generation'], id=population[0]['id']))
    return render_template('index.html', artist_pairs=render_artist_pairs())


@app.route('/markov', methods=['POST'])
@app.route('/markov/<key>', methods=['GET', 'POST'])
def markov(key=None):
    """GET: return the saved markov chain for a given id
    """
    if request.method == 'POST':
        """POST: given a song and artist, return a markov chain
        """
        pass
    return jsonify(cache_get(key))


@app.route('/spawn', methods=['POST'])
def spawn_population():
    """Given a population size, individual size, artist, and song, return
    an initial population
    """
    # params = {k: v for (k, v) in request.form.copy().items()}
    params = parse_params(request.form.copy())
    if params['mc_nodes'] > params['mc_size']:
        return jsonify({'msg': "mc nodes MUST be smaller than mc size!"})
    cache_hmset('settings', params)
    if params.get('traits'):
        params['traits'] = params['traits'].split(',')
    for k, v in params.items():
        try:
            params[k] = float(v)
        except:
            print "not a number. converting unicode to string"
            params[k] = str(v)
    # flask jsonify throws an error if you have a list of dicts so using
    # python json instead
    return json.dumps(render_population(**params))


@app.route('/fitness/<generation>/<id>', methods=['GET', 'POST'])
def fitness(generation, id, individual=None):
    # id, generation = map(int, [id, generation])
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
                return redirect(url_for('terminate', generation=generation, id=id))
            next_gen = begin_ga(key)
            return redirect(url_for('fitness', generation=next_gen, id=1))
        elif id < psize:
            return redirect(url_for('fitness', generation=generation, id=id+1))
        return redirect(url_for('terminate', generation=generation, id=id))

    return render_template('fitness.html', **kwargs)


@app.route('/population', methods=['GET'])
@app.route('/population/<generation>', methods=['GET'])
@app.route('/population/<generation>/<id>', methods=['GET', 'POST'])
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
        print "Params are ", params
        individual = cache_get(name).get(id)
        individual['fitness'] = params['fitness']
        cache_set(name, id, individual, serialize=True)
        return jsonify(individual)

    if entire_population:
        # TODO: turn entire_population into dictioanry
        return jsonify(entire_population[0])
    return jsonify(population.get(id) or population)


@app.route('/settings/<option>', methods=['GET'])
def settings(option):
    return jsonify({option: cache_get('settings').get(option)})


@app.route('/terminate/<generation>/<id>', methods=['GET'])
def terminate(generation, id, **kwargs):
    return render_template('terminate.html', **kwargs)


if __name__ == "__main__":
    app.run(debug=True)
