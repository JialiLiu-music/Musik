#!/usr/bin/env python3
"""Render paper figures from frozen machine-readable reports only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MODELS = ("b0", "b1", "b2", "b3", "s1")
STRATA = ("0-1s", "1-3s", "3-5s", ">5s")
COLORS = {"b0": "#6b7280", "b1": "#2563eb", "b2": "#059669", "b3": "#d97706", "s1": "#dc2626"}


def read_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"frozen report not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def import_pyplot():
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise RuntimeError("matplotlib is required to render figures") from error
    return plt


def validate_paper_report(report: dict) -> None:
    protocol = report.get("protocol", {})
    if protocol.get("models") != list(MODELS):
        raise ValueError("paper report model protocol mismatch")
    if protocol.get("splits") != {"val": 31, "test": 30}:
        raise ValueError("paper report split protocol mismatch")
    for split in ("val", "test"):
        for model in MODELS:
            metric = report["summary"][split][model]["ccc_mean"]
            if metric["mean"] is None:
                raise ValueError(f"missing ccc_mean: {split}/{model}")


def validate_analysis_report(report: dict) -> None:
    protocol = report.get("protocol", {})
    if protocol.get("unit") != "track" or protocol.get("test_tracks") != 30:
        raise ValueError("analysis report track protocol mismatch")
    if protocol.get("structure_is_automatic_input_not_ground_truth") is not True:
        raise ValueError("analysis report structure boundary is not marked automatic")
    for model in ("b2", "s1"):
        for label in STRATA:
            if report["boundary_error"][model][label]["mae"]["track_mean"] is None:
                raise ValueError(f"missing boundary MAE: {model}/{label}")


def render_model_comparison(report: dict, output: Path) -> None:
    plt = import_pyplot()
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True, constrained_layout=True)
    positions = range(len(MODELS))
    for axis, split, title in zip(axes, ("val", "test"), ("Validation", "Test")):
        means = [report["summary"][split][model]["ccc_mean"]["mean"] for model in MODELS]
        stds = [report["summary"][split][model]["ccc_mean"]["std"] or 0.0 for model in MODELS]
        axis.bar(positions, means, yerr=stds, capsize=4, color=[COLORS[m] for m in MODELS], alpha=0.9)
        axis.axhline(0, color="#374151", linewidth=0.8)
        axis.set_title(title)
        axis.set_xticks(list(positions), [model.upper() for model in MODELS])
        axis.set_xlabel("Model")
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Track-level mean CCC")
    figure.suptitle("Frozen model comparison")
    figure.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(figure)


def render_boundary_error(report: dict, output: Path) -> None:
    plt = import_pyplot()
    figure, axis = plt.subplots(figsize=(7, 4.2), constrained_layout=True)
    positions = list(range(len(STRATA)))
    width = 0.36
    for offset, model in ((-width / 2, "b2"), (width / 2, "s1")):
        values = [report["boundary_error"][model][label]["mae"]["track_mean"] for label in STRATA]
        axis.bar([position + offset for position in positions], values, width=width, label=model.upper(), color=COLORS[model])
    axis.set_xticks(positions, STRATA)
    axis.set_xlabel("Distance to nearest internal automatic boundary")
    axis.set_ylabel("Track-level MAE")
    axis.set_title("Descriptive boundary-distance error")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.25)
    figure.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-report", type=Path, required=True)
    parser.add_argument("--analysis-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    paper_report = read_json(args.paper_report)
    analysis_report = read_json(args.analysis_report)
    validate_paper_report(paper_report)
    validate_analysis_report(analysis_report)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    render_model_comparison(paper_report, args.output_dir / "figure-model-comparison.png")
    render_boundary_error(analysis_report, args.output_dir / "figure-boundary-error.png")
    metadata = {
        "source_reports": [str(args.paper_report), str(args.analysis_report)],
        "figures": ["figure-model-comparison.png", "figure-boundary-error.png"],
        "unit": "track",
        "automatic_structure_is_not_ground_truth": True,
        "test_results_are_read_only": True,
    }
    (args.output_dir / "figures-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"PAPER_FIGURES_OK output_dir={args.output_dir}")


if __name__ == "__main__":
    main()