#!/usr/bin/env python3
"""開発成果物の静的整合性チェッカー。

要求仕様書、アーキテクチャ設計書、テスト仕様書、テストコード、
製品コードが4つの開発ルールに従って相互に追跡可能か検査する。
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
TEST_RULE = ROOT / "docs" / "test_doxygen_guideline.md"
PRODUCT_RULE = ROOT / "docs" / "product_code_guideline.md"
TRACE_RULE = ROOT / "docs" / "traceability_rules.md"
PROCESS_RULE = ROOT / "docs" / "development_process_guideline.md"
WORKFLOW = ROOT / ".github" / "workflows" / "test.yml"
TEST_ROOT = ROOT / "tests"


REQ_PATTERN = r"REQ-[A-Z0-9]+-\d{3}"
TEST_PATTERN = r"TEST-(?:UNIT-\d{3}|UC-\d{2}-\d{2})"
UC_PATTERN = r"UC-\d{2}"


class Checker:
    """4つの開発ルールに対応する静的検査を実行する。"""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.requirement_ids: set[str] = set()
        self.test_ids: set[str] = set()
        self.product_api_targets: set[str] = set()
        self.test_api_targets: set[str] = set()

    def error(self, rule: str, message: str) -> None:
        self.errors.append(f"[{rule}] {message}")

    def read(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            self.error("process", f"{path.relative_to(ROOT)} cannot be read: {exc}")
            return ""

    def duplicate_ids(self, values: list[str], label: str) -> None:
        seen: set[str] = set()
        for value in values:
            if value in seen:
                self.error("traceability", f"{label}: duplicate ID {value}")
            seen.add(value)

    def check_process_rule(self) -> None:
        required = (
            REQ_DOC,
            ARCH_DOC,
            TEST_SPEC,
            TEST_RULE,
            PRODUCT_RULE,
            TRACE_RULE,
            PROCESS_RULE,
            WORKFLOW,
        )
        for path in required:
            if not path.exists():
                self.error("process", f"required artifact is missing: {path.relative_to(ROOT)}")

        process = self.read(PROCESS_RULE)
        workflow = self.read(WORKFLOW)
        for phrase in ("要求仕様", "アーキテクチャ設計", "テスト仕様", "テストコード実装", "製品コード実装"):
            if phrase not in process:
                self.error("process", f"development process rule does not define: {phrase}")
        if "tools/check_artifacts.py" not in workflow:
            self.error("process", "test CI does not execute tools/check_artifacts.py")
        if "python -m unittest discover -s tests" not in workflow:
            self.error("process", "test CI does not execute tests from tests/")

    def check_requirements(self) -> None:
        text = self.read(REQ_DOC)
        ids = re.findall(rf"^#### ({REQ_PATTERN})", text, re.MULTILINE)
        self.duplicate_ids(ids, "requirements")
        self.requirement_ids = set(ids)
        if not ids:
            self.error("traceability", "requirements: no requirement IDs found")

        for match in re.finditer(
            rf"^#### ({REQ_PATTERN}).*?(?=^#### |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        ):
            req_id, block = match.groups()
            if block.count("関連成果物") != 1:
                self.error("traceability", f"{req_id}: related-artifacts block must occur exactly once")
            for marker in ("[[ARCH:", "[[TESTSPEC:", "[[API:"):
                if marker not in block:
                    self.error("traceability", f"{req_id}: missing {marker} link")
            for target in re.findall(r"\[\[ARCH:([^\]]+)\]\]", block):
                if not re.fullmatch(UC_PATTERN, target):
                    self.error("traceability", f"{req_id}: invalid architecture target {target}")
            for target in re.findall(r"\[\[TESTSPEC:([^\]]+)\]\]", block):
                if not re.fullmatch(TEST_PATTERN, target):
                    self.error("traceability", f"{req_id}: invalid test-spec target {target}")

    def check_architecture(self) -> None:
        text = self.read(ARCH_DOC)
        uc_ids = re.findall(r"^## 3\.[1-6] (UC-\d{2}) ", text, re.MULTILINE)
        if uc_ids != [f"UC-{i:02d}" for i in range(1, 7)]:
            self.error("traceability", "architecture: sections 3.1-3.6 must contain UC-01 through UC-06")
        for req_id in re.findall(r"\[\[REQ:([^\]]+)\]\]", text):
            if req_id not in self.requirement_ids:
                self.error("traceability", f"architecture: unknown requirement link {req_id}")
        for api in re.findall(r"\[\[API:([^\]]+)\]\]", text):
            if not re.fullmatch(r"[A-Za-z_][\w.]*", api):
                self.error("traceability", f"architecture: invalid API link {api}")

    def check_test_spec(self) -> None:
        text = self.read(TEST_SPEC)
        ids = re.findall(
            rf"^\| <a id=\"[^\"]+\"></a>({TEST_PATTERN}) \|",
            text,
            re.MULTILINE,
        )
        self.duplicate_ids(ids, "test-spec")
        self.test_ids = set(ids)
        if not ids:
            self.error("traceability", "test-spec: no detailed test IDs found")
        for line in text.splitlines():
            if not re.match(r'^\\| <a id="test-[^"]+"></a>TEST-', line):
                continue
            if "[[TESTCODE" not in line:
                self.error("traceability", f"test-spec: missing test-code link: {line[:100]}")
            for req_id in re.findall(REQ_PATTERN, line):
                if req_id not in self.requirement_ids:
                    self.error("traceability", f"test-spec: unknown requirement ID {req_id}")
        for target in re.findall(r"\[\[TESTCODE(?:_SHORT)?:([^\]]+)\]\]", text):
            if not re.fullmatch(r"[A-Za-z_][\w.]+", target):
                self.error("traceability", f"test-spec: invalid test-code target {target}")

    def collect_product_api_targets(self) -> None:
        for path in sorted(ROOT.glob("*.py")):
            if path.name.startswith("test_"):
                continue
            module = path.stem
            try:
                tree = ast.parse(self.read(path), filename=str(path))
            except SyntaxError as exc:
                self.error("product", f"{path.relative_to(ROOT)}: syntax error: {exc}")
                continue
            self.product_api_targets.add(module)
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.product_api_targets.add(f"{module}.{node.name}")
                    for parent in ast.walk(node):
                        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)) and parent is not node:
                            self.product_api_targets.add(f"{module}.{node.name}.{parent.name}")

    def collect_test_api_targets(self) -> None:
        for path in sorted(TEST_ROOT.rglob("test_*.py")):
            module = f"tests.{path.stem}"
            try:
                tree = ast.parse(self.read(path), filename=str(path))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                    self.test_api_targets.add(f"{module}.{node.name}")
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef) and any(child is node for child in parent.body):
                            self.test_api_targets.add(f"{module}.{parent.name}.{node.name}")

    def check_api_links(self) -> None:
        combined = self.read(REQ_DOC) + self.read(ARCH_DOC) + self.read(TEST_SPEC)
        for target in re.findall(r"\[\[API:([^\]]+)\]\]", combined):
            if target not in self.product_api_targets:
                self.error("traceability", f"unknown product API target: {target}")
        for target in re.findall(r"\[\[TESTCODE(?:_SHORT)?:([^\]]+)\]\]", combined):
            if target not in self.test_api_targets:
                self.error("traceability", f"unknown test-code API target: {target}")

    def check_test_code_rule(self) -> None:
        found: list[str] = []
        required_labels = ("テスト目的:", "テスト手順:", "パスクライテリア:", "検証根拠:")
        for path in sorted(TEST_ROOT.rglob("test_*.py")):
            source = self.read(path)
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError as exc:
                self.error("test", f"{path.relative_to(ROOT)}: syntax error: {exc}")
                continue
            lines = source.splitlines()
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
                    continue
                doc = ast.get_docstring(node, clean=False) or ""
                ids = re.findall(TEST_PATTERN, doc)
                if len(ids) != 1:
                    self.error("test", f"{path.relative_to(ROOT)}:{node.lineno}: exactly one TEST ID is required")
                    continue
                test_id = ids[0]
                found.append(test_id)
                for label in required_labels:
                    if label not in doc:
                        self.error("test", f"{path.relative_to(ROOT)}:{node.lineno}: {test_id} missing {label}")
                if "期待結果:" in doc:
                    self.error("test", f"{path.relative_to(ROOT)}:{node.lineno}: {test_id} uses 期待結果 instead of パスクライテリア")
                preceding = "\n".join(lines[max(0, node.lineno - 4): node.lineno - 1])
                if test_id not in preceding:
                    self.error("test", f"{path.relative_to(ROOT)}:{node.lineno}: {test_id} missing source comment")
        self.duplicate_ids(found, "test-code")
        for test_id in found:
            if test_id not in self.test_ids:
                self.error("test", f"{test_id} is absent from test-spec")

    def check_product_code_rule(self) -> None:
        """製品コードAPIのdocstring規約をASTで確認する。"""
        for path in sorted(ROOT.glob("*.py")):
            if path.name.startswith("test_"):
                continue
            source = self.read(path)
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError:
                continue
            if not ast.get_docstring(tree):
                self.error("product", f"{path.relative_to(ROOT)}: missing module docstring")
            for node in ast.walk(tree):
                if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name.startswith("_"):
                    continue
                if not ast.get_docstring(node):
                    self.error("product", f"{path.relative_to(ROOT)}:{node.lineno}: {node.name} missing docstring")

    def check_traceability_rule(self) -> None:
        text = self.read(TRACE_RULE)
        for phrase in ("REQ-", "TEST-UNIT-", "[[ARCH:", "[[API:", "[[TESTSPEC:", "[[TESTCODE_SHORT:"):
            if phrase not in text:
                self.error("traceability", f"traceability rule does not define {phrase}")
        for path in (REQ_DOC, ARCH_DOC, TEST_SPEC):
            content = self.read(path)
            for req_id in re.findall(r"\[\[REQ:([^\]]+)\]\]", content):
                if req_id not in self.requirement_ids:
                    self.error("traceability", f"{path.name}: unknown REQ link {req_id}")

    def run(self) -> int:
        self.check_process_rule()
        if self.errors:
            self.report()
            return 1
        self.check_requirements()
        self.check_architecture()
        self.check_test_spec()
        self.collect_product_api_targets()
        self.collect_test_api_targets()
        self.check_api_links()
        self.check_test_code_rule()
        self.check_product_code_rule()
        self.check_traceability_rule()
        if self.errors:
            self.report()
            return 1
        print("Static artifact check: PASSED")
        print("Rules checked: development process, traceability, product code, test code")
        return 0

    def report(self) -> None:
        print("Static artifact check: FAILED")
        for error in self.errors:
            print(f"- {error}")


if __name__ == "__main__":
    sys.exit(Checker().run())
