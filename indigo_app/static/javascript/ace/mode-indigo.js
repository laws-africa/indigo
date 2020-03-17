ace.define("ace/mode/indigo", ["require", "exports", "module", "ace/lib/oop", "ace/mode/text_highlight_rules"], function(require, exports, module) {
"use strict";

var oop = require("../lib/oop");
var TextHighlightRules = require("./text_highlight_rules").TextHighlightRules;

var IndigoHighlightRules = function() {

    // matching groups MUST cover the entire matched string.
    // regexps are ordered -> the first match is used
    this.$rules = {
        "start": [
            {
                token: ["constant.numeric", "entity.name.tag"],
                regex: /^(\s*[0-9][0-9a-z]*\.)(\s.*)?$/
            }, {
                token: "constant.language",
                regex: /^\s*(?:BODY|PREAMBLE|PREFACE)\s*$/,
            }, {
                token: ["constant.language", "entity.name.tag"],
                regex: /^(\s*LONGTITLE|CROSSHEADING)(\s+.+)$/,
            }, {
                token: "constant.numeric",
                regex: /^\s*\([0-9][0-9a-z]*\)/
            }, {
                token: "constant.numeric",
                regex: /^\s*\([a-z][0-9a-z]*\)/
            }, {
                token: ["constant.language", "constant.numeric", "entity.name.tag"],
                regex: /^(\s*(?:chapter|part|subpart))(\s+[a-zA-Z0-9]+\s*)(.*)?$/,
                caseInsensitive: true,
            }, {
                token: "constant.language",
                regex: /^SCHEDULE\s*$/,
            }, {
                token: ["constant.language", "entity.name.tag"],
                regex: /^(HEADING)(\s+.*)$/,
            }, {
                token: ["constant.language", "entity.name.tag"],
                regex: /^(SUBHEADING)(\s+.*)$/,
            }, {
                token: "comment.line.remark",
                regex: /\[\[/,
                next: "remark",
            }, {
                token: "markup.underline.link",
                regex: /\[[^\]]*\]\([^\)]*\)/,
            }, {
                token: "constant.other.image",
                regex: /!\[[^\]]*\]\([^\)]*\)/,
            }, {
                token: "constant.language.table",
                regex: /^\s*{\|/,
                next: "table",
            }, {
                token: "markup.bold",
                regex: /\*\*(.*?)\*\*/,
            }, {
                token: "markup.italic",
                regex: /\/\/(.*?)\/\//,
            }
        ],
        "remark": [
            // remarks can contain links
            {
                token: "markup.underline.link",
                regex: /\[[^\]]*\]\([^\)]*\)/,
            },
            {
                token: "comment.line.remark",
                regex: /]]/,
                next: "start",
            },
            {
                defaultToken: "comment.line.remark"
            }
        ],
        "table": [
            {
                token: "constant.language.table",
                regex: /^\s*\|}\s*$/,
                next: "start"
            },
            {
                token: "constant.language.table",
                regex: /^\s*!|(\|-?)/,
            }
        ]
    };
};

oop.inherits(IndigoHighlightRules, TextHighlightRules);

var TextMode = require("./text").Mode;
var Mode = function() {
    this.HighlightRules = IndigoHighlightRules;
};

oop.inherits(Mode, TextMode);

(function() {
    this.$id = "ace/mode/indigo";
}).call(Mode.prototype);

exports.Mode = Mode;
});
