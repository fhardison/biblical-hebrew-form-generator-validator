---
name: Use uv for running tests and managing dependencies
description: User prefers uv for running tests and managing Python dependencies in this project
type: feedback
---

Always use `uv run pytest` to run tests and `uv add` to manage dependencies. Do not use `python -m pytest` directly.

**Why:** User explicitly corrected this when plain `python -m pytest` was suggested.

**How to apply:** Any time tests need to be run or dependencies added in this project, use uv commands.
