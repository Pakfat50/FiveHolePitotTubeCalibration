#!/usr/bin/env python3
"""静的な成果物整合性チェック。

要求仕様書、アーキテクチャ設計書、テスト仕様書、テストコード、
製品コードの最低限のID・リンク・docstring形式を検査する。
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQ_DOC = ROOT / "docs" / "pitot_calibration_gui_spec.md"
ARCH_DOC = ROOT / "docs" / "architecture_design.md"
TEST_SPEC = ROOT / "docs" / "test_specification.md"
TEST_ROOT = ROOT / "tests"


class Checker:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def duplicate_ids(self, values: list[str], label: str) -> None:
        seen: set[str] = set()
        for value in values:
            if value in seen:
                self.error(f"{label}: duplicate ID {value}")
            seen.add(value)

    def check_requirements(self) -> set[str]:
        text = REQ_DOC.read_text(encoding="utf-8")
        ids = re.findall(r"^#### (REQ-[A-Z0-9]+-\d{3})", text, re.MULTILINE)
        self.duplicate_ids(ids, "requirements")
        if not ids:
            self.error("requirements: no requirement IDs found")

        for match in re.finditer(
            r"^#### (REQ-[A-Z0-9]+-\d{3}).*?(?=^#### |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        ):
            req_id, block = match.groups()
            if "関連成果物" not in block:
                self.error(f"requirements: {req_id} has no related-artifacts block")
            if "[[ARCH:" not in block:
                self.error(f"requirements: {req_id} has no architecture link")
            if "[[TESTSPEC:" not in block:
                self.error(f"requirements: {req_id} has no test-spec link")
            for target in re.findall(r"\[\[ARCH:([^\]]+)\]\]", block):
                if not re.fullmatch(r"UC-\d{2}", target):
                    self.error(f"requirements: {req_id} has invalid ARCH target {target}")
            for target in re.findall(r"\[\[TESTSPEC:([^\]]+)\]\]", block):
                if not re.fullmatch(r"TEST-(?:UNIT-\d{3}|UC-\d{2}-\d{2})", target):
                    self.error(f"requirements: {req_id} has invalid TESTSPEC target {target}")
        return set(ids)

    def check_architecture(self, req_ids: set[str]) -> None:
        text = ARCH_DOC.read_text(encoding="utf-8")
        uc_ids = re.findall(r"^## 3\.[1-6] (UC-\d{2}) ", text, re.MULTILINE)
        if uc_ids != [f"UC-{i:02d}" for i in range(1, 7)]:
            self.error("architecture: sections 3.1-3.6 must contain UC-01 through UC-06")
        for req_id in re.findall(r"\[\[REQ:([^\]]+)\]\]", text):
            if req_id not in req_ids:
                self.error(f"architecture: unknown requirement link {req_id}")
        for api in re.findall(r"\[\[API:([^\]]+)\]\]", text):
            if not re.fullmatch(r"[A-Za-z_][\w.]*", api):
                self.error(f"architecture: invalid API link {api}")

    def check_test_spec(self, req_ids: set[str]) -> set[str]:
        text = TEST_SPEC.read_text(encoding="utf-8")
        ids = re.findall(r"^\\| <a id=\"test-[^\"]+\"></a>(TEST-(?:UNIT-\d{3}|UC-\d{2}-\d{2})) \\|", text, re.MULTILINE)
        self.duplicate_ids(ids, "test-spec")
        if not ids:
            self.error("test-spec: no detailed test IDs found")
        for line in text.splitlines():
            if "| TEST-" not in line:
                continue
            if "[[TESTCODE_SHORT:" not in line:
                self.error(f"test-spec: missing test-code link: {line[:100]}")
            for req_id in re.findall(r"REQ-[A-Z0-9]+-\d{3}", line):
                if req_id not in req_ids:
                    self.error(f"test-spec: unknown requirement ID {req_id}")
        for target in re.findall(r"\[\[TESTCODE_SHORT:([^\]]+)\]\]", text):
            if not re.fullmatch(r"[A-Za-z_][\w.]+", target):
                self.error(f"test-spec: invalid test-code target {target}")
        return set(ids)

    @staticmethod
    def test_functions(path: Path) -> list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, list[str]]]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        lines = path.read_text(encoding="utf-8").splitlines()
        result = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                result.append((node, lines))
        return result

    def check_test_code(self, test_ids: set[str]) -> None:
        found: list[str] = []
        for path in sorted(TEST_ROOT.rglob("test_*.py")):
            try:
                functions = self.test_functions(path)
            except SyntaxError as exc:
                self.error(f"test-code: {path}: syntax error: {exc}")
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            for node, _ in functions:
                doc = ast.get_docstring(node, clean=False) or ""
                ids = re.findall(r"TEST-(?:UNIT-\d{3}|UC-\d{2}-\d{2})", doc)
                if len(ids) != 1:
                    self.error(f"test-code: {path}:{node.lineno}: test method must contain exactly one TEST ID")
                    continue
                test_id = ids[0]
                found.append(test_id)
                required = ("テスト目的:", "テスト手順:", "パスクライテリア:", "検証根拠:")
                for label in required:
                    if label not in doc:
                        self.error(f"test-code: {path}:{node.lineno}: {test_id} missing {label}")
                if "期待結果:" in doc:
                    self.error(f"test-code: {path}:{node.lineno}: {test_id} uses 期待結果 instead of パスクライテリア")
                preceding = "\n".join(lines[max(0, node.lineno - 4): node.lineno - 1])
                if test_id not in preceding:
                    self.error(f"test-code: {path}:{node.lineno}: {test_id} missing source comment")
        self.duplicate_ids(found, "test-code")
        for test_id in found:
            if test_id not in test_ids:
                self.error(f"test-code: {test_id} is absent from test-spec")

    def check_product_code(self) -> None:
        for path in sorted(ROOT.glob("*.py")):
            if path.name.startswith("test_"):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                self.error(f"product-code: {path}: syntax error: {exc}")
                continue
            if not ast.get_docstring(tree):
                self.error(f"product-code: {path}: missing module docstring")
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue
                    if not ast.get_docstring(node):
                        self.error(f"product-code: {path}:{node.lineno}: {node.name} missing docstring")

    def run(self) -> int:
        for path in (REQ_DOC, ARCH_DOC, TEST_SPEC):
            if not path.exists():
                self.error(f"missing document: {path}")
        if not self.errors:
            req_ids = self.check_requirements()
            self.check_architecture(req_ids)
            test_ids = self.check_test_spec(req_ids)
            self.check_test_code(test_ids)
            self.check_product_code()
        if self.errors:
            print("Static artifact check: FAILED")
            for error in self.errors:
                print(f"- {error}")
            return 1
        print("Static artifact check: PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(Checker().run())
