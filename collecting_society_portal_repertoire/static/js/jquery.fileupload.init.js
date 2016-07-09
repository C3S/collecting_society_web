$(function () {
    'use strict';

    var apiUrl = $('#apiurl').data('url');

    // Initialize the jQuery File Upload widget:
    $('#fileupload').fileupload({
        xhrFields: {withCredentials: true},
        url: apiUrl + '/upload',
        uploadTemplateId: "template-upload",
        downloadTemplateId: "template-download",
        method: 'POST',
        dataType: 'json',
        acceptFileTypes: /(\.|\/)(mp3)$/i,
        maxFileSize: 1000000000, // 1 GB
        maxChunkSize:   1000000, // 1 MB
        // resume upload
        add: function (e, data) {
            var that = this;
            $.ajax({
                xhrFields: {withCredentials: true},
                url: apiUrl + '/show/' + data.files[0].name,
                dataType: 'json'
            }).done(function (result) {
                data.uploadedBytes = result.resumable && result.size;
                $.blueimp.fileupload.prototype
                    .options.add.call(that, e, data);
            });
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
