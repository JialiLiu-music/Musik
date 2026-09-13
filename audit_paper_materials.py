#!/usr/bin/env python3
"""Audit local paper materials against the frozen reporting contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MATERIALS = (
    "paper-draft.md",
    "paper-materials.md",
    "paper-tables.md",
    "paper-figures-checklist.md",
    "paper-captions-and-citations.md",
)
REQUIRED_TEXT = (
    "205 首",
    "144/31/30",
    "6150",
    "9225",
    "曲目级",
    "测试集",
    "冻结",
    "自动结构",
    "不是人工",
    "不得从 `ccc_mean` 反推",
)
FROZEN_VALUES = (
    "0.123921",
    "0.027514",
    "0.027084",
    "-0.000430",
    "0.022841",
    "0.981702",
    "0.226977",
)
DANGEROUS_ASSERTIONS = (
    "自动乐段模型普遍优于平坦时序模型",
    "S1 带来稳定、显著的结构增益",
    "All-In-One 自动边界等同于人工结构真值",
)
FROZEN_REPORT_FILES = ("paper-results.json", "formal-test-analysis.json")
FINAL_PACKAGE_FILES = (
    "paper-tables-filled.md",
    "figure-model-comparison.png",
    "figure-boundary-error.png",
    "figures-metadata.json",
    "source-sha256.json",
    "delivery-metadata.json",
)
FROZEN_REPORT_HASHES = {
    "paper-results.json": "7408a199cf28933effbfe5ec14bfe4fb6d8d3d75702d8ace9b9635e9d68c4192",
    "formal-test-analysis.json": "869bc9322b9e544e4bbe53542c77737ae79a3fa1bf04e62d5269bf3aceec95db",
}


def latest_dir(root: Path, prefix: str) -> Path | None:
    candidates = sorted(path for path in root.glob(f"{prefix}*") if path.is_dir())
    return candidates[-1] if candidates else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_frozen_inputs(root: Path) -> dict[str, object]:
    directory = latest_dir(root, "frozen-inputs-")
    missing_files = []
    hash_mismatches = []
    if directory is None:
        missing_files = list(FROZEN_REPORT_FILES)
    else:
        for name in FROZEN_REPORT_FILES:
            path = directory / name
            if not path.is_file():
                missing_files.append(name)
            elif sha256(path) != FROZEN_REPORT_HASHES[name]:
                hash_mismatches.append(name)
    return {
        "directory": str(directory) if directory else None,
        "missing_files": missing_files,
        "hash_mismatches": hash_mismatches,
        "status": "ok" if not missing_files and not hash_mismatches else "blocked",
    }


def audit_final_package(root: Path) -> dict[str, object]:
    directory = latest_dir(root, "final-paper-package-")
    missing_files = []
    invalid_files = []
    if directory is None:
        missing_files = list(FINAL_PACKAGE_FILES)
    else:
        for name in FINAL_PACKAGE_FILES:
            path = directory / name
            if not path.is_file():
                missing_files.append(name)
            elif path.stat().st_size <= 0:
                invalid_files.append(name)
        table_path = directory / "paper-tables-filled.md"
        if table_path.is_file():
            table_text = table_path.read_text(encoding="utf-8")
            if "当前本地工作区没有该冻结 JSON 副本" in table_text or "远程 JSON" in table_text:
                invalid_files.append("paper-tables-filled.md")
        for name in ("figure-model-comparison.png", "figure-boundary-error.png"):
            path = directory / name
            if path.is_file() and not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                invalid_files.append(name)
    return {
        "directory": str(directory) if directory else None,
        "missing_files": missing_files,
        "invalid_files": invalid_files,
        "status": "ok" if not missing_files and not invalid_files else "blocked",
    }


def read_materials(root: Path) -> dict[str, str]:
    materials = {}
    for name in MATERIALS:
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"missing paper material: {path}")
        materials[name] = path.read_text(encoding="utf-8")
    return materials


def audit_materials(materials: dict[str, str]) -> dict[str, object]:
    combined = "\n".join(materials.values())
    missing_text = [item for item in REQUIRED_TEXT if item not in combined]
    missing_values = [item for item in FROZEN_VALUES if item not in combined]
    draft = materials["paper-draft.md"]
    table = materials["paper-tables.md"]
    checklist = materials["paper-figures-checklist.md"]
    captions = materials["paper-captions-and-citations.md"]
    required_sections = [
        heading for heading in (
            "## 1 引言",
            "## 2 数据与任务定义",
            "## 3 模型方法",
            "## 4 实验设置",
            "## 5 结果",
            "## 6 讨论",
            "## 7 局限性",
            "## 8 结论",
        ) if heading not in draft
    ]
    required_tables = [
        heading for heading in ("表 3 曲目级 CCC 均值", "表 5 测试集结构模型配对比较", "表 6 自动边界距离描述性分析")
        if heading not in table
    ]
    required_caption_sections = [
        heading for heading in ("图 3 验证集与测试集模型比较", "图 5 自动边界距离误差", "表 4 分轴指标引用表")
        if heading not in captions
    ]
    forbidden_in_conclusion = [
        phrase for phrase in DANGEROUS_ASSERTIONS
        if phrase in draft
        and "不支持" not in draft[draft.index(phrase) - 80 : draft.index(phrase) + len(phrase) + 30]
    ]
    results = {
        "materials": list(materials),
        "required_text_missing": missing_text,
        "frozen_values_missing": missing_values,
        "paper_sections_missing": required_sections,
        "paper_tables_missing": required_tables,
        "caption_sections_missing": required_caption_sections,
        "dangerous_assertions_in_draft": forbidden_in_conclusion,
        "remote_machine_readable_reports_local_copy": False,
        "status": "blocked" if missing_text or missing_values or required_sections or required_tables or required_caption_sections or forbidden_in_conclusion else "ok",
    }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = audit_materials(read_materials(args.reports_dir))
    frozen_inputs = audit_frozen_inputs(args.reports_dir)
    final_package = audit_final_package(args.reports_dir)
    result["remote_machine_readable_reports_local_copy"] = frozen_inputs["status"] == "ok"
    result["frozen_inputs"] = frozen_inputs
    result["final_package"] = final_package
    if result["status"] == "ok" and (frozen_inputs["status"] != "ok" or final_package["status"] != "ok"):
        result["status"] = "blocked"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PAPER_MATERIALS_AUDIT status={result['status']}")
    print(f"MISSING_TEXT={len(result['required_text_missing'])}")
    print(f"MISSING_VALUES={len(result['frozen_values_missing'])}")
    print(f"MISSING_SECTIONS={len(result['paper_sections_missing']) + len(result['paper_tables_missing']) + len(result['caption_sections_missing'])}")
    print(f"DANGEROUS_ASSERTIONS={len(result['dangerous_assertions_in_draft'])}")
    print(f"FROZEN_INPUTS_STATUS={frozen_inputs['status']}")
    print(f"FINAL_PACKAGE_STATUS={final_package['status']}")
    if result["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()