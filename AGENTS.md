# AGENTS Instruction

The main developer documentation for Wagtail lives in the `docs/contributing` directory. Here is additional guidance for agents.

## Pull request guidelines

- Describe the "why" of the changes, why the proposed solution is the right one.
- Highlight areas of the proposed changes that require careful review.
- Always add a disclaimer to the PR description mentioning how AI agents are involved with the contribution.

### AI/Agent disclosure template (copy/paste & edit):

**If human review has *not yet* occurred (use this initially):**
> This pull request includes code written with the assistance of AI.  
> The code has **not yet been reviewed** by a human.

## Wagtail-specific pitfalls for AI agents

### StreamField and StreamBlock template access

- Wagtail's StreamBlock and StreamField use the same template syntax, but they differ from standard Django field access. When you use StreamField and other custom block types in Wagtail templates, you usually need to use the value property in your data variables. 
