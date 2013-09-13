import json
from collections import defaultdict
from itertools import chain

import model
import ga
from core import GAInitialization

import web

urls = (
    '/', 'Index',
    '/fitness/(.+)', 'Fitness',
    '/save_fitness/(.+)', 'SaveFitness',
    '/terminate', 'Terminate',
)

render = web.template.render('templates/', base='layout')
app = web.application(urls, globals())
title = 'GA Server'
USER_SETTINGS = {'mc_size': 0, 'mc_nodes': 0, 'rate': 0.0}
SETTINGS = GAInitialization()


class Index(object):
    def GET(self):
        title = "Welcome!"

        # clear stale settings
        SETTINGS.reset_ga()

        # get pairs of artist and song
        listings = SETTINGS.music_collection('artist:*')

        return render.index(title, listings)

    def POST(self):
        artist, song = web.input()['influencer'].split(' - ')
        params = {k: v for (k, v) in web.input().items() if k not in ['influencer']}
        params.update({
            'artist': artist,
            'song': song
        })
        SETTINGS.save_properties(params)
        population = ga.create_population(params)

        for individual in population:
            notes = individual.pop('note')
            for note in notes:
                trait = individual
                trait.update({
                    'trait_id': notes.index(note),
                    'fitness': 0,
                    'note': note,
                    'user_note': note,
                    'duration': 1
                })
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


class SaveFitness:
    def POST(self, indi_id):
        """Updates the user-note in a single trait in an individual. This is information
        is used to find out what notes the user didn't like from the computer
        presented melody"""
        t_id = web.input()['trait_id']
        _note = web.input()['name'].replace('b', '-')
        fitness_score = web.input()['fitness']
        saved_traits = model.pop_find_trait(int(indi_id), int(t_id))
        model.pop_update_user_trait(saved_traits, {"$set": {"user_note":_note}})
        model.pop_update_indi_fitness(int(indi_id), int(fitness_score))


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
