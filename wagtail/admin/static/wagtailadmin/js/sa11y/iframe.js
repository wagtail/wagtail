const interval = setInterval(() => {
    
    const doc = document.querySelector('.preview-panel__iframe'); 
    const content = doc.contentDocument;
    if(!content) return;

    const head = content.getElementsByTagName("head")[0];   
    const sa11yScript = document.createElement('script');
    sa11yScript.type = 'module';
    sa11yScript.innerHTML = `
        import { Sa11y, Lang } from "{% versioned_static './sa11y.esm.js' %}";
        import Sa11yLangEn from "{% versioned_static './lang/en.js' %}";

        // Optional: Custom checks
        import CustomChecks from "{% versioned_static './sa11y-custom-checks.esm.js' %}";

        // Set translations
        Lang.addI18n(Sa11yLangEn.strings);

        // Instantiate
        const sa11y = new Sa11y({
                customChecks: new CustomChecks, // Optional
                checkRoot: "body",
        });`

    head.appendChild(sa11yScript);

    clearInterval(interval);
}, 1000);


