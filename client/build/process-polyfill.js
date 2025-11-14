// Early polyfill for environments where `process` is missing in browser
(function() {
  try {
    var w = typeof window !== 'undefined' ? window : undefined;
    if (!w) return;
    if (typeof w.process === 'undefined') {
      w.process = { env: {} };
    }
    // Expose global identifier `process`
    try { var process = w.process; } catch(e) {}
  } catch (e) {
    // swallow
  }
})();