"""
Pre-compute music21 objects out of every midi file in the `midi_files` folder
"""
import pickle
import os
import re

import music21
from redis import Redis

r = Redis(db=2)
MIDI_PATH = '../midi_files'


def music_obj(path):
    return music21.converter.parse(path)


def parse(mobj, traits=['chord'], **kwargs):
    """Given a music21 object and a list of traits,
    extract those traits from the music21 object, while:
        -preserving order
        -keeping a nested list of each trait(s) due to chords
            >> [[A4], [B5], [B5, C#4, F#3]]
    """
    _mobj = filter(lambda x: type(x).__name__.lower() in traits, mobj.recurse())
    elements = [[pitch for pitch in element.pitches] for element in _mobj]
    return map(lambda pitches: map(lambda pitch: pitch.nameWithOctave, pitches), elements)


def cache_set(name, key, value, serialize=None):
    if serialize:
        value = pickle.dumps(value)
    return r.hset(name, key, value)


def clean_midi_name(name):
    """Fixes the midi names so that instead of capitalizing each new word
    in a file name, split the filename on the capital word and join the words
    together with an underscore and then lowercase the entire filename"""

    # THIS DOES NOT WORK CORRECTLY DO NOT USE!!!
    split_capitals = map(str.lower, filter(None, re.split("([A-Z][^A-Z]*)", name)))
    return split_capitals


def cache_midi_folder():
    """Pre-cache every song in the midi folder by converting it to a music21
    object, extracting the desired traits, and storing in redis with the key
    `artist`:`song_name`
    """
    path = '../midi_files/{}'
    artists_dirs = map(path.format, os.listdir(MIDI_PATH))
    map(artists_dirs.remove, filter(lambda d: '.mid' in d or '.DS_Store' in d, artists_dirs))
    for _dir in artists_dirs:
        for root, d, files in os.walk(_dir):
            for _file in files:
                tmp_path = root + '/' + _file
                artist = root.split('/')[-1].lower()
                song = _file.replace('.mid', '').lower()
                name = '{}:{}'.format(artist, song)
                try:
                    mobj = music_obj(tmp_path)
                    notes = parse(mobj)
                    cache_set(name, 'original_notes', notes, serialize=True)
                except Exception, e:
                    print "ISSUE PARSING SONG! Exception is ", e
                    continue
