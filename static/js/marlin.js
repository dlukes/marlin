function makeConc() {
  var corpus = $('#corpus').val();
  var cql = $('#cql').val();
  var url = '/conc/' +
        encodeURIComponent(corpus) + '/' +
        encodeURIComponent(cql) + '/1';
  Turbolinks.visit(url);
}

$(document).ready(function() {
  $(document).keydown(function(e) {
    if (e.ctrlKey && e.keyCode == 13) {
      e.preventDefault();
      makeConc();
    }
  });

  $("form input").keydown(function(e) {
    if (e.keyCode == 13) {
      e.preventDefault();
      search();
    }
  });

  // a crude but simple way of checking whether we need to adjust the body
  // padding based on the height of the navbar -- just do it on every mouseup
  // (some of these will be tied to resizing the textarea, i.e. the navbar as
  // well)
  $(document).mouseup(function() {
    var navHeight = $(".navbar").height();
    $("body").css("padding-top", navHeight + 5);
  });
});
