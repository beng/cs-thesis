import json

from flask import Flask, request, jsonify, render_template, redirect, url_for

from render import cache_get, cache_set, render_population, cache_hmset
from ga import begin_ga

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
    if request.method == 'POST':
        # params = parse_params(request.form.copy())
        params = {'artist': 'vivaldi', 'song': 'winter_allegro', 'isize': 4, 'psize': 2, 'mc_size': 10, 'mc_nodes': 2, 'tgen': 2}
        params['base_key'] = '{}:{}:generation'.format(params['artist'], params['song'])
        print "base key is ", params['base_key']
        if params['mc_nodes'] > params['mc_size']:
            return jsonify({'msg': "mc nodes MUST be smaller than mc size!"})

        cache_hmset('settings', params)
        population = render_population(**params)
        print "population is ", population
        return redirect(url_for('fitness', generation=population[0]['generation'], id=population[0]['id']))
        # return render_template('fitness.html', individual=population[0])

    return render_template('index.html')


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
    params = {k: v for (k, v) in request.form.copy().items()}
    if params['mc_nodes'] > params['mc_size']:
        return jsonify({'msg': "mc nodes MUST be smaller than mc size!"})
    cache_hmset('settings', params)
    if params.get('traits'):
        params['traits'] = params['traits'].split(',')
    for k, v in params.items():
        try:
            params[k] = int(v)
        except:
            print "not a number. converting unicode to string"
            params[k] = str(v)
    # flask jsonify throws an error if you have a list of dicts so using
    # python json instead
    return json.dumps(render_population(**params))


@app.route('/fitness/<generation>/<id>', methods=['GET', 'POST'])
def fitness(generation, id, individual=None):
    # id, generation = map(int, [id, generation])
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


@app.route('/individual/<generation>/<id>', methods=['GET', 'POST'])
def individual(generation, id):
    """Return the notes for the requested individual"""
    if request.method == 'POST':
        # form data coming in, set the fitness score
        params = {k: v for (k, v) in request.form.copy().items()}
        settings = cache_get('settings')
        key = "{}:{}".format(settings['base_key'], generation)
        individual = cache_get(key).get(id)
        individual['fitness'] = int(params['fitness'])
        cache_set(key, id, individual, serialize=True)
        return jsonify({"msg": "in cache"})

    # only used if we decide to make this an endpoint for JS
    settings = cache_get('settings')
    name = "{}:{}".format(settings['base_key'], generation)
    individual = cache_get(name).get(id)
    notes = []
    for idx, chords in enumerate(individual['notes']):
        notes.append([idx, chords])
    individual['notes'] = notes
    return jsonify(individual)


@app.route('/settings/<option>', methods=['GET'])
def settings(option):
    return jsonify({option: cache_get('settings').get(option)})


@app.route('/terminate/<generation>/<id>', methods=['GET'])
def terminate(id):
    print "in terminate!"


if __name__ == "__main__":
    app.run(debug=True)
