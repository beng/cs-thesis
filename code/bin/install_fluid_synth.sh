# OS X Mavericks does not come with MIDI support. These need to be
# installed in order to get MIDI support, although, I am unable to even
# play a MIDI file with this...

brew install fluidsynth
wget http://www.schristiancollins.com/soundfonts/GeneralUser_GS_1.44-FluidSynth.zip
unzip GeneralUser_GS_1.44-FluidSynth.zip
mkdir -p /usr/local/share/fluidsynth
mv GeneralUser\ GS\ 1.44\ FluidSynth/GeneralUser\ GS\ FluidSynth\ v1.44.sf2 /usr/local/share/fluidsynth
