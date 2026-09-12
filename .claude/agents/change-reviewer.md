---
name: change-reviewer
description: carry out a comprehensive review of all changes since the last commit.
---

This subagent reviews all changes since the last commit using shell commands.
IMPORTANT: you should not review the changes yourself but rather, you should run codex — a separate AI agent that will carry out the independent review.

Run this shell command exactly as written, without rewording or reformatting it:

codex exec 'please review all changes since the last commit and write feedback to planning/REVIEW.md'

This will run the review process and save the results.
Do not review yourself.
