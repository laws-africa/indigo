ace.define("ace/mode/indigo_highlight_rules", ["require", "exports", "module", "ace/lib/oop", "ace/mode/text_highlight_rules"], function(require, exports, module) {
"use strict";

var oop = require("../lib/oop");
var TextHighlightRules = require("./text_highlight_rules").TextHighlightRules;

var IndigoPLHighlightRules = function() {

    // regexp must not have capturing parentheses. Use (?:) instead.
    // regexps are ordered -> the first match is used
    this.$rules = {
        "start": [
            {
                // section and article
                token: ["constant.numeric", "entity.name.tag"],
                regex: /^((Art(\.|ykuł)|§)\s+[0-9][0-9a-z]*\.)/
            }, {
                token: "constant.language",
                regex: /^(body|preamble|preface)\s*$/,
                caseInsensitive: true,
            }, {
                // paragraph
                token: "constant.numeric",
                regex: /^[0-9][0-9a-z]*\./
            }, {
                // point and litera
                token: "constant.numeric",
                regex: /^[0-9a-z]*\)/
            }, {
                // indent (two different dash characters)
                token: "constant.numeric",
                regex: /^(–|-)\s+/
            }, {
                token: ["constant.language", "constant.numeric", "entity.name.tag"],
                regex: /^(dział|rozdział|oddział)(\s+[a-zA-Z0-9]+\s*)(-.*)?$/,
            }, {
                token: ["constant.language", "constant.numeric", "entity.name.tag"],
                regex: /^(schedule)(\s+[a-zA-Z0-9]*\s*)(-.*)?$/,
                caseInsensitive: true,
            }, {
                token: "constant.language",
                regex: /^schedule\s*$/,
                caseInsensitive: true,
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
                regex: /^{\|/,
                next: "table",
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
                regex: /^\|}/,
                next: "start"
            },
            {
                token: "constant.language.table",
                regex: /^!|(\|-?)/,
            }
        ]
    };
};

oop.inherits(IndigoPLHighlightRules, TextHighlightRules);

exports.IndigoPLHighlightRules = IndigoPLHighlightRules;
});

ace.define("ace/mode/indigo_pl", ["require", "exports", "module", "ace/lib/oop", "ace/mode/text", "ace/mode/indigo_highlight_rules"], function(require, exports, module) {
"use strict";

var oop = require("../lib/oop");
var TextMode = require("./text").Mode;
var IndigoPLHighlightRules = require("./indigo_highlight_rules").IndigoPLHighlightRules;

var Mode = function() {
    this.HighlightRules = IndigoPLHighlightRules;
};

oop.inherits(Mode, TextMode);

(function() {
    this.$id = "ace/mode/indigo_pl";
}).call(Mode.prototype);

exports.Mode = Mode;
});
