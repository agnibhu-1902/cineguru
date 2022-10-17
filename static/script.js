document.addEventListener("DOMContentLoaded", function(){
  window.addEventListener('scroll', function() {
        document.getElementById('navbar_top').classList.add('fixed-top');
        // add padding top to show content behind navbar
        navbar_height = document.querySelector('.navbar').offsetHeight;
        document.body.style.paddingTop = navbar_height + 'px';
  });
});
// DOMContentLoaded  end