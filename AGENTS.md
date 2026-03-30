# AGENTS Instruction

The main developer documentation for Wagtail lives in the `docs/contributing` directory. Here is additional guidance for agents.

## Pull request guidelines

- Describe the "why" of the changes — why these changes are necessary and why the proposed solution is the right one.
- Highlight areas of the proposed changes that require careful review.
- Always add a disclaimer to the PR description mentioning how AI agents are involved with the contribution.

### AI/Agent disclosure template (copy/paste & edit):

**If human review has *not yet* occurred (use this initially):**
> This pull request includes code written with the assistance of AI.  
> The code has **not yet been reviewed** by a human.

## Wagtail-specific pitfalls for AI agents

### StreamField and StreamBlock template access

- Wagtail's StreamBlock and StreamField use a template syntax that differs from standard Django field access. When working with StreamField or custom block types in templates, you should access block data via the `value` property.

Example:
```
{% for block in page.body %}
  {{ block.value }}
{% endfor %}
```
Failing to use `block.value` may result in unexpected output or missing data in templates.
Use `block.value` (or `self.value` inside a block template) rather than treating the field like a plain Django model field.
