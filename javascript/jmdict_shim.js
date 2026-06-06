// Loads the JMdict WASM binary for the active dictionary mode and exposes
// window.jmdictReady — a Promise that resolves with a Proxy object that
// supports jmdict[word] bracket access backed by the WASM lookup() function.
(function () {
    var pkg = new URL('../pkg/', document.currentScript.src).href;
    var mode = localStorage.getItem('dictionaryMode') === 'ultra' ? 'ultra' : 'full';
    var wasmJs = pkg + (mode === 'ultra' ? 'jmdict_ultra_wasm.js' : 'jmdict_full_wasm.js');
    var wasmGz = pkg + (mode === 'ultra' ? 'jmdict_ultra_wasm_bg.wasm.gz' : 'jmdict_full_wasm_bg.wasm.gz');

    var wasmResponse = fetch(wasmGz).then(function (r) {
        return new Response(
            r.body.pipeThrough(new DecompressionStream('gzip')),
            { headers: { 'Content-Type': 'application/wasm' } }
        );
    });

    window.jmdictReady = import(wasmJs).then(function (mod) {
        return mod.default({ module_or_path: wasmResponse }).then(function () {
            console.log('[timing] jmdict wasm ready: ' + performance.now().toFixed(0) + ' ms');
            return new Proxy({}, {
                get: function (_, word) {
                    if (typeof word !== 'string') return undefined;
                    var result = mod.lookup(word);
                    return result === null ? undefined : result;
                },
                has: function (_, word) {
                    return mod.lookup(word) !== null;
                }
            });
        });
    });
})();
