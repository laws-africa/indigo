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
    events: {
      'click button.post': 'postReply',
      'focus textarea': 'replyFocus',
      'blur textarea': 'replyBlur',
      'click': 'focused',
    },

    initialize: function(options) {
      // root annotation
      this.root = this.model.find(function(a) { return !a.get('in_reply_to'); });
      this.annotationTemplate = options.template;

      // views for each annotation
      this.annotationViews = this.model.map(function(note) {
        return new Indigo.AnnotationView({model: note, template: options.template});
      });

      this.render();

      $('body').on('click', _.bind(this.blurred, this));
    },

    render: function() {
      this.$el.empty();

      this.annotationViews.forEach(function(note) { 
        this.el.appendChild(note.el);
      }, this);

      $('<div class="annotation reply-container">')
        .append('<textarea class="form-control reply-box" placeholder="Reply...">')
        .append('<button class="btn btn-info btn-sm post hidden">Reply</button>')
        .appendTo(this.el);
    },

    display: function() {
      var node = document.getElementById(this.root.get('anchor').id);
      if (node) node.appendChild(this.el);
    },

    focused: function() {
      this.$el.addClass('focused');
    },

    blurred: function(e) {
      if (!(this.el == e.target || jQuery.contains(this.el, e.target))) {
        this.$el.removeClass('focused');
      }
    },

    replyFocus: function(e) {
      this.$el.find('.btn.post').removeClass('hidden');
    },

    replyBlur: function(e) {
      this.$el.find('.btn.post').toggleClass('hidden', this.$el.find('textarea').val() === '');
    },

    postReply: function(e) {
      var text = this.$el.find('textarea').val(),
          user = Indigo.userView.model,
          view,
          reply;

      // TODO: format the text?

      reply = new Indigo.Annotation({
        text: text,
        in_reply_to: this.root.get('id'),
        created_by_user: {
          id: user.get('id'),
          display_name: user.get('first_name'), // XXX
        }
      });
      view = new Indigo.AnnotationView({model: reply, template: this.annotationTemplate});

      // TODO: save it

      this.model.add(reply);
      this.annotationViews.push(view);

      view.$el.insertBefore(this.$el.find('.reply-container')[0]);

      this.$el.find('textarea').val('');
    },
  });


  /**
   * Handle all the annotations in a document
   */
  Indigo.DocumentAnnotationsView = Backbone.View.extend({
    el: "#document-sheet",
    events: {
      'click #new-annotation-floater': 'newAnnotation',
      'click #new-annotation-box .cancel': 'cancelNewAnnotation',
      'click #new-annotation-box .save': 'saveNewAnnotation',
    },

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

      this.$newButton = $("#new-annotation-floater");
      this.$newBox = $("#new-annotation-box");
      this.$el.on('mouseenter', '.akn-subsection', _.bind(this.enterSection, this));
    },

    renderAnnotations: function() {
      this.threadViews.forEach(function(v) { v.display(); });
    },

    enterSection: function(e) {
      if ($(e.currentTarget).find(".annotation-thread").length === 0) {
        e.currentTarget.appendChild(this.$newButton[0]);
        this.$newButton.show();
      } else {
        this.$newButton.hide();
      }
    },

    newAnnotation: function(e) {
      this.$newButton
        .hide()
        .closest('.akn-subsection')
        .append(this.$newBox);

      this.$newBox.show().find('textarea').focus();
    },

    cancelNewAnnotation: function(e) {
      this.$newBox.hide().find('textarea').val('');
    },

    saveNewAnnotation: function(e) {
      // TODO: format the text?
      var text = this.$newBox.find('textarea').val(),
          user = Indigo.userView.model;

      var note = new Indigo.Annotation({
        text: text,
        anchor: {
          // XXX
          id: this.$newBox.closest('.akn-subsection').attr('id'),
        },
        created_by_user: {
          id: user.get('id'),
          display_name: user.get('first_name'), // XXX
        }
      });

      // TODO: save it
      var thread = new Backbone.Collection([note]);
      var view = new Indigo.AnnotationThreadView({model: thread, template: this.annotationTemplate});
      this.threadViews.push(view);

      this.$newBox.hide().find('textarea').val('');

      view.display();
    },
  });
})(window);
