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
        $("<div id="+el.index+" style='border:2px solid white;'>").appendTo("#sortable-trait");
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
    var that = this;
    var _normalize = function(score, min, range) {
        /*
            we need to normalize the score so we can operate on a scale between
            0 and 100.

            additionally, if you dont move the notes around then your score is 0,
            but it should be displayed as 100.
        */
        console.log("euclidan score is " + score);
        console.log("min score is " + min);
        console.log("range is " + range);
        console.log("normalized score is " + (100 - (((score - min) / range) * 100)));
        return (100 - (((score - min) / range) * 100));
    };

    var _distance_fn = function(x, y) {
        /*
            euclidean distance
        */

        console.log("old score" + that.score);
        x.forEach(function(el) {
            that.score += Math.sqrt(Math.pow((el.index - y[el.index].index), 2));
        });
        console.log("new score" + that.score);
        return that.score;
    };


    if(adjusted_order.length < 1) {
        console.log("fitness is 100");
    }

    var _score = _distance_fn(original_notes, adjusted_order);
    var _max_score = _distance_fn(original_notes, reversed);
    var _normalized = _normalize(_score, 0, _max_score);
    return _normalized;
};

Individual.prototype.fitness_graph = function() {
    var previous_indis = [];
    var previous_indis_scores = [];

    $.getJSON('/population/' + this.generation, function(obj) {
        console.log(obj);
        for(var idx in obj) {
            if(obj[idx].hasOwnProperty('fitness')) {
                previous_indis.push(obj[idx].id);
                previous_indis_scores.push(Math.ceil(obj[idx].fitness));
            }
        }
        console.log(previous_indis);
        console.log(previous_indis_scores);
        var chart = new Highcharts.Chart({
            chart: {
                type: 'line',
                renderTo: 'fitness-container'
            },
            title: {
                    text: 'Fitness Score Over Time',
                    x: -20 //center
                },
            xAxis: {
                categories: previous_indis,
                title: {text: 'Individual ID'}
            },
            yAxis: {
                title: {text: 'Score'},
                plotLines: [{
                    value: 0,
                    width: 1,
                    color: '#808080'
                }]
            },
            tooltip: {
                valueSuffix: ''
            },
            legend: {
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle',
                borderWidth: 0
            },
            series: [{
                name: 'Fitness Score',
                data: previous_indis_scores
            }]
        });
    });
};

function initializeMusic() {
    MIDI.loadPlugin({
        soundfontUrl: "../../static/js/soundfont/",
        instrument: ["acoustic_grand_piano"],
        callback: playMusic
    });
}

function playMusic() {
    var playSong = function(_c) {
        for (var i = 0; i < _c.length; i++) {
            var chord = _c[i];
            var delay = i / 4;
            playChord(chord, delay);
        }
    };

    var playChord = function(chord, delay) {
        var midiNotes = [];

        for (var i = 0; i < chord.notes.length; i++) {
            midiNotes.push(MIDI.keyToNote[chord.notes[i]]);
        }
        console.log(chord.notes + ' (' + JSON.stringify(midiNotes) + ') ' + delay);
        MIDI.chordOn(0, midiNotes, 127, delay);
    };

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
    MIDI.chordOn(0, midiNotes, 127, delay);
}

$(function() {
    var indi_id = $("#indi-id").attr("class");
    var generation = $("#current-gen").attr("class");
    var indi_uri = '/population/' + generation + '/' + indi_id;
    var individual;

    $("#next-song").click(function() {
        // being lazy. this is to ensure that if the user doesnt move any of
        // the traits around, the fitness score of 100 is still sent!
        $.post(indi_uri, {fitness: individual.score}, function(resp) {
            console.log("resp is ", resp);
        });
        $("#ns").submit();
    });

    $.getJSON(indi_uri, function(resp) {
        resp.notes.forEach(function(el, idx) {
            original_notes.push({
                'index': idx,
                'notes': el.map(function(n){
                    // midi.js requires flats to be denoted as `b`
                    return n.replace("-", "b");
                })
            });
        });
        resp.notes = original_notes;
        reversed = original_notes.reverse();
        individual = new Individual(resp);
        individual.render_notes();
        individual.fitness_graph();
    });


    $('#play').click(function(){
        initializeMusic();
    });

    $("#override-fitness-submit").click(function() {
        var override_score = $("#override-fitness-score").val();
        $.post(indi_uri, {fitness: override_score}, function(resp) {
            $("#ns").submit();
        });
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
              var new_order_notes = [];
              adjusted_order.forEach(function(el) {
                var chords = [];
                for(var n in el.notes) {
                    chords.push(el.notes[n]);
                }
                new_order_notes.push(chords);
              });
              var _score = individual.fitness();
              individual.score = _score;
              $('#current_score').html("Current Score: <small>" + _score.toFixed(2) + "/100</small>");
              initializeMusic();
              $.post(indi_uri, {fitness: _score, adjusted_notes: JSON.stringify(new_order_notes)}, function(resp) {
                  console.log("resp is ", resp);
              });
        }
    });

    $( "#sortable-trait" ).disableSelection();
});
