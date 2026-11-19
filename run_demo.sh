#!/usr/bin/env bash
# Regenerate data, run all five agent variants, and compare each against the baseline.
set -e
cd "$(dirname "$0")"
python3 scripts/generate_data.py
for variant in baseline chatty sloppy stale no_abstain; do
  echo "=== $variant ==="
  python3 -m traj run --config configs/$variant.json --out-dir outputs/run_$variant || true
done
for variant in chatty sloppy stale no_abstain; do
  python3 -m traj compare \
    --baseline outputs/run_baseline/summary.json \
    --current outputs/run_$variant/summary.json \
    --out outputs/comparison_$variant.md || true
done
echo "Done. Reports in outputs/*/report.md, comparisons in outputs/comparison_*.md"
