# Generated Quest Reward Planner

The reward planner turns a generated quest blueprint into a blueprint where every quest has an explicit reward decision. It can add conservative draft rewards or record that a quest intentionally has no reward.

The planner never executes mod code and does not attempt to infer pack economy values from arbitrary item recipes. Automatic rewards use a small cross-pack vanilla utility palette so the result remains portable and easy to review.

## Generate a reward plan

```bash
python -m generator quest-reward-plan /path/to/modpack.mrpack
```

Write the complete rewarded blueprint as JSON:

```bash
python -m generator quest-reward-plan /path/to/modpack.mrpack \
  --target-quests 600 \
  --chapter-size 40 \
  --policy conservative \
  --format json \
  --output quest-reward-plan.json
```

## Policies

- `none` records an intentional no-reward decision for every quest.
- `conservative` rewards terminal milestones and major progression gates.
- `balanced` also rewards periodic progression milestones.
- `generous` additionally rewards chapter-entry milestones and more frequent progress points.

Low-confidence or planner-marked review quests are never rewarded automatically. They receive an explicit no-reward decision until a pack author reviews them.

## Export a rewarded questbook

```bash
python -m generator ftb-quest-export /path/to/modpack.mrpack \
  --destination generated/ftbquests \
  --reward-policy conservative
```

The exporter creates stable FTB reward IDs and writes item rewards using valid FTB Quests reward records. The default export policy is `unassigned`, preserving the unrewarded blueprint unless a policy is requested.

## Review reward decisions

```bash
python -m generator questbook-review /path/to/modpack.mrpack \
  --reward-policy conservative
```

With a reward policy selected, the reviewer no longer reports missing reward decisions. Other editorial findings, such as weak descriptions or low-confidence objectives, remain visible.

## Validate the planner

```bash
python -m generator reward-planner-audit
python -m generator reward-planner-audit \
  --format json \
  --output reports/reward-planner-audit.json
```

The contract verifies complete decisions, conservative reward density, policy scaling, low-confidence protection, deterministic output, reviewer integration, and FTB reward export.
