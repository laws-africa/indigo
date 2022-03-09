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
      'click .edit-anntn': 'edit',
      'click .close-anntn': 'close',
      'click .btn.save': 'save',
      'click .btn.cancel': 'cancel',
      'click .btn.unedit': 'unedit',
      'click .create-anntn-task': 'createTask',
    },

    initialize: function(options) {
      this.template = options.template;
      this.listenTo(this.model, 'destroy', this.remove);
      this.document = options.document;

      // is this view dealing with starting a new annotation thread?
      this.isNew = this.model.isNew();
      this.listenTo(this.model, 'sync', this.saved);
      this.listenTo(this.model, 'change', this.render);

      this.render();
    },

    render: function() {
      var self = this;
      this.$el.empty();

      if (this.isNew) {
        // controls for adding a new annotation
        var template = $("#new-annotation-template")
            .clone()
            .attr('id', '')
            .show()
            .get(0);
        this.el.appendChild(template);
        this.$el.addClass('is-new');
      } else {
        var html = this.model.toHtml(),
            json = this.model.toJSON();

        json.html = html;
        if (json.task) {
          json.task = json.task.toJSON();
        }
        json.created_at_text = moment(json.created_at).fromNow();

        json.permissions = {
          'can_change': (Indigo.user.hasPerm('indigo_api.change_annotation') &&
              (Indigo.user.get('is_staff') ||
                  json.created_by_user && json.created_by_user.id == Indigo.user.get('id'))),
          'can_create_task': !json.task && Indigo.user.hasPerm('indigo_api.add_task'),
        };
        json.permissions.readonly = !(json.permissions.can_change || json.permissions.can_create_task);

        this.$el.append(this.template(json));
      }
    },

    delete: function(e) {
      if (confirm("Are you sure?")) {
        this.remove();
        this.model.destroy();
      }
    },

    saved: function() {
      this.isNew = false;
      this.$el.removeClass('is-new');
      this.render();
    },

    cancel: function(e) {
      this.remove();
      this.model.destroy();
    },

    save: function(e) {
      var text = this.$el.find('textarea').val();
      if (!text) return;

      this.model.set('text', text);
      this.model.save();
    },

    edit: function(e) {
      var $textarea = $(document.createElement('textarea'));
      $textarea.addClass('form-control').val(this.model.get('text'));

      this.$el
          .find('.button-container')
          .append('<button class="btn btn-primary btn-sm save">Save</button>')
          .append('<button class="btn btn-outline-secondary btn-sm unedit float-right">Cancel</button>')
          .end()
          .find('.content')
          .replaceWith($textarea);

      $textarea.focus().trigger('input');
    },

    unedit: function(e) {
      e.stopPropagation();
      this.render();
    },

    close: function(e) {
      if (confirm('Are you sure you want to resolve this?')) {
        this.model.set('closed', true);
        this.model.save();
      }
    },

    createTask: function(e) {
      // create a task based on this annotation
      this.model.createTask();
    },
  });


  /** This view handles a thread of annotations.
   *
   * A thread is anchored to a place (the target) in the document using W3C Annotation compliant selectors.
   *
   * The target is determined by an anchor element and list of selectors. The selectors are relative to the
   * anchor element. The anchor is determined by the nearest element with an ID.
   *
   * We use two selectors, based on the W3C Annotations Model (https://www.w3.org/TR/annotation-model/)
   * and using https://github.com/tilgovi/dom-anchor-text-quote and https://github.com/tilgovi/dom-anchor-text-position.
   *
   * 1. The first is a TextPositionSelector that simply specifies the start and
   *    end offset of the annotation in the text of the anchor element.
   *    (https://www.w3.org/TR/annotation-model/#text-position-selector)
   *
   * 2. The second is a TextQuoteSelector that includes the selected text, and some context
   *    from just before and just after it.
   *    https://www.w3.org/TR/annotation-model/#text-quote-selector
   *
   * These selectors are used together to determine what text should be highlighted. Together, they make the
   * system somewhat robust against changes to the highlighted text. See https://web.hypothes.is/blog/fuzzy-anchoring/
   * for inspiration.
   *
   * First, we try to find the text with the TextPositionSelector. We then check the result against the
   * TextQuoteSelector's "exact" selected text. If they match, then we've selected the right text. This
   * makes the common case fast.
   *
   * If they don't match, then we try a fuzzy match using the TextQuoteSelector. If that doesn't match,
   * we give up.
   */
  Indigo.AnnotationThreadView = Backbone.View.extend({
    className: 'annotation-thread ig',
    tagName: 'la-gutter-item',
    events: {
      'click button.post': 'postReply',
      'focus textarea': 'replyFocus',
      'blur textarea': 'replyBlur',
      'click': 'focus',
      'input textarea': 'textareaChanged',
    },

    initialize: function(options) {
      this.annotationTemplate = options.template;
      this.document = options.document;
      this.anchorRoot = options.root;
      this.marks = [];
      // this is used in the gutter
      this.contentElement = this.el;

      // root annotation
      this.root = this.model.root();

      // target for converting to a range
      this.target = {
        anchor_id: this.root.get('anchor_id'),
        selectors: this.root.get('selectors'),
      };

      // views for each annotation
      this.annotationViews = this.model.annotations.map(function(note) {
        /**
         * Comments from tasks (fake annotations) appended to the annotation
         * thread appeared as new empty annotations field since they lack IDs.
         *
         * They come as a note model with an empty note.id, therefore, we set the
         * autogenerated note.cid as the model's id so that it can be rendered as
         * a normal reply.
         *
         * Each note has a note.attributes element that contains the data of a note.
         * The note.attributes element has an attributes.id field that is null and thus we fill
         * it using the autogenerated note.cid so that they can be rendered as
         * normal reply to annotations.
         */
        if (note.id === null && note.attributes.text !== null){
          note.id = note.cid;
          note.attributes.id = note.cid;
        }
        return new Indigo.AnnotationView({
          model: note,
          template: options.template,
          document: options.document,
        });
      });

      this.listenTo(this.model, 'destroy', this.destroyed);
      this.listenTo(this.model.annotations, 'remove', this.annotationRemoved);
      this.listenTo(this.root, 'change:closed', this.setClosed);
      $('body').on('click', _.bind(this.blurred, this));

      this.render();
    },

    render: function() {
      this.$el.empty();

      this.annotationViews.forEach(function(note) {
        this.el.appendChild(note.el);
      }, this);

      if (Indigo.user.hasPerm('indigo_api.add_annotation')) {
        $('<div class="annotation reply-container">')
            .append('<textarea class="form-control reply-box" placeholder="Reply...">')
            .append('<button class="btn btn-primary btn-sm post hidden" disabled>Reply</button>')
            .appendTo(this.el);
      }
    },

    setClosed: function() {
      this.$el.toggleClass('closed', this.root.get('closed'));

      if (this.root.get('closed')) {
        this.blur();
        this.unmark();
        this.$el.remove();
        this.trigger('closed', this);
      } else {
        this.display();
      }
    },

    display: function() {
      var range;

      if (this.root.get('closed')) return;

      this.unmark();
      range = Indigo.dom.targetToRange(this.target, this.anchorRoot);

      if (range && this.mark(range)) {
        // gutter uses this for positioning
        this.el.anchor = this.marks[0];

        // the DOM elements get rudely removed from the view when the document
        // sheet is re-rendered, which seems to break event handlers, so
        // we have to re-bind them
        this.delegateEvents();
        this.annotationViews.forEach(function(v) { v.delegateEvents(); });
        return true;
      }
      this.el.anchor = null;
      return false;
    },

    mark: function(range) {
      var self = this,
          handler = _.bind(this.markClicked, this);

      this.marks = [];
      Indigo.dom.markRange(range, 'mark', function (mark) {
        self.marks.push(mark);
        mark.addEventListener('click', handler);
      });

      return this.marks.length > 0;
    },

    unmark: function() {
      this.marks.forEach(function(mark) {
        while (mark.firstChild) {
          mark.parentElement.insertBefore(mark.firstChild, mark);
        }
        mark.parentElement.removeChild(mark);
      });
      this.marks = [];
    },

    markClicked: function(e) {
      e.stopPropagation();
      // fake a click on the element to blur any currently active annotation
      this.el.click();
    },

    focus: function() {
      this.el.active = true;
      this.marks.forEach(function(mark) { mark.classList.add('active'); });
    },

    blurred: function(e) {
      const gutter = this.el.closest('la-gutter');
      if (e.target.contains(gutter) && !(this.el == e.target || jQuery.contains(this.el, e.target))) {
        this.blur();
      }
    },

    blur: function() {
      this.el.active = false;
      this.marks.forEach(function(mark) { mark.classList.remove('active'); });
    },

    replyFocus: function(e) {
      $(e.target).closest('.annotation').find('.btn.post').removeClass('hidden');
    },

    replyBlur: function(e) {
      $(e.target).closest('.annotation').find('.btn.post').toggleClass('hidden', this.$el.find('textarea').val() === '');
    },

    postReply: function(e) {
      var text = this.$el.find('textarea').val(),
          view,
          reply,
          self = this;

      this.$el.find('.btn.post').prop('disabled', true);
      reply = this.model.add({text: text});
      reply
          .save()
          .then(function() {
            view = new Indigo.AnnotationView({
              model: reply,
              template: self.annotationTemplate,
              document: self.document,
            });
            self.annotationViews.push(view);

            view.$el.insertBefore(self.$el.find('.reply-container')[0]);

            self.$el.find('textarea').val('');
            self.$el.find('.btn.post').addClass('hidden');

            self.trigger('resized', this);
          });
    },

    annotationRemoved: function() {
      this.trigger('resized', this);
    },

    destroyed: function() {
      this.blur();
      this.unmark();
      this.remove();
      this.trigger('deleted', this);
    },

    textareaChanged: function(e) {
      var input = e.currentTarget;

      $(input)
          .siblings('.btn.save, .btn.post')
          .attr('disabled', input.value.trim() === '');


      if (input.scrollHeight > input.clientHeight) {
        input.style.height = input.scrollHeight + "px";
      }
    },
  });


  /**
   * Handle all the annotations in a document
   */
  Indigo.DocumentAnnotationsView = Backbone.View.extend({
    el: ".document-workspace-content",
    events: {
      'click #new-annotation-floater': 'newAnnotation',
      'click .next-annotation': 'nextAnnotation',
      'click .prev-annotation': 'prevAnnotation',
    },

    initialize: function(options) {
      this.prefocus = options.prefocus;
      this.annotatable = this.model.tradition().settings.annotatable;
      this.contentContainer = this.el.querySelector('.content-with-gutter');
      this.$annotationNav = this.$el.find('.annotation-nav');
      this.annotationTemplate = Handlebars.compile($("#annotation-template").html());
      document.addEventListener('selectionchange', _.bind(this.selectionChanged, this));

      this.newButton = this.makeFloatingButton();
      this.newButtonTimeout = null;

      this.newButtonItem = document.createElement('la-gutter-item');
      this.newButtonItem.appendChild(this.newButton);

      this.gutter = this.el.querySelector('.gutter la-gutter');
      this.gutter.akomaNtoso = this.el.querySelector('.content-with-gutter > .content');

      this.counts = new Backbone.Model();
      this.listenTo(this.counts, 'change', this.renderCounts);

      this.threadViews = [];
      this.visibleThreads = [];
      this.threads = this.model.annotationThreads();
      this.listenTo(this.threads, 'add', this.makeView);
      this.listenTo(this.threads, 'reset', this.reset);
      this.listenTo(this.threads, 'add remove reset', this.count);
      this.listenTo(this.threads.annotations, 'change:closed', this.count);
      this.reset();
    },

    makeFloatingButton: function() {
      const i = document.createElement('i');
      i.className = 'fas fa-comment';
      const button = document.createElement('div');
      button.id = 'new-annotation-floater';
      button.appendChild(i);

      return button;
    },

    reset: function() {
      this.threadViews = [];
      this.visibleThreads = [];
      this.counts.set({threads: 0});
      this.threads.forEach(t => this.makeView(t));
      this.renderAnnotations();
    },

    makeView: function(thread) {
      var view = new Indigo.AnnotationThreadView({
        model: thread,
        template: this.annotationTemplate,
        document: this.model,
        root: this.contentContainer,
      });

      this.listenTo(view, 'deleted', this.threadDeleted);
      this.listenTo(view, 'closed', this.threadClosed);
      this.threadViews.push(view);
      if (view.display()) {
        this.gutter.appendChild(view.el);
        this.visibleThreads.push(view);
      }

      return view;
    },

    count: function() {
      this.counts.set({
        threads: this.visibleThreads.length,
      });
    },

    threadDeleted: function(view) {
      this.threadViews = _.without(this.threadViews, view);
      this.visibleThreads = _.without(this.visibleThreads, view);
      this.counts.set({
        threads: this.visibleThreads.length,
      });
      this.renderCounts();
      view.el.remove();
    },

    threadClosed: function(view) {
      this.visibleThreads = _.without(this.visibleThreads, view);
    },

    renderAnnotations: function() {
      // TODO: this gets called every time a new TOC entry is selected,
      // so it will always attempt to prefocus an annotation. It just so happens
      // that the click events prevent anything after the initial prefocus from
      // working. It's dirty, we should only prefocus on the first render.
      var prefocus = this.prefocus,
          gutter = this.gutter,
          visible = [];

      this.threadViews.forEach(function(v) {
        if (v.display()) {
          gutter.appendChild(v.el);
          visible.push(v);

          if (prefocus && (v.model.annotations.at(0).get('id') || "").toString() === prefocus) {
            v.el.active = true;
            v.el.scrollIntoView();
          }
        }
      });

      this.visibleThreads = visible;
      this.counts.set('threads', visible.length);
    },

    renderCounts: function() {
      var count = this.counts.get('threads');
      this.$annotationNav.find('.n-threads').text(count);
      this.$annotationNav.toggleClass('d-none', count === 0);
    },

    // setup a new annotation thread
    newAnnotation: function(e) {
      var target, thread;

      e.stopPropagation();
      this.removeNewButton();

      // don't go outside of the AKN document
      target = Indigo.dom.rangeToTarget(this.pendingRange, this.contentContainer);
      if (!target) return;


      // createThread triggers add, the makeView which appends la-gutter-item
      thread = this.threads.createThread({selectors: target.selectors, anchor_id: target.anchor_id, closed: false});

      this.threadViews.forEach(v => {
        if (v.model === thread) {
          v.display();

          const layoutCompleteHandler = () => {
            v.el.querySelector('textarea:first-child').focus();
            this.gutter.removeEventListener('layoutComplete', layoutCompleteHandler);
          };
          this.gutter.addEventListener("layoutComplete", layoutCompleteHandler);
          v.el.active = true;
        }
      });

    },

    removeNewButton: function() {
      this.newButtonItem.remove();
      this.newButtonTimeout = null;
    },

    nextAnnotation: function(e) {
      e.preventDefault();
      e.stopPropagation();
      this.removeNewButton();

      // is there an active item?
      this.gutter.activateNextItem().then((activeItem) => {
        this.handleScrollForActiveItem(activeItem);
      });
    },

    prevAnnotation: function(e) {
      e.preventDefault();
      e.stopPropagation();
      this.removeNewButton();

      this.gutter.activatePrevItem().then((activeItem) => {
        this.handleScrollForActiveItem(activeItem);
      });
    },

    handleScrollForActiveItem: function (item) {
      const handler = () => {
        this.gutter.removeEventListener('layoutComplete', handler);

        const container = item.closest('.document-sheet-container');
        if (container) {
          container.scrollTo({
            top: parseFloat(item.style.top.replace('px', '')) - 50,
            behavior: 'smooth',
          });
        }
      };
      this.gutter.addEventListener('layoutComplete', handler);
    },

    selectionChanged: function(e) {
      var range, root,
          sel = document.getSelection();

      if (sel.rangeCount > 0 && !sel.getRangeAt(0).collapsed) {
        if (this.newButtonTimeout) window.clearTimeout(this.newButtonTimeout);

        range = sel.getRangeAt(0);
        root = this.contentContainer.querySelector('la-akoma-ntoso');

        // is the common ancestor inside the akn container?
        if (range.commonAncestorContainer.compareDocumentPosition(root) & Node.DOCUMENT_POSITION_CONTAINS) {
          // disallow comments in editables
          if ($(range.startContainer).closest('.cke_editable').length) return;
          if ($(range.endContainer).closest('.cke_editable').length) return;

          // find first element
          root = range.startContainer;
          while (root && root.nodeType !== Node.ELEMENT_NODE) root = root.parentElement;

          this.pendingRange = range;
          this.newButtonItem.anchor = root;
          if (!this.gutter.contains(this.newButtonItem)) {
            this.gutter.appendChild(this.newButtonItem);
          }
        }
      } else {
        // this needs to stick around for a little bit, for the case
        // where the selection has been cleared because the button is
        // being clicked
        this.newButtonTimeout = window.setTimeout(_.bind(this.removeNewButton, this), 200);
      }
    },
  });
})(window);
