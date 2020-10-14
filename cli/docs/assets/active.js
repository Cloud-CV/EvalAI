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

$(document).ready(function() {
    $("body").tooltip({ selector: '[data-toggle=tooltip]' });
    $.notify.addStyle('notification', {
        html: "<div><span data-notify-text/></div>",
        classes: {
          base: {
            "white-space": "nowrap",
            "color": "white",
            "background-color": "black",
            "padding": "12px",
            "border-radius": "24px",
            "width": "auto",
            "font-weight": "300"
          },
          
        }
      });   
});

 // Show the button when scrolled till 100px
window.onscroll = function() {scrollFunction()};

 function scrollFunction() {
  if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
    document.getElementById("up-arrow").style.display = "block";
  } else {
    document.getElementById("up-arrow").style.display = "none";
  }
}

 // Scroll to the top
function topFunction() {
  document.body.scrollTop = 0; 
  document.documentElement.scrollTop = 0; 
}



function CopyToClipboard(elementId) {
  var aux = document.createElement("input");
  var command = document.getElementById(elementId).innerHTML ; 
  command = command.replace('&lt;', '<').replace('&gt;', '>');
  aux.setAttribute("value", command);
  document.body.appendChild(aux);
  aux.select();
  document.execCommand("copy");
  document.body.removeChild(aux);
  $.notify("Command copied to clipboard", {
      style: 'notification'
  });
}
