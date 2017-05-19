(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /** This view handles a single annotation in a thread.
   */
  Indigo.AnnotationView = Backbone.View.extend({
    className: function() {
      return 'annotation ' + (!this.model.get('in_reply_to') ? 'root' : 'reply');
    },
    events: {
    },
    bindings: {
    },

    initialize: function(options) {
      this.template = options.template;
      this.render();
      //this.stickIt();
    },

    render: function() {
      this.$el.empty().append(this.template(this.model.toJSON()));
    },
  });


  /** This view handles a thread of annotations.
   */
  Indigo.AnnotationThreadView = Backbone.View.extend({
    className: 'annotation-thread ig',

    initialize: function(options) {
      // root annotation
      this.root = this.model.find(function(a) { return !a.get('in_reply_to'); });
      // views for each annotation
      this.annotationViews = this.model.map(function(note) {
        return new Indigo.AnnotationView({model: note, template: options.template});
      });

      this.render();
    },

    render: function() {
      this.$el.empty();

      this.annotationViews.forEach(function(note) { 
        note.render();
        this.el.appendChild(note.el);
      }, this);
    },

    display: function() {
      var node = document.getElementById(this.root.get('anchor').id);
      if (node) node.appendChild(this.el);
    },
  });


  /**
   * Handle all the annotations in a document
   */
  Indigo.DocumentAnnotationsView = Backbone.View.extend({
    initialize: function() {
      this.annotations = new Backbone.Collection();
      this.annotations.add([{
        id: 1,
        anchor: {
          id: 'section-1.1.1',
        },
        text: 'this is my annotation',
        created_by_user: {
          id: 1,
          display_name: 'Greg K.',
        },
      }, {
        id: 2,
        anchor: {
          id: 'section-1.1.2',
        },
        text: 'and another one',
        created_by_user: {
          id: 1,
          display_name: 'Greg K.',
        },
      }, {
        id: 3,
        anchor: {
          id: 'section-1.1.2',
        },
        text: 'a reply to someone',
        created_by_user: {
          id: 1,
          display_name: 'Greg K.',
        },
        in_reply_to: 2,
      }]);

      // group by thread and transform into collections
      var threads = _.map(this.annotations.groupBy(function(a) {
        return a.get('in_reply_to') || a.get('id');
      }), function(notes) {
        return new Backbone.Collection(notes);
      });

      var template = this.annotationTemplate = Handlebars.compile($("#annotation-template").html());

      this.threadViews = threads.map(function(thread) {
        return new Indigo.AnnotationThreadView({model: thread, template: template});
      });
    },

    renderAnnotations: function() {
      this.threadViews.forEach(function(v) { v.display(); });
    },
  });
})(window);
