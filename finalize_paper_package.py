#!/usr/bin/env python3
"""Finalize paper tables, figures, hashes, and delivery metadata from frozen reports."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
from types import ModuleType
from typing import Any

MODELS = ("b0", "b1", "b2", "b3", "s1")
SPLITS = ("validation", "test")
AXIS_METRICS = (
    ("valence_ccc", "Valence CCC"),
    ("arousal_ccc", "Arousal CCC"),
    ("valence_mae", "Valence MAE"),
    ("arousal_mae", "Arousal MAE"),
    ("valence_rmse", "Valence RMSE"),
    ("arousal_rmse", "Arousal RMSE"),
)
RENDER_METRICS = ("ccc_mean",) + tuple(metric for metric, _ in AXIS_METRICS)
STRATA = ("0-1s", "1-3s", "3-5s", ">5s")
TABLE_HEADING = "## 表 4 分轴指标引用表"
UNFILLED_TABLE_NOTE = "下表字段必须从远程 `reports/paper-results.json` 复制；当前本地工作区没有该冻结 JSON 副本，因此不填入未经当前文件校验的数值。"
FILLED_TABLE_NOTE = "下表字段已由本地收口脚本从冻结 `paper-results.json` 只读填充；来源文件和 SHA-256 见同目录 `source-sha256.json`。"
NEXT_HEADING = "\n## "
ROW_PATTERN = re.compile(r"^(\|\s*(validation|test)\s*\|\s*(B0|B1|B2|B3|S1)\s*\|)(.*)$")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"frozen report not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def finite_number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ValueError(f"missing or non-finite numeric value: {label}")
    return float(value)


def validate_paper_report(report: dict[str, Any]) -> None:
    protocol = report.get("protocol")
    if not isinstance(protocol, dict):
        raise ValueError("paper report protocol is missing")
    if protocol.get("unit") != "track":
        raise ValueError("paper report unit protocol mismatch")
    if protocol.get("models") != list(MODELS):
        raise ValueError("paper report model protocol mismatch")
    if protocol.get("splits") != {"val": 31, "test": 30}:
        raise ValueError("paper report split protocol mismatch")
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("paper report summary is missing")
    for report_split, split_label in (("val", "validation"), ("test", "test")):
        split_summary = summary.get(report_split)
        if not isinstance(split_summary, dict):
            raise ValueError(f"paper report summary is missing: {report_split}")
        for model in MODELS:
            metrics = split_summary.get(model)
            if not isinstance(metrics, dict):
                raise ValueError(f"paper report model is missing: {report_split}/{model}")
            for metric in RENDER_METRICS:
                item = metrics.get(metric)
                if not isinstance(item, dict):
                    raise ValueError(f"paper report metric is missing: {report_split}/{model}/{metric}")
                finite_number(item.get("mean"), f"{report_split}/{model}/{metric}/mean")
                if metric == "ccc_mean" and item.get("std") is not None:
                    finite_number(item.get("std"), f"{report_split}/{model}/{metric}/std")
                if metric == "ccc_mean" and "std" not in item:
                    raise ValueError(f"paper report ccc_mean std is missing: {report_split}/{model}")


def validate_analysis_report(report: dict[str, Any]) -> None:
    protocol = report.get("protocol")
    if not isinstance(protocol, dict):
        raise ValueError("analysis report protocol is missing")
    if protocol.get("unit") != "track" or protocol.get("test_tracks") != 30:
        raise ValueError("analysis report track protocol mismatch")
    if protocol.get("structure_is_automatic_input_not_ground_truth") is not True:
        raise ValueError("analysis report structure boundary is not marked automatic")
    boundary_error = report.get("boundary_error")
    if not isinstance(boundary_error, dict):
        raise ValueError("analysis report boundary_error is missing")
    for model in ("b2", "s1"):
        model_values = boundary_error.get(model)
        if not isinstance(model_values, dict):
            raise ValueError(f"analysis report boundary model is missing: {model}")
        if tuple(model_values) != STRATA:
            raise ValueError(f"analysis report boundary strata mismatch: {model}")
        for stratum in STRATA:
            values = model_values[stratum]
            try:
                track_mean = values["mae"]["track_mean"]
            except (KeyError, TypeError) as error:
                raise ValueError(f"analysis report boundary MAE is missing: {model}/{stratum}") from error
            finite_number(track_mean, f"boundary_error/{model}/{stratum}/mae/track_mean")


def metric_value(report: dict[str, Any], split: str, model: str, metric: str) -> str:
    report_split = "val" if split == "validation" else "test"
    value = report["summary"][report_split][model.lower()][metric]["mean"]
    return f"{finite_number(value, f'{split}/{model}/{metric}'):.6f}"


def fill_axis_table(template: str, report: dict[str, Any]) -> str:
    if TABLE_HEADING not in template:
        raise ValueError(f"table heading not found: {TABLE_HEADING}")
    start = template.index(TABLE_HEADING)
    end = template.find(NEXT_HEADING, start + len(TABLE_HEADING))
    if end < 0:
        end = len(template)
    section = template[start:end]
    rows = section.replace(UNFILLED_TABLE_NOTE, FILLED_TABLE_NOTE).splitlines()
    expected = [(split, model.upper()) for split in SPLITS for model in MODELS]
    found: list[tuple[str, str]] = []
    replaced: list[str] = []
    for line in rows:
        match = ROW_PATTERN.match(line)
        if not match:
            replaced.append(line)
            continue
        split, model = match.group(2), match.group(3)
        found.append((split, model))
        values = [metric_value(report, split, model, metric) for metric, _ in AXIS_METRICS]
        replaced.append(match.group(1) + " " + " | ".join(values) + " |")
    if found != expected:
        raise ValueError(f"table rows do not match required order: {found}")
    filled_section = "\n".join(replaced)
    if end < len(template) and template[end:].startswith(NEXT_HEADING):
        filled_section += "\n"
    return template[:start] + filled_section + template[end:]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_renderer(path: Path) -> ModuleType:
    if not path.is_file():
        raise FileNotFoundError(f"figure renderer not found: {path}")
    spec = importlib.util.spec_from_file_location("paper_figure_renderer", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load figure renderer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_new_output_dir(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise FileExistsError(f"output path is not a directory: {path}")
        if any(path.iterdir()):
            raise FileExistsError(f"output directory must be new and empty: {path}")
    else:
        path.mkdir(parents=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-report", type=Path, required=True)
    parser.add_argument("--analysis-report", type=Path, required=True)
    parser.add_argument("--table-template", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--renderer", type=Path, default=Path(__file__).with_name("render_paper_figures.py"))
    args = parser.parse_args()

    paper_report = read_json(args.paper_report)
    analysis_report = read_json(args.analysis_report)
    validate_paper_report(paper_report)
    validate_analysis_report(analysis_report)
    if not args.table_template.is_file():
        raise FileNotFoundError(f"table template not found: {args.table_template}")
    template = args.table_template.read_text(encoding="utf-8")
    filled_table = fill_axis_table(template, paper_report)

    ensure_new_output_dir(args.output_dir)
    table_output = args.output_dir / "paper-tables-filled.md"
    table_output.write_text(filled_table, encoding="utf-8")

    renderer = load_renderer(args.renderer)
    renderer.render_model_comparison(paper_report, args.output_dir / "figure-model-comparison.png")
    renderer.render_boundary_error(analysis_report, args.output_dir / "figure-boundary-error.png")
    figures_metadata = {
        "source_reports": [str(args.paper_report), str(args.analysis_report)],
        "figures": ["figure-model-comparison.png", "figure-boundary-error.png"],
        "unit": "track",
        "automatic_structure_is_not_ground_truth": True,
        "test_results_are_read_only": True,
    }
    (args.output_dir / "figures-metadata.json").write_text(
        json.dumps(figures_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    source_paths = [args.paper_report, args.analysis_report, args.table_template, args.renderer]
    source_hashes = {
        str(path): {"sha256": sha256(path), "size_bytes": path.stat().st_size}
        for path in source_paths
    }
    (args.output_dir / "source-sha256.json").write_text(
        json.dumps(source_hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    metadata = {
        "status": "ok",
        "source_reports": [str(args.paper_report), str(args.analysis_report)],
        "source_table_template": str(args.table_template),
        "renderer": str(args.renderer),
        "outputs": [
            "paper-tables-filled.md",
            "figure-model-comparison.png",
            "figure-boundary-error.png",
            "figures-metadata.json",
            "source-sha256.json",
            "delivery-metadata.json",
        ],
        "protocol": {
            "unit": "track",
            "models": list(MODELS),
            "automatic_structure_is_not_ground_truth": True,
            "test_results_are_read_only": True,
        },
        "source_sha256_file": "source-sha256.json",
    }
    (args.output_dir / "delivery-metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"PAPER_PACKAGE_FINALIZED output_dir={args.output_dir}")


if __name__ == "__main__":
    main()