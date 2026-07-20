# Secure Application Update Client

Commit 106 adds the client side of the update metadata introduced in Commit 105. The client can inspect a local metadata file or an HTTPS update feed, select the correct Windows or Linux package, compare semantic versions, and stage a verified artifact without executing it.

## Check for an update

```bash
python -m generator quest-maker-update-check \
  https://updates.example.invalid/stable/latest.json \
  --current-version 1.0.0 \
  --channel stable \
  --platform auto
```

Use `--signing-key <path>` to verify HMAC-SHA256 metadata created by `quest-maker-update-metadata`. Add `--require-signature` when unsigned feeds must be rejected.

The update check:

- accepts local metadata paths for offline release testing;
- requires HTTPS for remote metadata and artifact URLs;
- rejects credential-bearing URLs, URL fragments, insecure redirects, unsafe filenames, and unsupported platforms;
- enforces stable, beta, and nightly channel policy;
- compares full semantic versions, including prerelease precedence;
- applies a bounded metadata-download limit;
- verifies signed metadata before offering an artifact; and
- selects exactly one package for the detected or requested platform.

Stable clients accept only stable releases. Beta clients accept stable or beta releases. Nightly clients accept all three channels.

## Stage a verified update

```bash
python -m generator quest-maker-update-stage \
  https://updates.example.invalid/stable/latest.json \
  --current-version 1.0.0 \
  --channel stable \
  --platform auto \
  --destination ~/.ftb-quest-maker/updates
```

Staging is deliberately separate from installation. The command streams the selected artifact into a temporary `.part` file, enforces the declared and configured size limits, verifies the SHA-256 digest, flushes the file, and atomically moves it into place only after all checks pass. A failed or interrupted download leaves no accepted partial artifact.

A successful stage writes `pending-update.json` beside the artifact. The manifest records the current and target versions, channel, platform, source, size, checksum, and verified staged path. It contains no timestamps, so repeated staging of the same release is deterministic. A previously staged artifact with the expected size and digest is reused without another download.

The updater never launches an installer, replaces a running executable, or elevates privileges. Installation remains an explicit user or platform action.

## Limits and exit behavior

`--max-metadata-bytes` defaults to 1 MiB. `--max-artifact-bytes` defaults to 2 GiB. `--timeout` defaults to 15 seconds for each network operation.

Both commands return zero when the operation is valid. Being current is a successful result and does not create a staged artifact. Invalid metadata, rejected channels, missing platform artifacts, signature failures, insecure URLs, size mismatches, and checksum mismatches return a nonzero status.

## Contract audit

```bash
python -m generator application-update-client-audit
python -m generator application-update-client-audit \
  --format json \
  --output reports/application-update-client-audit.json
```

The contract covers semantic-version precedence, signed metadata, current-version handling, verified atomic staging, idempotent reuse, tamper rejection, HTTPS enforcement, and release-channel policy.
