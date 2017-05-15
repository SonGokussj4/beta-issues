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


// $('#issueStatus_editModal').on('show.bs.modal', function (event) {
//   var button = $(event.relatedTarget) // Button that triggered the modal
//   var iid = button.data('id') // Extract info from data-* attributes
//   var row_data = button.data('row_data')
//   // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
//   // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
//   var modal = $(this)
//   modal.find('.modal-title').text('ID: ' + iid)
//   modal.find('.modal-body span').text(row_data)
// })



