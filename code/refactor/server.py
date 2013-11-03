import json

from render import cache_get, cache_set, render_population

from flask import Flask, request, jsonify
app = Flask(__name__)

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
    if params.get('traits'):
        params['traits'] = params['traits'].split(',')
    for k, v in params.items():
        try:
            params[k] = int(v)
        except:
            print "not a number. leaving as is!"
            params[k] = v
    # flask jsonify throws an error if you have a list of dicts so using
    # python json instead
    return json.dumps(render_population(**params))


@app.route('/fitness/<generation>/<id>', methods=['GET', 'POST'])
def fitness(generation, id):
    """Return the notes for the requested individual"""
    if request.method == 'POST':
        # form data coming in
        # set fitness score, run ga, etc
        params = {k: v for (k, v) in request.form.copy().items()}
        name = "{}:{}:generation:{g}".format(*map(params.pop, ['artist', 'song']), g=generation)
        individual = cache_get(name).get(id)
        individual['fitness'] = params.get('fitness')
        cache_set(name, id, individual)
        return jsonify({"msg": "in cache"})

    artist = request.args['artist']
    song = request.args['song']
    name = "{}:{}:generation:{}".format(artist, song, generation)
    individual = cache_get(name).get(id)
    return jsonify(individual)

if __name__ == "__main__":
    app.run(debug=True)
