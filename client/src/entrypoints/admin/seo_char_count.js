(function () {
    function updateCharCount(inputId) {
        const input = document.getElementById(inputId);
        if (!input) {
            return;
        }

        const label = document.querySelector('label[for="' + inputId + '"]');
        if (!label) {
            return;
        }

        const originalText = label.textContent.trim();
        if (!originalText) {
            return;
        }

        const span = document.createElement('span');
        span.setAttribute('aria-live', 'polite');
        label.appendChild(span);

        function refreshLabel() {
            span.textContent = ` (${input.value.length})`;
        }

        refreshLabel();
        input.addEventListener('input', refreshLabel);
    }

    updateCharCount('id_seo_title');
    updateCharCount('id_search_description');
})();

