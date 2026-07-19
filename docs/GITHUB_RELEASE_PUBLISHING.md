# GitHub Release Publishing

Commit 108 adds deterministic GitHub Release plans and an explicit publishing gate.

Create a local plan without contacting GitHub:

```bash
python -m generator quest-maker-github-release-plan \
  --repository owner/ftb-quest-maker --tag v1.2.3 \
  --notes release-notes.md --asset dist/app.exe --asset dist/app.AppImage \
  --asset dist/update.json
```

Publish only after reviewing the plan and authenticating `gh`:

```bash
python -m generator quest-maker-github-release-publish \
  --repository owner/ftb-quest-maker --tag v1.2.3 \
  --notes release-notes.md --asset dist/app.exe --asset dist/app.AppImage \
  --asset dist/update.json --execute
```

The checked-in `.github/workflows/publish-release.yml` builds on target-host runners, generates update metadata, and publishes assets with the repository-scoped `GITHUB_TOKEN`. No token is stored in source control.

Validate the complete publishing contract with:

```bash
python -m generator github-release-publishing-audit
```
