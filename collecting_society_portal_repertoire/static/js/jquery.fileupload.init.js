$(function () {
    'use strict';

    /*
        2DOs: 
        - pause button with expected user feedback
        - autoresume on certain errors with max retries
        - activate dropzone
    */

    var data = $('#data');
    var apiUrl = data.data('url');
    var extensions = data.data('extensions').split(',');
    var lastResultFiles = [];
    var errorFiles = [];

    // Initialize the jQuery File Upload widget:
    $('#fileupload').fileupload({
        xhrFields: {withCredentials: true},
        url: apiUrl + '/upload',
        uploadTemplateId: "template-upload",
        downloadTemplateId: "template-download",
        method: 'POST',
        dataType: 'json',
        acceptFileTypes: new RegExp("(\.|\/)("+extensions.join('|')+")$", "i"),
        maxFileSize: 1024*1024*1024, // 1 GB
        maxChunkSize: 1024*1024, // 1 MB
        prependFiles: true,
    });

    // Resume temporary upload at last position
    $('#fileupload').fileupload({
        add: function (e, data) {
            var that = this;
            $.ajax({
                xhrFields: {withCredentials: true},
                url: apiUrl + '/show/' + data.files[0].name,
                dataType: 'json'
            }).done(function (result) {
                data.uploadedBytes = result.name && result.size;
                $.blueimp.fileupload.prototype
                    .options.add.call(that, e, data);
            });
        }
    });

    // Abort chunkupload on serverside error
    $('#fileupload').bind("fileuploadchunksend", function (e, data) {
        var abortChunkSend = data.context[0].abortChunkSend;
        var error = data.context[0].error;
        if (abortChunkSend) {
            data.files[0].error = error;
            return false;
        }
    });
    $('#fileupload').bind("fileuploadchunkdone", function (e, data) {
        if (data.result) {
            for (var index = 0; index < data.result.files.length; index++) {
                var file = data.result.files[index];
                if (file.error) {
                    data.context[index].abortChunkSend = true;
                    data.context[index].error = file.error;
                }
            }
        }
    });

    // Load existing files:
    $('#fileupload').addClass('fileupload-processing');
    $.ajax({
        xhrFields: {withCredentials: true},
        url: apiUrl + "/list",
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
    var that = $(this);
    $(this).unbind("play").one("play", function() {
        $('audio').each(function (i, el) {
            if (!$(el).is(that))
                $(el).trigger('pause');
        });
    });
});
