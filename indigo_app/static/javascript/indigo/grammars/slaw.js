(function(exports) {
  "use strict";

  class SlawGrammarModel extends Indigo.grammars.GrammarModel {
    constructor (...args) {
      super(...args);
      this.language_id = 'slaw';
      this.language_def = {
        defaultToken: '',
        hier: /Part|Chapter|Subpart/,
        markers: /PREFACE|PREAMBLE|BODY/,
        headings: /LONGTITLE|CROSSHEADING|HEADING|SUBHEADING/,
        tokenizer: {
          root: [
            // grouping markers
            [/^@markers\s*$/, 'keyword.marker'],

            // single line headings
            [/^(\s*)(@headings)(\s.*)$/, ['white', 'keyword.heading', 'string']],

            // hierarchical
            // Part num - heading
            [/^(\s*)(@hier)(\s+.+)(-)(\s+.*$)/i, ['white', 'keyword.hier', 'constant.numeric', 'delimiter', 'string']],
            // Part num
            [/^(\s*)(@hier)(\s+.+$)/i, ['white', 'keyword.hier', 'constant.numeric']],

            // 2. Section heading
            [/^(\s*)([0-9][0-9a-z]*\.)(\s.*$)/, ['white', 'constant.numeric', 'string']],

            // (2) subsections
            // (a) list
            [/^(\s*)(\([0-9a-z]+\))/i, ['white', 'constant.numeric']],

            // attachments
            [/^\s*(SCHEDULE)\b/, 'keyword.schedule'],

            // inlines
            [/\*\*.*?\*\*/, 'inline.bold'],
            [/\/\/.*?\/\//, 'inline.italic'],

            [/[{}[\]()]/, '@brackets']
          ]
        }
      };
      this.theme_id = 'slaw';
      this.theme_def = {
        base: 'vs',
        inherit: true,
        rules: [
          {token: 'string', foreground: '008000'},
          {token: 'constant.numeric', foreground: '0000FF'},
          {token: 'inline.bold', fontStyle: 'bold'},
          {token: 'inline.italic', fontStyle: 'italic'},
          {token: 'inline.ref', fontStyle: 'underline', foreground: 'ffa500'},
          {token: 'inline.underline', fontStyle: 'text-decoration: underline'}
        ]
      };

      this.image_re = /!\[([^\]]*)]\(([^)]*)\)/g;
    }

    installActions (editor) {
      editor.addAction({
        id: 'format.bold',
        label: 'Format Bold',
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_B],
        run: function(editor) {
          Indigo.monaco.wrapSelection(editor, 'format.bold', '**', '**');
          editor.pushUndoStop();
        }
      });

      editor.addAction({
        id: 'format.italics',
        label: 'Format Italics',
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_I],
        run: function(editor) {
          Indigo.monaco.wrapSelection(editor, 'format.italics', '//', '//');
          editor.pushUndoStop();
        }
      });

      editor.addAction({
        id: 'format.remark',
        label: 'Format Remark',
        run: function(editor) {
          Indigo.monaco.wrapSelection(editor, 'format.remark', '[[', ']]');
          editor.pushUndoStop();
        }
      });

      editor.addAction({
        id: 'insert.schedule',
        label: 'Insert Schedule',
        run: function(editor) {
          const sel = editor.getSelection();
          const cursor = sel.setEndPosition(sel.startLineNumber + 1, 12 + 24)
            .setStartPosition(sel.startLineNumber + 1, 12);

          editor.executeEdits(this.language_id, [{
            identifier: 'insert.schedule',
            range: sel,
            text: '\nSCHEDULE - <optional schedule name>\n<optional schedule title>\n\n',
          }], [cursor]);
          editor.pushUndoStop();
        }
      });

      editor.addAction({
        id: 'insert.table',
        label: 'Insert Table',
        run: function (editor) {
          let table;
          const sel = editor.getSelection();

          if (sel.isEmpty()) {
            table = ["", "{|", "|-", "! heading 1", "! heading 2", "|-", "| cell 1", "| cell 2", "|-", "| cell 3", "| cell 4", "|-", "|}", ""].join("\n");
          } else {
            var lines = editor.getModel().getValueInRange(sel).split("\n");
            table = "\n{|\n|-\n";
            lines.forEach(function(line) {
              // ignore empty lines
              if (line.trim() !== "") {
                table = table + "| " + line + "\n|-\n";
              }
            });
            table = table + "|}\n";
          }

          const cursor = sel.setEndPosition(sel.startLineNumber + 3, 3)
            .setStartPosition(sel.startLineNumber + 3, 3);

          editor.executeEdits(this.language_id, [{
            identifier: 'insert.table',
            range: sel,
            text: table,
          }], [cursor]);
          editor.pushUndoStop();
        }
      });
    }

    /**
     * Markup a textual remark
     */
    markupRemark (text) {
      return `[[${text}]]`;
    }

    /**
     * Markup a link (ref)
     */
    markupRef (title, href) {
      return `[${title}](${href})`;
    }

    markupImage (title, src) {
      return `![${title}](${src})`;
    }

    /**
     * Get the image filename at the cursor, if any.
     */
    getImageAtCursor (editor) {
      const match = super.getImageAtCursor(editor);
      if (match) {
        match.title = match.match[1];
        match.src = match.match[2];
      }
      return match;
    }
  }

  exports.Indigo.grammars.registry.slaw = SlawGrammarModel;
})(window);
