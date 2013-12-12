"""
Pre-compute music21 objects out of every midi file in the `midi_files` folder
"""
import pickle
import os

import music21
from redis import Redis
from flask.ext.script import Manager

from gor0x import create_app

manager = Manager(create_app)
r = Redis()
MIDI_PATH = './bin/midi'


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


@manager.command
def clean_midi_name():
    """Recurses through a path converting any MIDI file name to lowercase"""
    for root, _, files in os.walk('./bin/midi'):
        from itertools import imap, takewhile
        list(imap(lambda f: os.rename(f, f.lower()),
                  map(lambda f: os.path.join(root, f),
                      takewhile(lambda f: f != '.DS_Store', files))))


@manager.command
def cache_midi_folder():
    """Pre-cache every song in the midi folder by converting it to a music21
    object, extracting the desired traits, and storing in redis with the key
    `artist`:`song_name`
    """
    path = './bin/midi/{}'
    artists_dirs = map(path.format, os.listdir(MIDI_PATH))
    map(artists_dirs.remove, filter(lambda d: '.mid' in d or '.DS_Store' in d, artists_dirs))
    for _dir in artists_dirs:
        for root, d, files in os.walk(_dir):
            for _file in files:
                print "\n"
                tmp_path = root + '/' + _file
                artist = root.split('/')[-1].lower()
                song = _file.replace('.mid', '').lower()
                name = '{}:{}'.format(artist, song)
                try:
                    print "begin parsing of:", name
                    mobj = music_obj(tmp_path)
                    print ">> begin extraction of CHORDS for:", name
                    notes = parse(mobj)
                    if notes:
                        print ">> notes are", notes
                        print ">> begin caching of notes with NAME: `{}` and set: `original_notes`".format(name)
                        cache_set(name, 'original_notes', notes, serialize=True)
                        print ">> begin left push of: `{}` into list `artist pairs`".format(name)
                        r.lpush('artist_pairs', name)
                except Exception, e:
                    print "ISSUE PARSING SONG: {}! Exception is {}".format(name, e)
                    continue
                print "\n"
                print "-" * 100


if __name__ == "__main__":
    manager.run()
