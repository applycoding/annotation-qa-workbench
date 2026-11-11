# SPDX-License-Identifier: Apache-2.0

"""Console script ``aqw``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from annotation_qa_workbench.report import (
    compute_warehouse_scores,
    load_report,
    recompute_and_validate,
    write_report,
)
from annotation_qa_workbench.scenes import generate_warehouse_v1, write_scene


def cmd_generate(out: Path) -> int:
    scene = generate_warehouse_v1()
    write_scene(out / "warehouse_v1.json", scene)
    return 0


def cmd_score(scene: Path, out: Path, sha: str | None) -> int:
    if not sha or len(sha) != 40:
        print("missing or invalid --sha", file=sys.stderr)
        return 1
    payload = compute_warehouse_scores(scene)
    payload["git_sha"] = sha
    payload["sample"] = False
    write_report(out, payload)
    errors = recompute_and_validate(payload, scene, require_ci=True, expect_sha=sha)
    if errors:
        print("gate failures:", errors, file=sys.stderr)
        return 1
    return 0


def cmd_report_check(path: Path, require_ci: bool, expect_sha: str | None) -> int:
    report = load_report(path)
    scene = Path("fixtures/scenes/warehouse_v1.json")
    errors = recompute_and_validate(
        report, scene, require_ci=require_ci, expect_sha=expect_sha
    )
    if errors:
        print("validation errors:", errors, file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aqw")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate")
    gen.add_argument("--out", type=Path, required=True)

    score = sub.add_parser("score")
    score.add_argument("--scene", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    score.add_argument("--sha", type=str, default=None)

    rep = sub.add_parser("report")
    rep.add_argument("--check", action="store_true")
    rep.add_argument("path", type=Path)
    rep.add_argument("--require-ci", action="store_true")
    rep.add_argument("--expect-sha", type=str, default=None)

    args = parser.parse_args(argv)
    if args.command == "generate":
        return cmd_generate(args.out)
    if args.command == "score":
        return cmd_score(args.scene, args.out, args.sha)
    if args.command == "report":
        if not args.check:
            print("only --check is supported", file=sys.stderr)
            return 2
        return cmd_report_check(args.path, args.require_ci, args.expect_sha)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
