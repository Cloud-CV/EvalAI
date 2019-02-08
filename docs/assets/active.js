$(document).ready(function() {
    // Highlight the home tab
    $(function () {
      $('ul.primary-nav li a').removeClass('active');
      $('ul.primary-nav li a.home').addClass('active');
    });
});

function scroll_to_anchor(anchor_id){
    var tag = $("#"+ anchor_id);
    $('html,body').animate({scrollTop: tag.offset().top},'fast');
}

$("#main-button").click(function() {
   scroll_to_anchor('examples');
});
