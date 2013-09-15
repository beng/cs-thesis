colors = {
    'A': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'B': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'C': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'D': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'E': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'F': '#'+(Math.random()*0xFFFFFF<<0).toString(16),
    'G': '#'+(Math.random()*0xFFFFFF<<0).toString(16)
};

var Response = function(r) {
    this.params = r;
};

Response.prototype.generation = function() {
    return this.params.generation
};

Response.prototype.id = function() {
    return this.params.indi_id
};

Response.prototype.color = function(pitch) {
    return "background-color:".concat(colors[pitch], ";");
};

Response.prototype.render_style = function(pitch) {
    return "border:2px solid black;".concat(this.color(pitch));
};

Response.prototype.render_notes = function() {
    for(idx in this.params.notes) {
        var key = this.params.notes[idx];
        $("<div/>", {
            id: key.id,
            class: key.note,
            text: key.note,
            style: this.render_style(key.note[0]),
        }).appendTo("#sortable-trait");
    }
};

$(function() {
    var indi_id = $("#indi-id").attr("class");

    $.get('/individual', {
        id: indi_id,
    }, function(r) {
        var resp = new Response(JSON.parse(r));
        resp.render_notes();
    });

    $( "#sortable-trait" ).sortable({
        stop: function(event) {
          // calculate fitness
          // get_ed();
        }
    });

    $( "#sortable-trait" ).disableSelection();

    $("#play").click(function() {
        console.log("clicked play");
    });

    $("#stop").click(function() {
        console.log("clicked stop");
    })
});