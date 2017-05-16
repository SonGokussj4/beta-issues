// templates/upload_release_changelog.html
// When user clicks on UPLOAD the loading button will start spinning...
$('#loading-forever-btn').click(function () {
    var btn = $(this)
    btn.button('loading')
    setTimeout(function(){
        btn.prop('value', 'still going..')
    }, 1000);
});

// Shows tooltip above selected element. Usage:
// <element data-toggle="tooltip" data-placement="top" title="Shown text">
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});


// Multiple addition of file in upload_release_changes.html

$(document).on('ready', function() {
    $("#input-1a").fileinput({
    uploadUrl: "not/working/for/now", // server upload action
    uploadAsync: true,
    minFileCount: 1,
    showUpload: false,
    showRemove: true,
    dropZoneEnabled: true,
    allowedFileExtensions: ['pdf'],
});
})
