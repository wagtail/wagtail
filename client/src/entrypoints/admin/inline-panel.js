document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[id$='-FORMS']").forEach((panelElement) => {
        const formsetPrefix = panelElement.dataset.formsetPrefix;
        const emptyChildFormPrefix = panelElement.dataset.emptyChildFormPrefix;
        const canOrder = panelElement.dataset.canOrder === "true";
        const maxForms = parseInt(panelElement.dataset.maxForms, 10);

        new InlinePanel({
            formsetPrefix,
            emptyChildFormPrefix,
            canOrder,
            maxForms,
        });
    });
});
