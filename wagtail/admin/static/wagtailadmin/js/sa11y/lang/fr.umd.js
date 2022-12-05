(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
  typeof define === 'function' && define.amd ? define(factory) :
  (global = typeof globalThis !== 'undefined' ? globalThis : global || self, global.Sa11yLangFr = factory());
})(this, (function () { 'use strict';

  var fr = {
    // French
    strings: {
      LANG_CODE: 'fr',
      MAIN_TOGGLE_LABEL: 'Vérifier l’accessibilité',
      CONTAINER_LABEL: 'Vérificateur d’accessibilité',
      ERROR: 'Erreur',
      ERRORS: 'Erreurs',
      WARNING: 'Avertissement',
      WARNINGS: 'Avertissements',
      GOOD: 'Correct',
      ON: 'Allumer',
      OFF: 'Éteindre',
      ALERT_TEXT: 'Alerte',
      ALERT_CLOSE: 'Fermer',
      SHOW_OUTLINE: 'Schéma',
      HIDE_OUTLINE: 'Schéma',
      SHOW_SETTINGS: 'Paramètres',
      HIDE_SETTINGS: 'Paramètres',
      PAGE_OUTLINE: 'Page du schéma',
      SETTINGS: 'Paramètres',
      CONTRAST: 'Contraste',
      FORM_LABELS: 'Étiquettes de formulaires',
      LINKS_ADVANCED: 'Liens (avancés)',
      DARK_MODE: 'Mode sombre',
      SHORTCUT_SCREEN_READER: 'Passer à l’édition. Raccourci clavier: Alt et point',
      SHORTCUT_TOOLTIP: 'Passer à l’édition',
      NEW_TAB: 'Ouvrir dans un nouvel onglet',
      PANEL_HEADING: 'Vérification d’accessibilité',
      PANEL_STATUS_NONE: 'Aucune erreur trouvée.',
      PANEL_ICON_WARNINGS: 'avertissement(s) trouvé(s).',
      PANEL_ICON_TOTAL: 'problème(s) trouvé(s) au total.',
      NOT_VISIBLE_ALERT: 'L’élément que vous tentez de consulter n’est pas visible; il peut être masqué, à l’intérieur de l’accordéon ou dans le volet de l’onglet. Voir l’aperçu:',
      ERROR_MISSING_ROOT_TARGET: 'L\'accessibilité de la page entière a été vérifiée, car la zone cible <code><code>%(root)</code> n\'existe pas.',
      HEADING_NOT_VISIBLE_ALERT: 'L\'en-tête n\'est pas visible ; il peut être caché ou à l\'intérieur d\'un accordéon ou d\'un composant d\'onglet.',

      // Alternative text module stop words
      SUSPICIOUS_ALT_STOPWORDS: ['image', 'illustration', 'photo', 'photographie'],
      PLACEHOLDER_ALT_STOPWORDS: ['alt', 'image', 'photographie', 'décorative', 'photographie', 'support d’affichage', 'support d’affichage d’image', 'séparateur', '.'],
      PARTIAL_ALT_STOPWORDS: [
        'clic',
        'cliquer ici',
        'cliquer pour plus de détails',
        'cliquer ici pour plus d’informations',
        'cliquer ici pour plus d’informations.',
        'cocher',
        'télécharger',
        'télécharger ici',
        'télécharger ici.',
        'pour en savoir',
        'pour en savoir d’avantage',
        'pour en savoir d’avantage.',
        'pour en savoir d’avantage >',
        'formulaire',
        'ici',
        'ici.',
        'info',
        'information',
        'lien',
        'en apprendre',
        'en apprendre davantage',
        'en apprendre davantage.',
        'en apprendre davantage >',
        'davantage',
        'plus',
        'plus >',
        'page',
        'papier',
        'en savoir plus',
        'en savoir plus >',
        'lire',
        'lisez ceci',
        'ceci',
        'cette page',
        'cette page.',
        'ce site web',
        'ce site web.',
        'consulter',
        'consulter notre',
        'site web',
        '.',
      ],
      WARNING_ALT_STOPWORDS: ['< ', ' >', 'cliquer ici'],
      NEW_WINDOW_PHRASES: ['externe', 'nouvel onglet', 'nouvelle fenêtre', 'fenêtre pop-up', 'pop-up'],

      // Only some items in list would need to be translated.
      FILE_TYPE_PHRASES: ['document', 'feuille de calcul', 'feuille de travail', 'installation', 'vidéo', 'pdf', 'doc', 'docx', 'word', 'mp3', 'ppt', 'texte', 'pptx', 'PowerPoint', 'txt', 'exe', 'dmg', 'rtf', 'Windows OS', 'Mac OS', 'csv', 'xls', 'xlsx', 'mp4', 'mov', 'avi', 'zip'],

      // Readability
      LANG_READABILITY: 'Lisibilité',
      LANG_AVG_SENTENCE: 'Nombre de mots moyens par phrase:',
      LANG_COMPLEX_WORDS: 'Mots complexes:',
      LANG_TOTAL_WORDS: 'Mots:',
      LANG_VERY_DIFFICULT: 'Très difficile',
      LANG_DIFFICULT: 'Difficile',
      LANG_FAIRLY_DIFFICULT: 'Assez difficile',
      LANG_GOOD: 'Correct',
      READABILITY_NO_P_OR_LI_MESSAGE: 'Incapable de calculer le taux de lisibilité. Aucun paragraphe <code>&lt;p&gt;</code> ou liste de contenu <code>&lt;li&gt;</code> trouvé.',
      READABILITY_NOT_ENOUGH_CONTENT_MESSAGE: 'Pas suffisamment de contenu pour calculer le taux de lisibilité.',

      // Headings
      HEADING_NON_CONSECUTIVE_LEVEL: 'Utilisation d’un niveau d’en-tête non consécutif. Les en-têtes ne doivent jamais sauter de niveaux ou aller de <strong>L’en-tête %(prevLevel)</strong> à <strong {r}>L’en-tête %(level)</strong>.',
      HEADING_EMPTY: 'En-tête vide trouvé! Pour résoudre, supprimer cette ligne ou changer le format de <strong {r}>L’en-tête %(level)</strong> à <strong>Normal</strong> ou <strong>Paragraphe</strong>.',
      HEADING_LONG: 'L’en-tête est long! Les en-têtes doivent être utilisées pour organiser le contenu et acheminer la structure. Ils doivent être brefs, informatifs et uniques. Les en-têtes doi-vent être inférieures à 160 caractères (pas plus d’une phrase).<hr>Nombre de caractère(s): <strong {r}>%(headingLength)</strong>',
      HEADING_FIRST: 'Le premier en-tête sur la page doit être habituellement En-tête 1 ou En-tête 2. L’en-tête 1 doit débuter dans la section principale du contenu,  car il s\'agit de l’en-tête prin-cipal qui décrit l\'objectif général de la page. En savoir plus sur <a href="https://www.w3.org/WAI/tutorials/page-structure/headings/">La Structure Des En-têtes.</a>',
      HEADING_MISSING_ONE: 'En-tête 1 manquant. L’en-tête 1 doit débuter dans la zone principale de contenu, il est l’en-tête principal qui décrit l’objectif global de la page. En savoir plus sur <a href="https://www.w3.org/WAI/tutorials/page-structure/headings/">La Structure Des En-têtes. </a>',
      HEADING_EMPTY_WITH_IMAGE: 'L’en-tête ne contient pas de texte, mais seulement une image. Si ce n’est pas un en-tête, veuillez changer son format pour <strong {r}>L’en-tête %(level)</strong> à <strong>Normal</strong> ou <strong>Paragraphe</strong>. Sinon, veuillez ajouter du texte de remplacement à l’image si elle n’est pas décorative.',
      PANEL_HEADING_MISSING_ONE: 'En-tête 1 manquant!',

      // Links
      LINK_EMPTY: 'Retirer les liens vides sans texte.',
      LINK_EMPTY_LINK_NO_LABEL: 'Le lien ne comporte pas de texte perceptible par les lecteurs d\'écran ou autres techno-logies d\'assistance. À corriger: <ul><li>Ajoutez un texte bref qui décrit où le lien vous mène.</li><li>S’il s’agit d’un <a href="https://a11y-101.com/development/icons-and-links/">lien d’icône SVG (vectoriel), </a> il manque alors une description.</li><li>Si ce lien est une erreur due à un bogue de copier/coller, tentez de supprimer.</li></ul>',
      LINK_LABEL: '<strong>Lien de l’étiquette:</strong> %(linkText)',
      LINK_STOPWORD: 'Le texte du lien peut ne pas être suffisamment descriptif hors du contexte: <strong {r}>%(error)</strong><hr><strong>Conseil!</strong> Le texte du lien doit toujours être précis, unique et significatif. Évitez les mots courants comme &quot;cliquez ici&quot; ou &quot;en savoir plus&quot;.',
      LINK_BEST_PRACTICES: 'Remplacer le lien du texte: <strong {r}>%(error)</strong><hr><ul><li>&quot;Cliquer ici&quot; fait référence au mouvement de la souris, alors que de nombreuses personnes n\'utilisent pas de souris ou consultent peut-être ce site web sur un appareil mobile. Envisagez d\'utiliser un verbe différent qui se rapporte à la tâche.</li><li>Éviter l’utilisation de symbole HTML comme appel à l’action à moins qu\'ils ne soient cachés aux technologies d\'assistance.</li></ul>',
      LINK_URL: 'Des adresses URLs plus longues et moins compréhensibles utilisé en tant que lien de texte peuvent être difficiles à écouter avec une technologie d’assistance. Dans la plu-part des cas, il est recommandé d’utiliser du texte lisible plutôt qu’une adresse URL. Les adresses URL courtes (tels que les pages d’accueil de site web) sont correctes.<hr><strong>Conseil!</strong> Un lien de texte doit toujours être précis, unique et significatif pour qu\'il puisse être compris hors contexte.',

      // Links advanced
      NEW_TAB_WARNING: 'Le lien s’ouvre dans une nouvelle fenêtre ou un nouvel onglet sans avertissement.  Ce-la peut spécialement désorienter les gens qui ont une difficulté à percevoir le contenu visuel. Deuxièmement, ce n’est pas recommandé de contrôler l\'expérience d\'une per-sonne ou de prendre des décisions à sa place. Indiquer que le lient s’ouvrira dans une nouvelle fenêtre à l’intérieur du texte du lien.<hr><strong>Conseil!</strong> Apprenez les meilleures pratiques: <a href="https://www.nngroup.com/articles/new-browser-windows-and-tabs/">l’ouverture de lien dans les nouvelles fenêtres ou onglets des navigateurs.</a>',
      FILE_TYPE_WARNING: 'Le lien dirige vers un PDF ou un fichier téléchargeable (exemple: MP3, Zip, Word Doc) sans avertissements. Indiquer le type de fichier dans le lien du texte. S’il s’agit d’un fi-chier volumineux, envisagez d’inclure la taille du ficher.<hr><strong>Exemple:</strong> Rapport de synthèse (PDF, 3MB)',
      LINK_IDENTICAL_NAME: 'Le texte du lien est identique à  un autre, bien qu’il pointe vers une page différente. Des liens qui contiennent le même texte peuvent porter à confusion pour les gens qui utilisent des lecteurs d’écran.<hr>Ajoutez davantage de description au lien suivant pour le différencier de l’autre: <strong {r}>%(linkText)</strong>',

      // Images
      MISSING_ALT_LINK_BUT_HAS_TEXT_MESSAGE: 'L’image est utilisé en tant que lien avec un texte autour, alors que l’attribut de rem-placement doit être signalé comme décoratif ou nul.',
      MISSING_ALT_LINK_MESSAGE: 'L’image est utilisée en tant que lien mais manque de texte de remplacement! Veuillez vous assurer que le texte de remplacement décrit où le lien vous mène.',
      MISSING_ALT_MESSAGE: 'Texte de remplacement manquant! Si l’image transmet un message, une émotion ou des informations importantes - assurez-vous d’ajouter une description de l’image.',
      LINK_IMAGE_BAD_ALT_MESSAGE: 'L’extension du fichier trouvé à l’intérieur du texte de remplacement. Assurez-vous que le texte de remplacement décrit la destination du lien pas une description complète de l’image. Retirer: <strong {r}>%(error)</strong>.<hr><strong>Texte de remplacement: </strong> %(altText)',
      LINK_IMAGE_PLACEHOLDER_ALT_MESSAGE: 'Texte de remplacement non-descriptif ou séparateur trouvé dans une image. Assurez-vous que le texte de remplacement décrit la destination du lien, pas une description compète de l’image. Remplacer le texte de remplacement suivant: <strong {r}>%(altText)</strong>',
      LINK_IMAGE_SUS_ALT_MESSAGE: 'La technologie d’assistance indiquer déjà que c’est une image, donc &quot;<strong {r}>%(error)</strong>&quot; pourrait être redondant. Assurez-vous que le texte de remplacement décrit la destination du lien, pas la des-cription complète de l’image.<hr><strong>Texte de remplacement:</strong> %(altText)',
      LINK_ALT_HAS_BAD_WORD_MESSAGE: 'L’extension du fichier trouvé à l’intérieur du texte de remplacement. Si l’image trans-met un message, une émotion ou une information importante - assurez-vous d’ajouter une description de l’image. Retirer: <strong {r}>%(error)</strong>.<hr><strong>Texte de remplacement:</strong> %(altText)',
      ALT_PLACEHOLDER_MESSAGE: 'Texte de remplacement non-descriptif ou séparateur trouvé dans une image. Modifier le texte de remplacement suivant pour le rendre plus significatif: <strong {r}>%(altText)</strong>',
      ALT_HAS_SUS_WORD: 'Les technologies d’assistances indiquent déjà qu’il s’agit d’une image, donc &quot;<strong {r}>%(error)</strong>&quot; peut être redondant.<hr><strong>Texte de remplacement:</strong> %(altText)',
      LINK_IMAGE_ARIA_HIDDEN: 'Le lien autour de l’image a <code>aria-hidden=&quot;true&quot;</code> mais est toujours accessible au clavier. Si vous tentez de masquer un lien redondant ou dupliqué, ajouter <code>tabindex=&quot;-1&quot;</code> aussi.',
      LINK_IMAGE_NO_ALT_TEXT: 'L’image dans le lien est marquée comme décorative et il n’y a pas de lien de texte. Veuillez ajouter du texte de remplacement à l’image qui décrit la destination du lien.',
      LINK_IMAGE_HAS_TEXT: 'L’image est marqué comme étant décorative, bien que le lien utilise le texte autour en tant que description.',
      LINK_IMAGE_LONG_ALT: 'La description du texte de remplacement sur l’image lié est <strong>trop longue</strong>. Le texte de remplacement sur l’image liée devrait décrire où le lien vous mène, pas une description complète de l’image. <strong>Utilisez le titre de l’image en tant que lien du texte de remplacement.</strong><hr><strong>Texte de remplacement: (<span {r}>%(altLength)</span> caractères):</strong> %(altText)',
      LINK_IMAGE_ALT_WARNING: 'Le lien de l’image contient du texte de remplacement, mais assurez-vous que le texte de remplacement décrit la page de destination. <strong>Utilisez le titre de la page liée en tant que texte de remplacement.</strong> Est-ce que le texte de remplacement décrit où le lien vous mène?<hr><strong>Texte de remplacement:</strong> %(altText)',
      LINK_IMAGE_ALT_AND_TEXT_WARNING: 'Le lien de l’image contient <strong>du texte de remplacement et du texte à l’entour.</strong> Si cette image est décorative et est utilisé en tant que lien qui mène à une autre page, envisagez marquer l’image en tant que décorative, ou nulle - les liens texte autour de-vraient suffire.<hr><strong>Texte de remplacement:</strong> %(altText)',
      IMAGE_FIGURE_DECORATIVE: 'L’image est perçue de manière décorative <strong>décorative</strong> et sera ignorée par la technologie d’assistance. <hr>Bien qu’une <strong>légende</strong> est fournie, l’image devrait aussi avoir du texte de remplacement dans la plupart des cas.<ul><li>Le texte de remplacement devrait fournir une description précise de l’image.</li><li>La légende devrait fournir habituellement le contexte lié à l’image derrière le contenu environnant ou prêter attention à un élément d’information.</li></ul>En savoir plus: <a href="https://thoughtbot.com/blog/alt-vs-figcaption#the-figcaption-element">alt versus figcaption (légende de la figure). </a>',
      IMAGE_FIGURE_DUPLICATE_ALT: 'Ne pas utiliser le même mot pour la légende et le texte de remplacement. Les lecteurs d’écrans vont annoncer l’information en double.<ul><li>Le texte de remplacement devrait fournir une description précise de l’image.</li><li>La légende devrait fournir habituellement le contexte lié à l’image derrière le contenu environnant ou prêter attention à un élément d’information.</li></ul>En savoir plus: <a href="https://thoughtbot.com/blog/alt-vs-figcaption#the-figcaption-element">alt versus figcaption (légende de la figure).</a><hr><strong>Texte de remplacement:</strong> %(altText)',
      IMAGE_DECORATIVE: 'L’image est perçue de manière <strong>décorative</strong> et sera ignorée par la technologie d’assistance. Si l’image transmet un message, une émotion ou une information importante -  assurez-vous d’ajouter le texte de rempla-cement.',
      IMAGE_ALT_TOO_LONG: 'La description du texte de remplacement est <strong>trop longue</strong>. Le texte de remplacement doit être précis, mais significatif tout comme un <em>gazouillis (micromessage) </em> (environ 100 caractères). S’il s’agit d’une image complexe ou d’une illustration, ajoutez une longue description de l’image dans le texte ci-dessous ou dans la composante accordéon.<hr><strong>Texte de remplacement (<span {r}>%(altLength)</span> caractères):</strong> %(altText)',
      IMAGE_PASS: '<strong>Texte de remplacement:</strong> %(altText)',

      // Labels
      LABELS_MISSING_IMAGE_INPUT_MESSAGE: 'Le bouton de l’image manque un texte de remplacement. Veuillez ajouter un texte de remplacement pour fournir un nom accessible. Par exemple: <em>Rechercher</em> ou <em>Soumettre</em>.',
      LABELS_INPUT_RESET_MESSAGE: 'Le bouton réinitialiser <strong>ne devrait pas</strong> être utiliser sauf en cas de besoin spécifique, car il est facile de l’activer par erreur.<hr><strong>Conseil!</strong> En savoir plus sur <a href="https://www.nngroup.com/articles/reset-and-cancel-buttons/">les problèmes liés aux boutons Réinitialiser et Annuler.</a>',
      LABELS_ARIA_LABEL_INPUT_MESSAGE: 'L’entrée a un nom accessible, assurez-vouer qu’il y a aussi une étiquette visible.<hr>Le nom accessible pour cette entrée est: <strong>%(ariaLabel)</strong>',
      LABELS_NO_FOR_ATTRIBUTE_MESSAGE: 'Il n’y a pas d’étiquette associée à cette entrée. Ajouter en un <code>pour</code> l’attribut de l’étiquette qui correspond <code>id</code> à l’id(identifiant) de cette entrée.<hr>L’ID (L’identifiant) de cette entrée est: <code>id=&#34;%(id)&#34;</code>',
      LABELS_MISSING_LABEL_MESSAGE: 'Il n’y a pas d’étiquette associée à cette entrée. Veuillez ajouter un <code>id</code> id (identifiant) à cette entrée et ajouter un <code>for</code> attribut correspondant à l’étiquette.',

      // Embedded content
      EMBED_VIDEO: 'Assurez-vous <strong>que les vidéos ont des sous-titres codés.</strong> Fournir les sous-titres pour tout type de contenu audio ou vidéo est une exigence obli-gatoire de Niveau A. Les sous-titres aident les gens qui sont malentendants.',
      EMBED_AUDIO: 'Assurez-vous de fournir <strong>une transcription pour tous les balados.</strong> Fournir les transcriptions pour tout type de contenu audio est une exigence obligatoire de Niveau A. Les transcriptions aident les gens qui sont malentendant, mais peuvent profiter à tout le monde. Positionnez la transcription sous ou à l’intérieur du panneau accordéon.',
      EMBED_DATA_VIZ: 'Les gadgets logiciels de visualisation de données comme ceci sont souvent problématiques pour les gens qui utilisent un clavier ou un lecteur d’écran lors de la navigation et peuvent présenter d’importante difficultés pour les gens qui ont une malvoyance ou du daltonisme. Il est recommandé de fournir la même information de remplacement (texte ou tableau) dans le format ci-dessous du gadget logiciel.<hr>En savoir plus sur <a href="https://www.w3.org/WAI/tutorials/images/complex/">les images complexes.</a>',
      EMBED_MISSING_TITLE: 'Le contenu intégré requiert un nom accessible qui décrit le contenu. Veuillez fournir un titre (<code>title</code>) unique ou <code>aria-label</code> un attribut à l’élément <code>iframe</code>. En savoir plus sur les <a href="https://developer.mozilla.org/fr/docs/Web/HTML/Element/iframe#une_iframe_simple">iFrames.</a>',
      EMBED_GENERAL_WARNING: 'Impossible de vérifier le contenu intégré. Assurez-vous que les images ont du texte de remplacement, les vidéos ont des sous-titres, le texte est suffisamment contrasté et que les éléments interactifs sont  <a href="https://webaim.org/techniques/keyboard/">accessible par le clavier. </a>',

      // Quality assurance
      QA_BAD_LINK: 'Lien incorrect trouvé. Le lien semble diriger vers un environnement de développement. Assurez vous que le lien ne contient pas <em>dev</em> ou <em>wp-admin</em> dans l’adresse URL.<hr>Le lien dirige vers:<br><strong {r}>%(el)</strong>',
      QA_BAD_ITALICS: 'Les balises Gras et Italique ont une signification sémantique et <strong>ne devraient pas</strong> être utiliser pour surligner des paragraphes en entier. Les textes en Gras doivent être utilisés pour mettre <strong>l’emphase</strong> sur un mot ou une phrase. Les textes en Italiques doivent être utilisés pour surligneur les noms propres (ex. livres et titre d’articles), les mots étrangers et les citations.  Les citations longues doivent être formatées comme une citation en bloc.',
      QA_PDF: 'Les PDFSs sont considérés comme contenu web et doivent être accessible comme tel. Les PDFs contiennent souvent des erreurs pour les gens qui utilisent les lecteurs d’écrans (balises structurelles manquante ou des champs de formulaire manquants) et les gens qui ont une malvoyance (le texte ne resurgit pas lorsqu’il est agrandi).<ul><li>S’il s’agit d’un formulaire, utilisez un formulaire HTML comme alternative.</li><li>S’il s’agit d’un document, convertissez-le en page web.</li></ul>Sinon, veuillez vérifier  <strong {r}>%(pdfCount)</strong> <a href="https://www.adobe.com/accessibility/products/acrobat/using-acrobat-pro-accessibility-checker.html">PDF pour assurer l’accessibilité dans Acrobat DC.</a>',
      QA_PAGE_LANGUAGE: 'La langue de la page n’est pas indiquée!  Veuillez <a href="https://www.w3.org/International/questions/qa-html-language-declarations.fr">indiquer la langue sur la balise HTML.</a>',
      QA_PAGE_TITLE: 'Titre de la page manquant ! Veuillez fournir un <a href="https://developer.mozilla.org/fr/docs/Web/HTML/Element/title">titre de page.</a>',
      QA_BLOCKQUOTE_MESSAGE: 'Est-ce un en-tête?  <strong {r}>%(bqHeadingText)</strong><hr>Les citations en bloc doivent être utilisées pour les citations uniquement. S’il s’agit d’un en-tête, changez cette citation en bloc pour un en-tête sémantique (ex. En-tête 2 ou En-tête 3).',
      QA_FAKE_HEADING: 'Est-ce un en-tête? <strong {r}>%(boldtext)</strong><hr>Une ligne de texte Gras peut ressembler à un en-tête, mais pour une personne utili-sant un lecteur d’écran, il est impossible de déterminer ce qui est important ou com-ment accéder au contenu. Le texte en Gras ne devrait jamais remplacer un en-tête sémantique (En-tête 2 à En-tête 6).',
      QA_SHOULD_BE_LIST: 'Voulez-vous créer une liste? Une liste d’élément possible est trouvée: <strong {r}>%(firstPrefix)</strong><hr>Assurez-vous de créer une liste en suivant le formatage de bouton, de puces ou de nombre. Lors d’une liste  relative, la technologie d’assistance est en mesure de transmettre l’information telle que le nombre total d’élément et la position relative de chaque élément sur la site. En savoir plus sur les <a href="https://www.w3.org/WAI/tutorials/page-structure/content/#lists">listes relatives. </a>',
      QA_UPPERCASE_WARNING: 'Majuscules trouvées. Certains lecteur d’écran pourraient interpréter les textes majus-cules en tant qu’acronyme et pourraient être tentés de les lire individuellement. De plus, certaines personnes trouvent les majuscules difficiles à lire et peuvent donner l’impression de CRIER.',
      QA_DUPLICATE_ID: 'ID (Identifiant) dupliqué trouvé. Les erreurs d’ID (d’identifiants) dupliqués sont re-connues pour causer des problèmes au niveau de la technologie d’assistance lors-qu’ils tentent d’interagir avec le contenu.<hr>Veuillez retirer ou modifier l’ID (l’identifiant) suivant: <strong {r}>%(id)</strong>',
      QA_TEXT_UNDERLINE_WARNING: 'Le texte soulignés peuvent être confondus avec les liens. Envisagez d’utiliser un style différent comme &lt;strong&gt;<strong>forte importance</strong>&lt;/strong&gt; ou &lt;em&gt;<em>l’emphase.</em>&lt;/em&gt;.',
      QA_SUBSCRIPT_WARNING: 'Les options de mise en forme en indice et en exposant ne doivent être utilisées que pour modifier la position du texte afin de se conformer aux conventions ou normes typographiques. Il ne doit <strong>pas</strong> être utilisé uniquement à des fins de présentation ou d’apparence. La mise en forme de phrases entières pose des problèmes de lisibilité. Les cas d’utilisation appropriés incluent l’affichage d’exposants, de nombres ordinaux tels que 4<sup>th</sup> au lieu de quatrième et de formules chimiques (H<sub>2</sub>O).',

      // Tables
      TABLES_MISSING_HEADINGS: 'En-têtes de tableau manquants! Les tableaux accessibles doivent contenir le balisage HTML pour indiquer la cellule de l’en-tête et la cellule des donnés qui déterminent leur relation. Cette information fournit le contexte aux gens qui utilisent la technolo-gie d’assistance. Les tableaux doivent être utilisés pour les données relatives uni-quement.<hr>En savoir plus sur les <a href="https://www.w3.org/WAI/tutorials/tables/">tableaux accessibles.</a>',
      TABLES_SEMANTIC_HEADING: 'Les en-têtes sémantiques tels que En-tête 2 ou En-tête 3 doivent être utilisées uni-quement pour les sections de contenu; non pas pour les tableaux HTML. Indiquez les en-têtes de tableau en utilisant plutôt l’élément <code>&lt;th&gt;</code>.<hr>En savoir plus sur les <a href="https://www.w3.org/WAI/tutorials/tables/">tableaux accessibles.</a>',
      TABLES_EMPTY_HEADING: 'En-tête de tableau vide trouvé! Les en-têtes de tableau ne devraient jamais être vides. Il est important de déterminer les rangées et/ou colonnes des en-têtes pour détermi-ner leur relation. Cette information fournit le contexte aux gens qui utilisent la tech-nologie d’assistance. Veuillez garder à l’esprit que les tableaux devraient être utilisés pour les données relatives uniquement.<hr>En savoir plus sur les <a href="https://www.w3.org/WAI/tutorials/tables/">tableaux accessibles.</a>',

      // Contrast
      CONTRAST_ERROR: 'Ce texte n’est pas suffisamment contrasté avec l’arrière-plan. Le ratio du contraste devrait être au moins de 4.5:1 pour le texte normal et 3:1 pour les textes plus grands.<hr>Le ratio du contraste est de <strong {r}>%(cratio)</strong> pour le texte suivant: <strong {r}>%(nodetext)</strong>',
      CONTRAST_WARNING: 'Le contraste de ce texte est inconnu et doit être manuellement révisé. Assurez-vous que le texte et l’arrière-plan représentent des couleurs contrastantes. Le ratio du con-traste devrait être au moins de 4.5:1 pour les textes normaux et 3:1 pour les textes plus grands.<hr><strong>Veuillez réviser:</strong> %(nodetext)',
      CONTRAST_INPUT_ERROR: 'Le texte à l’intérieur de cette entrée n’est pas suffisamment contrasté avec l’arrière-plan. Le ratio du contraste devraient être au moins de 4.5:1 pour le texte normal et 3:1 pour les textes plus grands.<hr>Ratio du contraste: <strong {r}>%(cratio)</strong>',
    },
  };

  return fr;

}));
