SPEED = 200,
SPACING = 300,
LISTEN=true;

function get_ed() {

    original_notes = [];

    $("div#orig_notes > div").each(function(index) {
        original_notes.push([$(this).attr('id'), $(this).attr('class')]);
    });
    PATTERN = [];
    var adjusted_order = [];

    $('div#sortable-trait > div').each(function(index) {
        adjusted_order.push([$(this).attr('id'), $(this).attr('class')])
        PATTERN.push($(this).attr('id'));
    });

    var ed = euclidean_distance(original_notes, adjusted_order);
    //console.log(ed);
    $("#current_score").html('Current Score: <small id="cs">' + ed + '/MAX(euclidean_distance())</small>');

    return ed;
}

function euclidean_distance(song1, song2) {
    var score = 0;
    for(var i=0; i < song1.length; i++) {
        //console.log(song1[i][1]);
        //console.log(song2[i][1]);
        score += Math.sqrt(Math.pow((song1[i][1] - song2[i][1]), 2));
    }
    return score;
}

function playPattern(pattern) { // playback a pattern
    //var next = Math.random() * NOTES.length >> 0,
    var i = 0;
    //PATTERN[PATTERN.length] = next;

    (function play() { // recursive loop to play pattern
        setTimeout( function() {
            console.log("pattern i :: "+pattern[i]);

            playSingle( pattern[i]);

            i++;

            if( i < pattern.length ) {
                play();
            } else {
                setTimeout( function() { LISTEN = true; }, SPEED + SPACING );
            }
        },
        SPEED + SPACING)
    })(); // end recursion
}

function playSingle(note) { // play a color/note
    MIDI.loadPlugin(function() {
        default_bg = $('#'+note).css('background-color');
        $('#'+note).css('background-color', 'white');
        MIDI.noteOn(0, MIDI.keyToNote[note], 127, 0);
        setTimeout(function() { // turn off color
            MIDI.noteOff(0, MIDI.keyToNote[note], 0);
            $('#'+note).css('background-color', default_bg);
        }, SPEED);
    });
}

$(function() {
    $(".terminate-listen").each(function(i) {
        var pattern_order = []
        var generation = $(this).attr('id');
        $(this).click(function() {
            $("div.hidden-notes").each(function(idx,r) {
                if($(this).attr('id') === generation) {
                    $(this).each(function(idx, child) {
                        pattern_order.push($(this).children().attr('id'));

                    })
                }
            });
            playPattern(pattern_order);
        });
    });
    original_notes = [];

    $("div#orig_notes > div").each(function(index) {
        original_notes.push([$(this).attr('id'), $(this).attr('class')]);
    });

    colors = {
            'A': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
            'B': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
            'C': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
            'D': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
            'E': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
            'F': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
            'G': '#'+(Math.random()*0xFFFFFF<<0).toString(16)};

    $('div#sortable-trait > div').each(function(index) {
        $(this).css({ 'background-color': colors[$(this).attr('id')[0]]});
    });

    $( "#sortable-trait" ).sortable({
        stop: function(event) {
              // calculate fitness
              console.log(get_ed());
        }
    });
    $( "#sortable-trait" ).disableSelection();

    $('#listen').click(function(){
        PATTERN = [];
        // NOTES = [];
        var adjusted_order = [];

        $('div#sortable-trait > div').each(function(index) {
            adjusted_order.push([$(this).attr('id'), $(this).attr('class')])
            PATTERN.push($(this).attr('id'));
            // NOTES.push($(this).attr('id'));
        });

        //var ed = euclidean_distance(original_notes, adjusted_order);
        //$("#current_score").html('Current Score: <small id="cs">' + ed + '/100</small>');

        playPattern(PATTERN);
    });

    $("#next-song").click(function() {
        $("#ns").submit();
    });

    $("#save-order").click(function(){
        var melody = new Array();
        var indi_id = $(this).attr("href");
        $("div#sortable-trait > div").each(function(index){
            /*  If I don't do it like this, then web.py WILL NOT
                receive duplicate objects (e.g. if the notes are
                C3 C3 A4 then webpy will only get 1 C3 and 1 A4).
                Ignore the multiple web requests -- doesn't matter.
            */
            var note = $(this).attr('id');
            // console.log(FITNESS_SCORE);
            $.ajax({
                type: 'POST',
                async: false,
                url: '/save_fitness/' + indi_id,
                data: {name: note, duration:1, trait_id: index, fitness: get_ed()}, // 1 is quarter I believe
                success: function(){
                    console.log("SUCCESSFUL!");
                    console.log(indi_id);
                }
            });
        })
    });

    $("#love").click(function() {
        $("#qf").submit();
    });

    $("#hate").click(function() {
        $("#qf").submit();
    });

});