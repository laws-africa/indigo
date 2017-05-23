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
      'click .delete-anntn': 'delete',
    },

    initialize: function(options) {
      this.template = options.template;
      this.listenTo(this.model, 'destroy', this.remove);

      this.render();
    },

    render: function() {
      this.$el.empty().append(this.template(this.model.toJSON()));
    },
    
    delete: function(e) {
      if (confirm("Are you sure?")) {
        this.remove();
        this.model.destroy();
      }
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

      this.listenTo(this.model, 'destroy', this.annotationDeleted);

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

      // the DOM elements get rudely remove from the view when the document
      // sheet is re-rendered, which seems to break event handlers, so
      // we have to re-bind them
      this.delegateEvents();
      this.annotationViews.forEach(function(v) { v.delegateEvents(); });
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
          view,
          reply;

      // TODO: format the text?

      reply = Indigo.Annotation.newForCurrentUser({
        text: text,
        in_reply_to: this.root.get('id'),
      });
      view = new Indigo.AnnotationView({model: reply, template: this.annotationTemplate});

      // TODO: save it

      this.model.add(reply);
      this.annotationViews.push(view);

      view.$el.insertBefore(this.$el.find('.reply-container')[0]);

      this.$el.find('textarea').val('');
    },

    annotationDeleted: function(note) {
      if (this.root == note) {
        if (this.model.length > 0) {
          // delete everything else
          this.model.toArray().forEach(function(n) { n.destroy(); });
        }

        this.remove();
        this.trigger('deleted', this);
      }
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
      this.annotations = new Indigo.AnnotationList();
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
        var thread = new Backbone.Collection(notes);
        notes.forEach(function(n) { n.thread = thread; });
        return thread;
      });

      var template = this.annotationTemplate = Handlebars.compile($("#annotation-template").html());
      this.threadViews = threads.map(_.bind(this.makeView, this));

      this.$newButton = $("#new-annotation-floater");
      this.$newBox = $("#new-annotation-box");
      this.$el.on('mouseenter', '.akn-subsection', _.bind(this.enterSection, this));
    },

    makeView: function(thread) {
      var view = new Indigo.AnnotationThreadView({model: thread, template: this.annotationTemplate});
      this.listenTo(view, 'deleted', this.threadDeleted);
      return view;
    },

    threadDeleted: function(view) {
      this.threadViews = _.without(this.threadViews, view);
    },

    renderAnnotations: function() {
      this.threadViews.forEach(function(v) { v.display(); });
    },

    enterSection: function(e) {
      if (!Indigo.userView.model.authenticated()) return;

      if ($(e.currentTarget).find(".annotation-thread").length === 0) {
        e.currentTarget.appendChild(this.$newButton[0]);
        this.$newButton.show();
      } else {
        this.$newButton.hide();
      }
    },

    newAnnotation: function(e) {
      // XXX
      var $anchor = this.$newButton.closest('.akn-subsection');

      this.$newButton.hide();
      this.$newBox
        .appendTo($anchor)
        .data('anchor-id', $anchor.attr('id'))
        .show()
        .find('textarea')
        .focus();
    },

    cancelNewAnnotation: function(e) {
      this.$newBox.remove().find('textarea').val('');
    },

    saveNewAnnotation: function(e) {
      // TODO: format the text?
      var text = this.$newBox.find('textarea').val();

      var note = Indigo.Annotation.newForCurrentUser({
        text: text,
        anchor: {
          // XXX
          id: this.$newBox.closest('.akn-subsection').attr('id'),
        },
      });

      // TODO: save it
      var thread = new Backbone.Collection([note]);
      var view = this.makeView(thread);
      this.threadViews.push(view);

      this.$newBox.hide().find('textarea').val('');

      view.display();
    },
  });
})(window);
