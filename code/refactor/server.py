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
    # params = pop size and indi size (num traits)
    render_population(request.args)

if __name__ == "__main__":
    app.run(debug=True)
