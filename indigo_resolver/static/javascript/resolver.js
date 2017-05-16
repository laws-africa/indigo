$('.references > li a').on('click', function(e) {
  ga('send', 'event', 'resolver-click', e.target.getAttribute("data-authority"), e.target.href);
});

// send event if we didn't find any resolvers
if ($('body.resolver').hasClass('no-refs')) {
  ga('send', 'event', 'resolver-no-refs', $('body').data('frbr-uri'));
}
