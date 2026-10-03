# AGENTS Instruction

The main developer documentation for Wagtail lives in the `docs/contributing` directory. Here is additional guidance for agents.

## Pull request guidelines

- Always use our pull request template: `.github/PULL_REQUEST_TEMPLATE.md`.
- Highlight areas of the proposed changes that require careful review.
- Do not add commits that are unrelated to the purpose of the PR. Check the commit history against the latest upstream main branch before pushing to ensure that only relevant commits are included in the PR.

### The PR description must come from your operator, not you

A human skimming AI-generated output and deciding "yes, that looks right" is not a meaningful review — a passive check doesn't tell you whether anyone actually understands the change. Requiring the operator to be the one who writes and submits the description is a much stronger signal that a human is genuinely in the loop, rather than automating the entire bug-fixing process end to end.

- Do not write a PR description and open the PR yourself. If your operator asks for help, you may draft a summary of the "why" for them to edit, but they must be the one who puts the final description in the PR body and creates the PR.
- If your operator hasn't done this yet, do not open the PR. Hand the branch back and let them write the description — using your draft as a starting point if they want — and submit it themselves through the GitHub web interface.
- Wagtail requires contributors to disclose AI usage via the "AI usage" section of the pull request template — don't leave that section out or tell the operator it's optional. When providing a draft PR description, advise the operator to keep that section intact (filling it in themselves) rather than overwriting the whole template with your draft.

## Wagtail-specific pitfalls for AI agents

### StreamField and StreamBlock template access

- Wagtail's StreamBlock and StreamField use the same template syntax, but they differ from standard Django field access. When you use StreamField and other custom block types in Wagtail templates, you usually need to use the value property in your data variables.
