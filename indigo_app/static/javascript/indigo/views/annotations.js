(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;
  Indigo.annotations  = Indigo.annotations || {};

  /**
   * Given a browser Range object, transform it into a target description
   * suitable for use with annotations.
   */
  Indigo.annotations.rangeToTarget = function(range) {
    var anchor = range.commonAncestorContainer,
      target = {selectors: []},
      selector;

    // TODO: handle no id element (ie. body, preamble, etc.)
    anchor = $(anchor).closest('[id]')[0];
    // TODO: data-id?
    target.anchor_id = anchor.getAttribute('id');

    // position selector
    selector = textPositionFromRange(anchor, range);
    selector.type = "TextPositionSelector";
    target.selectors.push(selector);

    // quote selector, based on the position
    selector = textQuoteFromTextPosition(anchor, selector);
    selector.type = "TextQuoteSelector";
    target.selectors.push(selector);

    return target;
  };

  /**
   * Given an annotation target object, convert it into a browser
   * Range object.
   */
  Indigo.annotations.targetToRange = function(target) {
    // TODO: scope, look upwards, etc.
    var anchor = document.getElementById(target.anchor_id),
      posnSelector = _.findWhere(target.selectors, {type: "TextPositionSelector"}),
      quoteSelector = _.findWhere(target.selectors, {type: "TextQuoteSelector"}),
      range;

    if (posnSelector) {
      range = textPositionToRange(anchor, posnSelector);

      // compare text with the exact from the quote selector
      if (quoteSelector && range.toString() === quoteSelector.exact) {
        return range;
      }
    }

    // fall back to the quote selector
    if (quoteSelector) {
      return textQuoteToRange(anchor, quoteSelector);
    }
  },

  Indigo.annotations.markRange = function(range, tagName, callback) {
    var start, iterator, node,
        nodes = [],
        end = range.endContainer;

    function split(node, offset) {
      // TODO: will node always be a text node?
      if (offset !== 0 && offset !== node.length) {
        return node.splitText(offset);
      } else {
        return node;
      }
    }

    // split the start and end text nodes so that the offsets
    // fall on text node boundaries
    start = split(range.startContainer, range.startOffset);
    node = split(range.endContainer, range.endOffset);
    // returns the node AFTER the split (if it splits), but we want the one just before
    if (node !== end) end = node.previousSibling;

    // gather all the text nodes between start and end
    iterator = document.createNodeIterator(range.commonAncestorContainer, NodeFilter.SHOW_TEXT);
    domSeek(iterator, start);
    while (node = iterator.nextNode()) {
      nodes.push(node);
      if ((node.compareDocumentPosition(end) & node.DOCUMENT_POSITION_FOLLOWING) === 0) break;
    }

    // mark the gathered nodes
    nodes.forEach(function(node) {
      // TODO: data attributes, etc.
      var mark = document.createElement(tagName);
      node.parentElement.insertBefore(mark, node);
      mark.appendChild(node);
      if (callback) callback(mark);
    });
  };

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

          json.task.view_url =
            "/places/" +
            self.document.work.get('country') +
            (self.document.work.get('locality') ? ('-' + self.document.work.get('locality')) : '') +
            "/tasks/" +
            json.task.id;
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
   */
  Indigo.AnnotationThreadView = Backbone.View.extend({
    className: 'annotation-thread ig',
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

      // root annotation
      this.root = this.model.find(function(a) { return !a.get('in_reply_to'); });
      this.anchor = options.anchor || this.root.get('anchor').id;

      // views for each annotation
      this.annotationViews = this.model.map(function(note) {
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

      this.listenTo(this.model, 'destroy', this.annotationDeleted);
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
        this.$el.remove();
        this.trigger('closed', this);
      } else {
        this.display();
      }
    },

    display: function(forInput) {
      if (this.root.get('closed')) return;

      var node = document.getElementById(this.anchor);
      if (node) {
        node.appendChild(this.el);

        // the DOM elements get rudely removed from the view when the document
        // sheet is re-rendered, which seems to break event handlers, so
        // we have to re-bind them
        this.delegateEvents();
        this.annotationViews.forEach(function(v) { v.delegateEvents(); });

        if (forInput) {
          this.focus();
          this.$el
            .find('textarea')
            .first()
            .focus();
        }

        return true;
      } else {
        return false;
      }
    },

    focus: function() {
      this.$el.addClass('focused');
      this.$el.parent().addClass('annotation-focused');
    },

    scrollIntoView: function() {
      var container = this.$el.closest('.document-sheet-container')[0],
          top = this.el.getBoundingClientRect().top;

      if (container) {
        container.scrollBy({
          top: top - container.getBoundingClientRect().top - 50,
          behavior: 'smooth',
        });
      }
    },

    blurred: function(e) {
      if (!(this.el == e.target || jQuery.contains(this.el, e.target))) {
        this.blur();
      }
    },

    blur: function(e) {
      this.$el.removeClass('focused');
      this.$el.parent().removeClass('annotation-focused');
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

      reply = new Indigo.Annotation({
        text: text,
        in_reply_to: this.root.get('id'),
        anchor: this.root.get('anchor'),
      });
      this.document.annotations.add(reply);

      this.$el.find('.btn.post').prop('disabled', true);

      reply
        .save()
        .then(function() {
          view = new Indigo.AnnotationView({
            model: reply,
            template: self.annotationTemplate,
            document: self.document,
          });
          self.model.add(reply);
          self.annotationViews.push(view);

          view.$el.insertBefore(self.$el.find('.reply-container')[0]);

          self.$el.find('textarea').val('');
          self.$el.find('.btn.post').addClass('hidden');
        });
    },

    annotationDeleted: function(note) {
      if (this.root == note) {
        if (this.model.length > 0) {
          // delete everything else
          this.model.toArray().forEach(function(n) { n.destroy(); });
        }

        this.blur();
        this.remove();
        this.trigger('deleted', this);
      }
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
      var self = this;

      this.threadViews = [];
      this.prefocus = options.prefocus;
      this.annotatable = this.model.tradition().settings.annotatable;
      this.sheetContainer = this.el.querySelector('.document-sheet-container');
      this.$annotationNav = this.$el.find('.annotation-nav');

      this.$newButton = $("#new-annotation-floater");
      this.$el.on('mouseover', this.annotatable, _.bind(this.enterSection, this));

      this.model.annotations = this.annotations = new Indigo.AnnotationList([], {document: this.model});
      this.counts = new Backbone.Model({'threads': 0});
      this.listenTo(this.counts, 'change', this.renderCounts);
      this.visibleThreads = [];

      this.annotations.fetch().then(function() {
        // group by thread and transform into collections
        var threads = _.map(self.annotations.groupBy(function(a) {
          return a.get('in_reply_to') || a.get('id');
        }), function(notes) {
          var thread = new Backbone.Collection(notes, {comparator: 'created_at'});
          notes.forEach(function(n) { n.thread = thread; });
          return thread;
        });

        var template = self.annotationTemplate = Handlebars.compile($("#annotation-template").html());
        threads.forEach(_.bind(self.makeView, self));

        self.renderAnnotations();
      });
    },

    makeView: function(thread) {
      var view = new Indigo.AnnotationThreadView({
        model: thread,
        template: this.annotationTemplate,
        document: this.model
      });

      this.listenTo(view, 'deleted', this.threadDeleted);
      this.listenTo(view, 'closed', this.threadClosed);
      this.threadViews.push(view);

      return view;
    },

    threadDeleted: function(view) {
      this.threadViews = _.without(this.threadViews, view);
      this.visibleThreads = _.without(this.visibleThreads, view);
      this.counts.set('threads', this.counts.get('threads') - 1);
    },

    threadClosed: function(view) {
      this.visibleThreads = _.without(this.visibleThreads, view);
      this.counts.set('threads', this.counts.get('threads') - 1);
    },

    renderAnnotations: function() {
      // TODO: this gets called every time a new TOC entry is selected,
      // so it will always attempt to prefocus an annotation. It just so happens
      // that the click events prevent anything after the initial prefocus from
      // working. It's dirty, we should only prefocus on the first render.
      var prefocus = this.prefocus,
          visible = [];

      this.threadViews.forEach(function(v) {
        if (v.display()) visible.push(v);

        if (prefocus && (v.model.at(0).get('id') || "").toString() == prefocus) {
          v.focus();
          v.scrollIntoView();
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

    enterSection: function(e) {
      if (!Indigo.user.authenticated() ||
          !Indigo.user.hasPerm('indigo_api.add_annotation') ||
          e.enterAnnotationDone) return;

      var target = e.currentTarget,
          $target = $(target);

      if (!$target.is(this.annotatable)) return;

      if ($target.children(".annotation-thread").length === 0) {
        this.showAnnotationButton(target);
      } else {
        this.$newButton.hide();
      }

      e.enterAnnotationDone = true;
    },

    showAnnotationButton: _.debounce(function(target) {
      target.appendChild(this.$newButton[0]);
      this.$newButton.show();
    }, 100),

    // setup a new annotation thread
    newAnnotation: function(e) {
      var anchor = this.$newButton.closest(this.annotatable).attr('id'),
          root = new Indigo.Annotation({
            anchor: {
              id: anchor,
            },
          }),
          thread,
          view;

      this.threadViews.forEach(function(v) { v.blur(); });

      this.annotations.add(root);
      thread = new Backbone.Collection([root]);
      view = this.makeView(thread);

      this.$newButton.hide();
      view.display(true);

      this.visibleThreads.push(view);
      this.counts.set('threads', this.counts.get('threads') + 1);

      e.stopPropagation();
    },

    nextAnnotation: function(e) {
      e.preventDefault();
      e.stopPropagation();

      this.scrollSelected(true);
    },

    prevAnnotation: function(e) {
      e.preventDefault();
      e.stopPropagation();

      this.scrollSelected(false);
    },

    scrollSelected: function(toNext) {
      var threshold = this.sheetContainer.getBoundingClientRect().top + 50,
          candidates = [];

      // ensure none are selected
      this.visibleThreads.forEach(function(t) { t.blur(); });

      // candidates to be focused
      this.visibleThreads.forEach(function(thread) {
        var top = thread.el.getBoundingClientRect().top;

        if (toNext && top > threshold + 1 || !toNext && top < threshold - 1) {
          candidates.push({
            view: thread,
            offset: top - threshold,
          });
        }
      });
      candidates = _.sortBy(candidates, function(t) { return t.offset; });

      if (!toNext) candidates.reverse();

      if (candidates.length > 0) {
        candidates[0].view.focus();
        candidates[0].view.scrollIntoView();
      }
    },

    createRange: function() {
      return Indigo.rangeToTarget(document.getSelection().getRangeAt(0));
    },
  });
})(window);
