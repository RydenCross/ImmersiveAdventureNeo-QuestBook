# Verified Update Apply, Rollback, and Recovery

Commit 107 completes the staged-update lifecycle. Pending manifests are revalidated before use, artifacts must remain inside the staging directory, size and SHA-256 are checked again, and symlinks are rejected.

Linux AppImage replacement is opt-in and atomic. The current AppImage is copied to a rollback artifact before replacement and a deterministic `rollback-update.json` manifest records recovery state. Windows updates use a verified installer handoff; dry-run mode prints the exact silent installer command without executing it.

```bash
python -m generator quest-maker-update-apply ~/.ftb-quest-maker/updates/pending-update.json --current-executable /path/to/FTBQuestMaker.AppImage
python -m generator quest-maker-update-rollback ~/.ftb-quest-maker/updates/rollback-update.json
python -m generator update-application-audit
```

Both mutating commands require `--execute`; without it they are safe plans.
