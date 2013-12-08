$(function() {
    $("#export-btn").click(function() {
        $("input:checkbox:checked").each(function(btn) {
            var export_uri = '/population/export/' + $(this).attr('id') + '/' + $(this).val();
            $.get(export_uri, function(resp) {
                console.log(resp);
            });
        });
    });
});
