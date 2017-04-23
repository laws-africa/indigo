$('.references > li a').on('click', function(e) {
  ga('send', 'event', 'resolver-click', e.target.getAttribute("data-authority"), e.target.href);
});
