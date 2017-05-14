$('#loading-forever-btn').click(function () {
    var btn = $(this)
    btn.button('loading')
    setTimeout(function(){
        btn.prop('value', 'still going..')
    }, 1000);
});