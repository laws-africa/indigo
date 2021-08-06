export default function debounced(delay) {
    if (typeof window !== 'undefined') {
        let timer = null;
        return function (fn, ...args) {
            const context = this;
            if (timer) {
                window.clearTimeout(timer);
            }
            timer = window.setTimeout(() => {
                fn.apply(context, args);
            }, delay);
        };
    }
}
