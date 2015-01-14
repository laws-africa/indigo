from django_assets import Bundle, register

register('css', Bundle(
    'bower_components/bootstrap/dist/css/bootstrap.min.css',
    'bower_components/bootstrap/dist/css/bootstrap-theme.min.css',
    'bower_components/fontawesome/css/font-awesome.css',
    Bundle(
        'stylesheets/*.scss',
        filters='pyscss',
        output='stylesheets/styles.%(version)s.css'),
    output='stylesheets/app.%(version)s.css'))

register('js', Bundle(
    'bower_components/jquery/dist/jquery.min.js',
    'bower_components/underscore/underscore-min.js',
    'bower_components/backbone/backbone.js',
    'bower_components/backbone.stickit/backbone.stickit.js',
    'bower_components/bootstrap/dist/js/bootstrap.min.js',
    'javascript/indigo/models.js',
    'javascript/indigo/views/document.js',
    'javascript/indigo.js',
    output='js/app.%(version)s.js'))
