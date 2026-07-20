# Release Archive Unicode Path Contract

This contract validates the final release ZIP against Unicode path ambiguities that can behave differently across filesystems and extraction tools.

It rejects non-NFC names, NFKC/case-fold collisions, control characters, bidirectional formatting controls, and path segments ending in spaces or periods.

```bash
python -m generator release-archive-unicode-path-audit
python -m generator release-archive-unicode-path-audit --format json --output reports/release-archive-unicode-path-audit.json
```
