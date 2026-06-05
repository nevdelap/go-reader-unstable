// Unicode ranges defining Japanese characters, shared between index.html and test.js.
// Browser: loaded via <script src="japanese-ranges.js">, exposes JAPANESE_RANGES as a global.
// Node.js: required by test.js via module.exports.

const JAPANESE_RANGES = [
  '\\u3000-\\u303F', // CJK symbols and punctuation (includes ideographic space)
  '\\u3040-\\u309F', // hiragana
  '\\u30A0-\\u30FF', // katakana
  '\\u4E00-\\u9FFF', // CJK unified ideographs (kanji)
  '\\u3400-\\u4DBF', // CJK extension A
  '\\uFF00-\\uFFEF', // fullwidth and halfwidth forms
  '\\n',             // newlines (preserve line breaks feature)
].join('');

if (typeof module !== 'undefined') module.exports = { JAPANESE_RANGES };
