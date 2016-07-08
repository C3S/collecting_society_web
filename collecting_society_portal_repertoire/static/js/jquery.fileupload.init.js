$(function () {
    'use strict';

    // Initialize the jQuery File Upload widget:
    var uploadUrl = $('#fileupload').attr('action');
    $('#fileupload').fileupload({
        // Uncomment the following to send cross-domain cookies:
        // xhrFields: {withCredentials: true},
        url: uploadUrl,
        uploadTemplateId: "template-upload",
        downloadTemplateId: "template-download",
        method: 'POST',
        dataType: 'json',
        acceptFileTypes: /(\.|\/)(mp3)$/i,
        maxFileSize: 40000000 // 40 MB
    });

    // // Enable iframe cross-domain access via redirect option:
    // $('#fileupload').fileupload(
    //     'option',
    //     'redirect',
    //     window.location.href.replace(
    //         /\/[^\/]*$/,
    //         '/cors/result.html?%s'
    //     )
    // );

    // Load existing files:
    $('#fileupload').addClass('fileupload-processing');
    $.ajax({
        // Uncomment the following to send cross-domain cookies:
        //xhrFields: {withCredentials: true},
        url: uploadUrl,
        dataType: 'json',
        context: $('#fileupload')[0]
    }).always(function () {
        $(this).removeClass('fileupload-processing');
    }).done(function (result) {
        $(this).fileupload('option', 'done')
            .call(this, $.Event('done'), {result: result});
    });

    // // Upload server status check for browsers with CORS support:
    // if ($.support.cors) {
    //     $.ajax({
    //         url: uploadUrl,
    //         type: 'HEAD'
    //     }).fail(function () {
    //         $('<div class="alert alert-danger"/>')
    //             .text('Upload server currently unavailable - ' +
    //                     new Date())
    //             .appendTo('#fileupload');
    //     });
    // }

});

