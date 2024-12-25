(function() {
    function updateCharCount(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        const label = document.querySelector('label[for="' + inputId + '"]');
        if (!label) return;

        function refreshLabel() {
            const length = input.value.length;
            const originalText = label.dataset.originalText || label.textContent;
            if (!label.dataset.originalText) {
                label.dataset.originalText = originalText;
            }
            label.textContent = `${label.dataset.originalText} (${length})`;
        }

        // Update on load
        refreshLabel();
        // Update as the user types
        input.addEventListener('input', refreshLabel);
    }

    // Call for both fields
    updateCharCount('id_seo_title');
    updateCharCount('id_search_description');
})();
