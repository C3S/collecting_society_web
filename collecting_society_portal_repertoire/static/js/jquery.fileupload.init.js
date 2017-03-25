$(function () {
    'use strict';

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


    /*
        2DO: prevent further chunks being sent by client on error.
        Manual errors dont abort uploads. Http errors abort all uploads.
        Files with invalid extensions checked clientside are displayed,
        but not in the processed files array. This would be the desired state,
        after a chunk recieved a response with an error message in it,
        to be displayed to the user.
    */
    // // Prevent upload of chunks on error
    // $('#fileupload').bind('fileuploadchunksend', function (e, data) {
    //     $(lastResultFiles).each(function(){
    //         var result = this;
    //         if (result.error) {
    //             $(data.files).each(function(index, request){
    //                 if (request.name == result.name){
    //                     // data.abort();
    //                     // data.context.remove();
    //                     // data.files.error = true;
    //                     errorFiles[index] = request;
    //                     delete data.files[index];
    //                 }
    //             });
    //         }
    //     });
    // });
    // $('#fileupload').bind('fileuploadchunkalways', function (e, data) {
    //     lastResultFiles = (data.result ? data.result.files : []);
    //     $(errorFiles).each(function(index, file){
    //         data.files[index] = file;
    //     });
    // });

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
