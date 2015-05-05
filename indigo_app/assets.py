from django_assets import Bundle, register

register('css', Bundle(
    'bower_components/bootstrap/dist/css/bootstrap.min.css',
    'bower_components/bootstrap/dist/css/bootstrap-theme.min.css',
    'bower_components/fontawesome/css/font-awesome.css',
    'bower_components/bootstrap-datepicker/css/datepicker3.css',
    'stylesheets/select2-4.0.0.min.css',
    Bundle(
        'stylesheets/app.scss',
        filters='pyscss',
        output='stylesheets/styles.%(version)s.css'),
    output='stylesheets/app.%(version)s.css'))

register('js', Bundle(
    'bower_components/jquery/dist/jquery.min.js',
    'bower_components/jquery-cookie/jquery.cookie.js',
    'bower_components/underscore/underscore-min.js',
    'bower_components/backbone/backbone.js',
    'bower_components/backbone.stickit/backbone.stickit.js',
    'bower_components/bootstrap/dist/js/bootstrap.min.js',
    'bower_components/handlebars/handlebars.min.js',
    'bower_components/moment/min/moment.min.js',
    'bower_components/moment/locale/en-gb.js',
    'bower_components/bootstrap-datepicker/js/bootstrap-datepicker.js',
    'bower_components/tablesorter/jquery.tablesorter.min.js',
    'javascript/select2-4.0.0.min.js',
    'javascript/caret.js',
    'javascript/prettyprint.js',
    'javascript/indigo/models.js',
    'javascript/indigo/views/user.js',
    'javascript/indigo/views/reset_password.js',
    'javascript/indigo/views/document_properties.js',
    'javascript/indigo/views/document_toc.js',
    'javascript/indigo/views/document_editor.js',
    'javascript/indigo/views/document.js',
    'javascript/indigo/views/library.js',
    'javascript/indigo/views/error_box.js',
    'javascript/indigo/views/import.js',
    'javascript/indigo/timestamps.js',
    'javascript/indigo.js',
    output='js/app.%(version)s.js'))

register('lime-js', Bundle(
    'lime/dist/app.js',
    output='js/lime.%(version)s.js'))

register('lime-css', Bundle(
    'lime/dist/resources/LIME-all.css',
    'lime/dist/resources/stylesheets/extjs4.editor.css',
    'lime/dist/resources/stylesheets/extjs4.viewport.css',
    output='stylesheets/lime.%(version)s.css'))
