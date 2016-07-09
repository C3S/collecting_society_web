$(function () {
    'use strict';

    var uploadUrl = $('#fileupload').attr('action');

    // Initialize the jQuery File Upload widget:
    $('#fileupload').fileupload({
        xhrFields: {withCredentials: true},
        url: uploadUrl,
        uploadTemplateId: "template-upload",
        downloadTemplateId: "template-download",
        method: 'POST',
        dataType: 'json',
        acceptFileTypes: /(\.|\/)(mp3)$/i,
        maxFileSize: 1000000000, // 1 GB
        maxChunkSize:   1000000  // 1 MB
    });

    // Upload server status check for browsers with CORS support:
    if ($.support.cors) {
        $.ajax({
            xhrFields: {withCredentials: true},
            url: uploadUrl,
            type: 'HEAD'
        }).fail(function () {
            $('<div class="alert alert-danger"/>')
                .text('Upload server currently unavailable - ' +
                        new Date())
                .appendTo('#fileupload');
        });
    }

    // Load existing files:
    $('#fileupload').addClass('fileupload-processing');
    $.ajax({
        xhrFields: {withCredentials: true},
        url: uploadUrl,
        dataType: 'json',
        context: $('#fileupload')[0]
    }).always(function () {
        $(this).removeClass('fileupload-processing');
    }).done(function (result) {
        $(this).fileupload('option', 'done')
            .call(this, $.Event('done'), {result: result});
    });

});

// Play only one file at a time
$('#fileupload').delegate("audio", "click", function () {
    var _this = $(this);
    $(this).unbind("play").one("play", function() {
        $('audio').each(function (i, el) {
            if (!$(el).is(_this))
                $(el).trigger('pause');
        });
    });
});
