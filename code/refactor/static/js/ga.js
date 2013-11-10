var original_notes = [];
var adjusted_order = [];
var reversed_original_notes; // used to calculate max possible euclidean distance

var colors = {
    'A': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'B': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'C': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'D': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'E': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'F': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'G': '#'+(Math.random()*0xFFFFFF<<0).toString(16)
};

Individual = function(r) {
    this.id = r.id;
    this.generation = r.generation;
    this.score = r.fitness || 0;
    this.notes = r.notes;
};

Individual.prototype.color = function(pitch) {
    return "background-color:".concat(colors[pitch], ";");
};

Individual.prototype.render_style = function(pitch) {
    return "border:2px solid black;".concat(this.color(pitch));
};

Individual.prototype.render_notes = function() {
    var that = this;
    var _final = [];
    this.notes.forEach(function(el) {
        $("<div id="+el.index+">").appendTo("#sortable-trait");
        el.notes.forEach(function(_note) {
            $("<div/>", {
                id: el.index,
                class: _note,
                text: _note,
                style: that.render_style(_note[0]),
            }).appendTo("#" + el.index);
        });
    });
};

Individual.prototype.fitness = function() {
    if(adjusted_order.length < 1) {
        console.log("fitness is 100");
    }

    var _score = euclidean_distance(original_notes, adjusted_order);
    var _max_score = euclidean_distance(original_notes, reversed);
    var _normalized = normalize(_score, 0, _max_score);
    $('#current_score').html("Current Score: <small>" + _normalized + "/100</small>");
    return _normalized;
};

function normalize(score, min, range) {
    /*
        we need to normalize the score so we can operatore on a scale between
        0 and 100.

        additionally, if you dont move the notes around then your score is 0,
        but it should be displayed as 100.
    */
    return (100 - (((score - min) / range) * 100));
}

function euclidean_distance(x, y) {
    var _score = 0;
    x.forEach(function(el) {
        _score += Math.sqrt(Math.pow((el.index - y[el.index].index), 2));
    });

    return _score;
}

function initializeMusic() {
    MIDI.loadPlugin({
        soundfontUrl: "../../static/js/soundfont/",
        instrument: ["acoustic_grand_piano"],
        callback: playMusic
    });
}

function playMusic() {
    var _chords = adjusted_order.length > 0 ? adjusted_order : original_notes;
    playSong(_chords);
}

function playSong(chords) {
    for (var i = 0; i < chords.length; i++) {
        var chord = chords[i];
        var delay = i / 4;
        playChord(chord, delay);
    }
}


function playChord(chord, delay) {
    var midiNotes = [];

    for (var i = 0; i < chord.notes.length; i++) {
        midiNotes.push(MIDI.keyToNote[chord.notes[i]]);
    }
    console.log(chord.notes + ' (' + JSON.stringify(midiNotes) + ') ' + delay);
    MIDI.chordOn(1, midiNotes, 127, delay);
}

$(function() {
    var indi_id = $("#indi-id").attr("class");
    var generation = $("#current-gen").attr("class");
    var indi_uri = '/individual/' + generation + '/' + indi_id;
    var individual;
    $.getJSON(indi_uri, function(resp) {
        resp.notes.forEach(function(el) {
            var idx = el[0];
            var _notes = el[1];
            original_notes.push({
                'index': idx,
                'notes': _notes
            });
        });
        resp.notes = original_notes;
        reversed = original_notes.reverse();
        individual = new Individual(resp);
        individual.render_notes();
    });

    $('#play').click(function(){
        initializeMusic();
    });

    $("#next-song").click(function() {
        $("#ns").submit();
    });

    $( "#sortable-trait" ).sortable({
        stop: function(event) {
              adjusted_order.length = 0;
              $('div#sortable-trait > div').each(function(index) {
                  var child_notes = [];
                  $(this).children().each(function(idx) {
                      child_notes.push($(this).attr('class'));
                  });
                  adjusted_order.push({
                      index: $(this).attr('id'),
                      notes: child_notes
                  });
              });
              var _score = individual.fitness();
              console.log("normalized score is " + _score);
              initializeMusic();
              $.post(indi_uri, {fitness: _score}, function(resp) {
                  console.log("resp is ", resp);
              });
        }
    });

    $( "#sortable-trait" ).disableSelection();
});
