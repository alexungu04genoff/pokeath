## Git workflow

- After completing a coherent task, run the relevant validations/tests.
- If validation succeeds, review the diff and commit the completed change automatically.
- Do not wait for me to explicitly request a commit.
- Use concise descriptive commit messages.
- Split unrelated changes into separate commits when appropriate.
- Do not commit known broken or incomplete work unless it is explicitly an experimental checkpoint.
- Never force-push, rewrite history, reset away user work, or delete existing commits unless explicitly requested.
- For this repository, push completed validated commits to `origin/main` after committing unless doing so would overwrite/conflict with remote work.
- If push is rejected because the remote changed, stop and report the conflict instead of force-pushing.
