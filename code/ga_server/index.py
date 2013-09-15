import json
from collections import defaultdict
from itertools import chain

import model
import ga

import web

urls = (
    '/', 'Index',
    '/fitness/(.+)', 'Fitness',
    '/save_fitness/(.+)', 'SaveFitness',
    '/terminate', 'Terminate',
    '/fitness_graph/(.+)', 'FitnessGraph',
    '/current_best/(.+)/(.+)', 'CurrentBestIndividual',
)

render = web.template.render('templates/', base='layout')
app = web.application(urls, globals())
title = 'GA Server'
USER_SETTINGS = {'mc_size': 0, 'mc_nodes': 0, 'rate': 0.0}

class Index:
    def GET(self):
        """Render the parameter initialization view"""
        model.pop_clear_conn()
        model.params_clear_conn()
        # call REST server for a list of available songs
        br = web.Browser()
        br.open('http://localhost:8000/q/song') # make dynamic later
        songs = json.loads(br.get_text())
        print songs

        return render.index(title, songs)

    def POST(self):
        pd = web.input()
        num_gen = pd.num_gen
        song = pd.influencer

        # call REST server to get artist
        br = web.Browser()
        br.open('http://localhost:8000/q/songartist/' + song) # make dynamic later
        artist = json.loads(br.get_text())[0]
        print artist

        num_indi = pd.pop_size
        num_traits = pd.num_traits
        size = pd.mc_size
        nodes = pd.mc_nodes

        USER_SETTINGS['max_gen'] = int(num_gen)
        USER_SETTINGS['mc_size'] = int(size)
        USER_SETTINGS['mc_nodes'] = int(nodes)
        USER_SETTINGS['rate'] = float(pd.mrate)

        model.params_save({"max_gen":int(num_gen)})
        model.params_save({"num_indi": int(num_indi)})

        population = ga.create_population(artist, song, num_indi, num_traits, size, nodes, USER_SETTINGS['rate'])

        for indi in population:
            for nt in range(int(num_traits)):
                trait = {
                    "artist": indi['artist'],
                    "song": indi['song'],
                    "indi_id": int(indi['indi_id']),
                    "trait_id": nt,
                    "generation": int(indi['generation']),
                    "fitness": 0,
                    "note": indi['note'][nt],
                    "user_note": indi['note'][nt],
                    "duration": 1,}
                model.pop_save_individual(trait)

        # call fitness on first individual
        raise web.seeother('/fitness/0')

class Fitness:
    """This is an interactive fitness function, i.e. the individual is scored
    by the user. The user is shown a melody and is allowed to make X modifications
    to it (e.g. re-order up to X traits). The euclidean dsitance is taken for the original melody
    and the user-modified melody. Ideally, we want a fitness score of 0 because that
    means the user liked what the computer presented."""

    def GET(self, indi_id):
        print 'MRATE :: ',USER_SETTINGS
        individual = model.pop_find_individual(int(indi_id))
        # converts from unicode to dictionary
        fake_individual = []
        artist = ''
        song = ''
        current_gen = ''

        # note_colors = {
        #     'A': 'red',
        #     'B': 'yellow',
        #     'C': 'orange',
        #     'D': 'green',
        #     'E': 'blue',
        #     'F': 'purple',
        #     'G': 'grey',}

        idx = 0
        for i in individual:
            current_gen = i['generation']
            #if i['note'][0] in note_colors.keys():
            if '-' in i['note']:
                i['note'] = i['note'].replace('-', 'b')
            #color = note_colors[i['note'][0]]
            #fake_individual.append([i['note'],color])
            fake_individual.append([i['note'], idx])
            artist = i['artist']
            song = i['song']
            idx += 1

        # song_name = indi_id+"_song.mid" # don't cast indi_id to int because cant concat int and string
        max_gen = int(model.params_max_gen()['max_gen'])

        return render.fitness(title, indi_id, fake_individual, artist, song, max_gen, current_gen, USER_SETTINGS)

    def POST(self, indi_id):
        """
        @TODO get all traits for the individual by gathering all the notes
        and user-notes for the individual and storing in two lists. compute
        the euclidean distance between the two lists and set as fitness score
        for the individual

        @TODO oracle to decide what to do next
        """

        #model.pop_update_indi_fitness(int(indi_id), score)
        # query the individual and extract note and user-note
        individual = model.pop_find_individual(int(indi_id))
        user_list = []
        original_list = []

        # so ugly -- fix later
        for trait in individual:
            user_list.append(str(trait['user_note']))
            original_list.append(str(trait['note']))

        # score = ga.euclidean_distance(original_list, user_list)
        # print 'Fitness score :: ', score
        #update fitness score for individual
        # model.pop_update_indi_fitness(int(indi_id), score)
        ga.fate(int(indi_id))


class FitnessGraph(object):
    def GET(self, indi_id):
        all_indis = model.find_indis_less_than(int(indi_id))
        scores = [indi['fitness'] for indi in all_indis]
        resp = {k: v for (k, v) in enumerate(scores)}
        return json.dumps(resp)


class CurrentBestIndividual(object):
    def GET(self, indi_id, generation):
        best_indi = model.current_best_indi(int(indi_id), int(generation))
        print best_indi
        resp = {}
        if best_indi:
            resp.update({
                'id': best_indi['indi_id'],
                'score': best_indi['fitness']
            })
        return json.dumps(resp)


class SaveFitness:
    def POST(self, indi_id):
        req = json.loads(web.data())
        fitness = req['fitness']
        for pairs in req['notes']:
            trait_id = pairs['trait_id']
            note = pairs['name']
            saved_traits = model.pop_find_trait(int(indi_id), int(trait_id))
            user_note = note.replace('b', '-')
            model.pop_update_user_trait(saved_traits,
                {"$set": {"user_note": user_note}})
            model.pop_update_indi_fitness(int(indi_id), int(fitness))


class Terminate(object):
    def GET(self):
        """Return the best individual from each generation"""
        best_individuals = model.find_top_individuals()
        individuals = defaultdict(list)
        for k, v in best_individuals.items():
            for indi in v:
                for trait in indi:
                    trait = trait['user_note'].replace('-', 'b')
                    individuals[k].append(trait)
        return render.terminate(title, individuals)


if __name__ == "__main__":
    app.internalerror = web.debugerror
    app.run()
