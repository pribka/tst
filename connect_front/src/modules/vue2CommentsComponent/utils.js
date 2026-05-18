export const evt3rdArg = (() => {
    let result = false;
  
    try {
        const arg = Object.defineProperty({}, 'passive', {
            get() {
                result = { passive: true };
                return true;
            },
        });
  
        window.addEventListener('testpassive', arg, arg);
        window.remove('testpassive', arg, arg);
    } catch (e) { /* */ }
  
    return result;
})();