"""Build the canonical frontend showcase payload from QuantLab local stores."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quantlab.showcase import write_canonical_dashboard_artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="frontend/lib/showcase-payload.json",
        help="dashboard JSON artifact to write",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="quantlab-showcase-") as tmp:
        write_canonical_dashboard_artifact(Path(args.out), Path(tmp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
