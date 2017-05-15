// templates/upload_release_changelog.html
// When user clicks on UPLOAD the loading button will start spinning...
$('#loading-forever-btn').click(function () {
    var btn = $(this)
    btn.button('loading')
    setTimeout(function(){
        btn.prop('value', 'still going..')
    }, 1000);
});
