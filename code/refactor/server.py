from render import cache_get, cache_set, render_population

from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/markov", methods=['POST'])
@app.route("/markov/<key>", methods=['GET', 'POST'])
def markov(key=None):
    """GET: return the saved markov chain for a given id
    """
    if request.method == 'POST':
        """POST: given a song and artist, return a markov chain
        """
        pass
    return jsonify(cache_get(key))


@app.route("/spawn", methods=['GET'])
def spawn_population():
    """Given a population size, individual size, artist, and song, return
    an initial population
    """
    params = {k: v for (k, v) in request.args.copy().items()}
    if params.get('traits'):
        params['traits'] = params['traits'].split(',')
    for k, v in params.items():
        try:
            params[k] = int(v)
        except:
            print "not a number. leaving as is!"
            params[k] = v
    return jsonify(render_population(**params))

if __name__ == "__main__":
    app.run(debug=True)
