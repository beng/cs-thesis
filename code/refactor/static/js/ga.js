// function getRandomInt (min, max) {
//     return Math.floor(Math.random() * (max - min + 1)) + min;
// }

// $(function() {
//     var settings = {};
//     console.log('hello');
//     // var rnd = getRandomInt(1, 5);
//     // if(rnd < 2) {
//     //     $("#hello > p#ben").html("<p>hahaha</p>");
//     // } else {
//     //     $.getJSON('/individual/0/0', {song: 'winter_allegro', artist: 'vivaldi'}, function(o) {
//     //         console.log(o.note);
//     //         o.note.forEach(function(el) {
//     //             $("#hello").append("<p>"+el+"</p>");
//     //         });
//     //     })
//     // }

//     $.post('/initialize', {num_gen: 3, isize: 3, psize: 3, mc_nodes: 2, mc_size: 100, artist: 'vivaldi', song: 'winter_allegro'}, function(o) {
//         settings = o.settings;
//         var cg = 0;
//         var ci = 0;
//         console.log('psize is ', settings);
//         $.post('/spawn', {artist: 'vivaldi', song: 'winter_allegro', isize: 3, psize: 2, mc_size: 5, mc_nodes: 2}, function(pop) {
//             console.log(pop);
//             $.getJSON('/individual/' + cg + '/' + ci, {song: 'winter_allegro', artist: 'vivaldi'}, function(o) {
//                 ci++;
//                 console.log(o.note);
//                 o.note.forEach(function(el) {
//                     $("#hello").append("<p>"+el+"</p>");
//                 });
//                 $('#next').click(function() {
//                     console.log("ci is " + ci);
//                     if(ci <= settings.psize) {
//                         console.log("ci is less than pop size");
//                         $.getJSON('/individual/' + cg + '/' + ci, {song: 'winter_allegro', artist: 'vivaldi'}, function(o) {
//                             o.note.forEach(function(el) {
//                                 $("#hello").append("<p>"+el+"</p>");
//                             });
//                         })
//                     } else{
//                         // console.log('ci is ' + ci);
//                         console.log("next gen now!!!");
//                         console.log('cg is '+ cg);
//                     }
//                     ci++;
//                     console.log("new ci is " + ci);
//                 })
//                 // o.note.forEach(function(el) {
//                 //     $("#hello").append("<p>"+el+"</p>");
//                 // });
//             })
//         })
//     });

//     // http://localhost:5000/spawn -d "artist=vivaldi&song=winter_allegro&isize=3&psize=2&mc_size=5&mc_nodes=2"
// });
original_notes = [];

function initializeMusic() {
        MIDI.loadPlugin({
                soundfontUrl: "../../static/js/soundfont/",
                instrument: ["acoustic_grand_piano"],
                callback: playMusic
        });
}

function playMusic() {
    playSong(original_notes);
}

function playSong(keys) {
    for (var i = 0; i < keys.length; i++) {
        var key = keys[i];
        var delay = i / 4;
        if (typeof(key) == 'string')
            playKey(key, delay);
        else
            playChord(key, delay);
    }
}

function playKey(key, delay) {
        var midiNote = MIDI.keyToNote[key];
        console.log(key + ' (' + midiNote + ') ' + delay);
        MIDI.noteOn(0, midiNote, 127, delay);
}

function playChord(keys, delay) {
    console.log(keys.notes);
    var midiNotes = [];
    for (var i = 0; i < keys.notes.length; i++)
        midiNotes.push(MIDI.keyToNote[keys.notes[i]]);
    console.log(keys.notes + ' (' + JSON.stringify(midiNotes) + ') ' + delay);
    MIDI.chordOn(1, midiNotes, 127, delay);
}

$(function() {
    var indi_id = $("#indi-id").attr("class");
    var generation = $("#current-gen").attr("class");
    var indi_uri = '/individual/' + generation + '/' + indi_id;

    $.getJSON(indi_uri, function(resp) {
        resp.notes.forEach(function(el) {
            var idx = el[0];
            var _notes = el[1];
            original_notes.push({
                'index': idx,
                'notes': _notes
            });
        });
    });


    $('#listen').click(function(){
        initializeMusic();
        $.post(indi_uri, {fitness: 100}, function(resp) {
            console.log("resp is ", resp);
        });
    });

    $("#next-song").click(function() {
        console.log("CLICK!!!");
        $("#ns").submit();
    });
});
