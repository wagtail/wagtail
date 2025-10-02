==============================
UI Naming Guidelines
==============================

This page sets out how to name UI elements in Wagtail’s admin.  
It focuses on **icon-only buttons and controls**, which often cause problems for screen reader and speech-recognition users.

The goal is simple:  
*Make every control understandable, consistent, and translatable.*

Why this matters
----------------
- Without good names, people using assistive tech can’t tell what a button does.
- Developers often invent labels on the spot, so the same icon gets different names in different places.
- Translation is harder if strings aren’t consistent.
- Clear names also make the UI easier for everyone.

General rules
-------------
- **Name by what the control does, not by what the icon looks like.**  
  - bad: “hamburger” → good: “Open main menu”  
  - bad: “magnifying glass” → good: “Search”

- **Keep it short and action-oriented.**  
  Use verbs: Open, Close, Search, Expand, Collapse, Edit, Delete.

- **Avoid Wagtail-internal jargon.**  
  - bad: “trigger snippet chooser” → good: “Choose snippet”

- **Every icon-only control needs:**  
  - an accessible label (`aria-label` or `aria-labelledby`)  
  - a tooltip with the same text (shown on hover/focus)

- **All labels must be translatable.**  
  Don’t hard-code English strings.

Toggle and stateful controls
----------------------------
- Label the **result of the action**, not the current state.
  - good: “Expand sidebar” (when it’s collapsed)  
  - good: “Collapse sidebar” (when it’s expanded)  
  - bad: “Toggle sidebar”

- For switches, use a clear pair:
  - “Enable dark mode” / “Disable dark mode”

- Update ARIA attributes (`aria-expanded`, `aria-pressed`, etc.) when state changes so assistive tech can keep up.

Consistency
-----------
- Reuse the same label for the same action everywhere.  
  If a three-dot menu is called “More actions” in one place, don’t call it “Options” elsewhere.

- If two similar-looking icons do different things, qualify them:
  - “Open page actions”  
  - “Open image actions”

Examples
--------

+---------------------+---------------+------------------------------+
| Element             | bad           | good                         |
+=====================+===============+==============================+
| Sidebar toggle      | Toggle        | Expand sidebar / Collapse    |
|                     |               | sidebar                       |
+---------------------+---------------+------------------------------+
| Search icon         | (no label)    | Search site                  |
+---------------------+---------------+------------------------------+
| Three-dots menu     | …             | More actions                 |
+---------------------+---------------+------------------------------+
| User avatar menu    | (no label)    | Account menu                 |
+---------------------+---------------+------------------------------+
| Help icon           | ?             | Help and support             |
+---------------------+---------------+------------------------------+

Implementation notes
--------------------
- Tooltip and accessible labels should come from the translation framework.
- Keep tooltip text and ARIA label in sync.
- Update labels dynamically if the control’s state changes.
- For bigger regions (sidebars, modals, toolbars) give the container a clear ARIA landmark or label.

References
----------
- WCAG 2.2 and ATAG 2.0
- GOV.UK Design System accessibility guidance
- USWDS accessibility docs
- Material Design: icon button accessibility
- Carbon Design System: icon button guidelines
- Apple HIG accessibility notes
