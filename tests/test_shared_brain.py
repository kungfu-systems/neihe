# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "shared_brain.py"
REQUIRED_FILES = (
    "AGENTS.md",
    "ABOUT_ME.md",
    "PROJECTS.md",
    "EXPERIENCE_CANDIDATES.md",
    "rules/ADOPTED_RULES.md",
)


class SharedBrainRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config = self.root / "config" / "config.json"
        self.brain = self.root / "我的AI共享大脑"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *arguments: str, expected: int = 0):
        command = [
            sys.executable,
            str(SCRIPT),
            "--config",
            str(self.config),
            *arguments,
        ]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def initialize(self):
        return self.run_cli("init", "--path", str(self.brain), "--apply")

    def test_locate_without_registration_fails_without_discovery(self):
        result = self.run_cli("locate", expected=2)
        self.assertEqual(result["code"], "locator-missing")
        self.assertFalse(self.config.exists())
        self.assertFalse(self.brain.exists())

    def test_init_is_dry_run_by_default_then_creates_and_locates(self):
        plan = self.run_cli("init", "--path", str(self.brain))
        self.assertEqual(plan["mode"], "dry-run")
        self.assertFalse(self.brain.exists())
        self.assertFalse(self.config.exists())

        applied = self.initialize()
        self.assertEqual(applied["mode"], "applied")
        for relative in REQUIRED_FILES:
            self.assertTrue((self.brain / relative).is_file(), relative)
        locator = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(locator["shared_brain_path"], str(self.brain.resolve()))

        located = self.run_cli("locate")
        self.assertEqual(located["shared_brain_path"], str(self.brain.resolve()))
        self.assertTrue(located["inspection"]["complete"])

    def test_repeated_init_preserves_user_content(self):
        self.initialize()
        about = self.brain / "ABOUT_ME.md"
        about.write_text("# 我的真实内容\n", encoding="utf-8")
        result = self.initialize()
        self.assertEqual(result["mode"], "applied")
        self.assertEqual(about.read_text(encoding="utf-8"), "# 我的真实内容\n")

    def test_registration_conflict_requires_explicit_replace(self):
        self.initialize()
        other = self.root / "另一个共享大脑"
        for relative in REQUIRED_FILES:
            target = other / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("placeholder\n", encoding="utf-8")

        conflict = self.run_cli("register", "--path", str(other), expected=2)
        self.assertEqual(conflict["code"], "registration-conflict")
        replaced = self.run_cli(
            "register", "--path", str(other), "--replace", "--apply"
        )
        self.assertEqual(replaced["registration"]["action"], "replace")
        self.assertEqual(
            self.run_cli("locate")["shared_brain_path"], str(other.resolve())
        )

    def test_doctor_reports_incomplete_structure_without_repairing_it(self):
        self.initialize()
        (self.brain / "PROJECTS.md").unlink()
        result = self.run_cli("doctor", expected=1)
        self.assertFalse(result["ok"])
        self.assertIn("PROJECTS.md", result["inspection"]["missing_files"])
        self.assertFalse((self.brain / "PROJECTS.md").exists())

    def test_required_file_symlink_is_rejected(self):
        self.initialize()
        outside = self.root / "outside.md"
        outside.write_text("must remain untouched\n", encoding="utf-8")
        candidates = self.brain / "EXPERIENCE_CANDIDATES.md"
        candidates.unlink()
        candidates.symlink_to(outside)

        doctor = self.run_cli("doctor", expected=1)
        self.assertIn("EXPERIENCE_CANDIDATES.md", doctor["inspection"]["invalid_entries"])
        init = self.run_cli("init", "--path", str(self.brain), expected=2)
        self.assertEqual(init["code"], "destination-conflict")
        self.assertEqual(outside.read_text(encoding="utf-8"), "must remain untouched\n")

    def test_candidate_add_is_review_pending_idempotent_and_never_adopts(self):
        self.initialize()
        candidate_path = self.root / "candidate.json"
        candidate_path.write_text(
            json.dumps(
                {
                    "schema": "neihe.experience-candidate/v1",
                    "title": "先展示具体结果",
                    "source_task": "一次 Agent 入门直播",
                    "what_happened": "抽象开场后，观众反复询问课程能做什么。",
                    "facts": ["观众连续提出了相同问题。"],
                    "inferences": ["抽象表达可能提高了理解成本。"],
                    "candidate_rule": "面向新学员时，先展示一个具体结果。",
                    "trigger_conditions": ["公开入门直播"],
                    "not_applicable": ["已经完成基础课的专业班"],
                    "next_validation": "比较两种开场前十分钟的提问情况。",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        candidates = self.brain / "EXPERIENCE_CANDIDATES.md"
        adopted = self.brain / "rules" / "ADOPTED_RULES.md"
        before_candidates = candidates.read_text(encoding="utf-8")
        before_adopted = adopted.read_text(encoding="utf-8")

        plan = self.run_cli("candidate-add", "--input", str(candidate_path))
        self.assertEqual(plan["state"], "would-append")
        self.assertEqual(candidates.read_text(encoding="utf-8"), before_candidates)

        applied = self.run_cli(
            "candidate-add", "--input", str(candidate_path), "--apply"
        )
        self.assertEqual(applied["state"], "appended")
        self.assertFalse(applied["adopted_rules_modified"])
        self.assertIn("人工审查：待审核", candidates.read_text(encoding="utf-8"))
        self.assertEqual(adopted.read_text(encoding="utf-8"), before_adopted)

        duplicate = self.run_cli(
            "candidate-add", "--input", str(candidate_path), "--apply"
        )
        self.assertEqual(duplicate["state"], "already-present")
        self.assertEqual(
            candidates.read_text(encoding="utf-8").count(applied["candidate_id"]),
            1,
        )

    def test_candidate_write_lock_fails_closed(self):
        self.initialize()
        candidate_path = self.root / "candidate.json"
        candidate_path.write_text(
            json.dumps(
                {
                    "schema": "neihe.experience-candidate/v1",
                    "title": "有锁时不写",
                    "source_task": "并发测试",
                    "what_happened": "另一个 Agent 正在写入。",
                    "facts": ["写锁目录存在。"],
                    "inferences": [],
                    "candidate_rule": "检测到锁时停止。",
                    "trigger_conditions": ["共享大脑并发写入"],
                    "not_applicable": ["只读操作"],
                    "next_validation": "移除测试锁后重新运行。",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        target = self.brain / "EXPERIENCE_CANDIDATES.md"
        before = target.read_text(encoding="utf-8")
        (self.brain / ".neihe-write.lock").mkdir()
        result = self.run_cli(
            "candidate-add", "--input", str(candidate_path), "--apply", expected=2
        )
        self.assertEqual(result["code"], "shared-brain-busy")
        self.assertEqual(target.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
