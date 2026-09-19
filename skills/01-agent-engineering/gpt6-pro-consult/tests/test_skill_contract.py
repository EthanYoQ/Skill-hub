#!/usr/bin/env python3

from __future__ import annotations

import json
import importlib.util
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_in_app_browser_is_the_only_default_surface(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Codex 内置侧边 Browser（in-app Browser）", skill)
        self.assertIn("选择独立的 `iab` 绑定", skill)
        self.assertIn("当前主 Codex task 执行", skill)
        self.assertIn("不调用 Chrome 扩展、Chrome CLI、OpenCLI", skill)
        self.assertIn("不切换 Chrome 或 CLI", skill)
        self.assertNotIn("browser:control-in-app-browser", skill)

    def test_trigger_contract_covers_explicit_and_consequential_design_decisions(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        description = skill.split("---", 2)[1]
        self.assertIn(
            "description: 用户点名或需作实质性软件设计、架构取舍时调用侧边 Browser。",
            description,
        )
        self.assertIn("显式点名 `$gpt6-pro-consult`", skill)
        self.assertIn("实质性权衡仍未解决", skill)
        self.assertIn("普通实现、已确定方案的落地、小型孤立修复", skill)
        self.assertIn("自动附件或私有上下文共享，不触发本 Skill", skill)
        self.assertIn("不触发", skill)
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: true", metadata)
        for broad_trigger in ("任何软件设计", "均用 Codex", "Pro 编排循环时也触发"):
            self.assertNotIn(broad_trigger, description)

    def test_explicit_consultation_authorizes_direct_dispatch_after_preflight(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("通过所有发送前门槛后直接以一次 `Enter` 提交", skill)
        self.assertIn("不得再询问“是否发送”", skill)
        self.assertIn("明确要求预览、仅起草或暂停", skill)

    def test_reviewer_and_orchestrator_modes_are_defined(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("### Reviewer（默认）", skill)
        self.assertIn("### Orchestrator loop", skill)
        self.assertIn("默认最多进行 3 个", skill)
        self.assertIn("Pro 不能扩大权限", skill)

    def test_required_public_files_exist_and_legacy_cli_files_do_not(self) -> None:
        for relative in (
            "agents/openai.yaml",
            "references/in-app-browser-workflow.md",
            "references/context-packet-template.md",
            "scripts/build_attachment_bundle.py",
            "scripts/check_packet_safety.py",
            "scripts/validate_session_evidence.py",
            "references/session-evidence-template.json",
        ):
            self.assertTrue((SKILL_DIR / relative).is_file(), relative)

        for relative in (
            "references/chrome-workflow.md",
            "references/opencli-fallback.md",
            "scripts/run_gpt6_pro_consult.py",
            "scripts/extract_chatgpt_reply.py",
            "tests/test_model_selection.py",
        ):
            self.assertFalse((SKILL_DIR / relative).exists(), relative)

    def test_evals_assert_in_app_browser_routing(self) -> None:
        eval_path = SKILL_DIR / "evals/evals.json"
        if not eval_path.exists():
            self.skipTest("runtime package intentionally excludes eval fixtures")
        payload = json.loads(eval_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["skill_name"], "gpt6-pro-consult")
        self.assertGreaterEqual(len(payload["evals"]), 6)
        for case in payload["evals"]:
            joined = " ".join([case["expected_output"], *case["assertions"]])
            self.assertTrue("in-app Browser" in joined or "iab" in joined, case["id"])
            self.assertIn("Chrome", joined, case["id"])
            self.assertGreaterEqual(len(case["assertions"]), 5, case["id"])

    def test_browser_workflow_has_truthfulness_and_duplicate_send_gates(self) -> None:
        workflow = (SKILL_DIR / "references/in-app-browser-workflow.md").read_text(encoding="utf-8")
        for required in (
            'agent.browsers.get("iab")',
            "iab.documentation()",
            "file chooser",
            "distinctive prefix",
            "NOT_SENT",
            "SENT",
            "UNKNOWN",
            "不冒险重复提交",
            "iab-consultation-evidence.json",
            "Browser session ID",
            "当前主 Codex task",
        ):
            self.assertIn(required, workflow)

    def test_completed_evidence_requires_clean_release(self) -> None:
        validator_path = SKILL_DIR / "scripts/validate_session_evidence.py"
        spec = importlib.util.spec_from_file_location("sol_pro_evidence_validator", validator_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        ref = {"browser_id": "iab-1", "tab_id": "tab-1", "tab_url": "https://chatgpt.com/c/1"}
        payload = {
            "schema_version": "1.4",
            "task_run_id": "run-1",
            "executed_by": "main-codex-task",
            "browser": {"type": "iab", **ref},
            "model_gate": {
                "binding_ref": ref,
                "captured_at": "2026-07-29T00:00:00Z",
                "gpt_6_pro_checked": True,
                "observed_signals": ["model picker GPT-6 Pro [selected]"],
            },
            "late_clean_gate": {
                "binding_ref": ref,
                "captured_at": "2026-07-29T00:00:30Z",
                "checked_after_model_menu": True,
                "composer_empty": True,
                "composer_text_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "project_context": False,
                "pending_upload_count": 0,
                "unexpected_attachments": [],
            },
            "packet": {
                "sha256": "a" * 64,
                "distinctive_prefix": "case-prefix",
                "sentinel": "GPT6_PRO_RESULT_CASE",
                "visible_attachments": [],
            },
            "dispatch": {
                "binding_ref": ref,
                "captured_at": "2026-07-29T00:01:00Z",
                "state": "SENT",
                "send_click_count": 1,
                "submit_signal": "user-turn",
            },
            "response": {
                "binding_ref": ref,
                "captured_at": "2026-07-29T00:02:00Z",
                "generation_complete": True,
                "assistant_turn_sha256": "b" * 64,
                "assistant_sentinel_verified": True,
            },
            "route_exclusions": {
                "chrome_extension_used": False,
                "chrome_cli_used": False,
                "opencli_used": False,
                "external_playwright_used": False,
            },
            "cleanup": {
                "captured_at": "2026-07-29T00:03:00Z",
                "release_method": "tab.close",
                "release_completed": True,
                "release_was_last_browser_action": True,
                "retained_tab_status": "none",
                "pre_release_project_context": False,
                "pre_release_draft_present": False,
                "pre_release_pending_upload_count": 0,
                "pre_release_unexpected_attachments": [],
            },
            "binding_verified": True,
            "status": "completed",
        }
        self.assertEqual(module.validate(payload), [])
        payload["model_gate"]["observed_signals"] = ["composer control 6 Pro", "model picker 最新 [selected]"]
        self.assertEqual(module.validate(payload), [])

        payload["model_gate"]["observed_signals"] = [
            "composer control 5.6 Pro",
            "model picker 最新 [selected]",
        ]
        self.assertIn("a complete GPT-6 Pro model signal is required", module.validate(payload))
        payload["model_gate"]["observed_signals"] = ["Pro"]
        self.assertIn("a complete GPT-6 Pro model signal is required", module.validate(payload))
        payload["model_gate"]["observed_signals"] = ["model picker GPT-6 Pro [selected]"]
        payload["late_clean_gate"]["composer_empty"] = False
        self.assertIn("late clean gate must prove empty composer", module.validate(payload))
        payload["late_clean_gate"]["composer_empty"] = True
        payload["cleanup"]["pre_release_pending_upload_count"] = 1
        self.assertIn("cleanup must prove no pending uploads", module.validate(payload))

    def test_completion_requires_same_session_browser_evidence(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "会话绑定证据",
            "Browser session ID",
            "同一 Browser session",
            "静态路由测试",
            "Session-bound evidence: complete | incomplete",
            "validate_session_evidence.py",
            "Evidence binding verified: yes | no",
        ):
            self.assertIn(required, skill)

    def test_each_task_uses_a_clean_isolated_tab_and_always_releases(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        workflow = (SKILL_DIR / "references/in-app-browser-workflow.md").read_text(encoding="utf-8")
        for required in (
            "每个新 Codex task 都新建专用 ChatGPT tab",
            "不得复用其他 task 留下的对话、Project、composer 草稿、附件或上传状态",
            "释放本 task 自建 tab",
            "close()",
            "不得把未完成上传或含附件草稿的 tab 标为 `handoff`",
            "延迟净空门",
            "STALE_COMPOSER_BLOCKER",
            "Temporary Chat 不能作为隔离回退",
        ):
            self.assertIn(required, skill)

        for required in (
            "非 Project 的新对话",
            "composer 为空",
            "不属于本 task",
            "强制清理与释放",
            "作为本 turn 的最后一个 Browser 动作",
            "release 方法",
            "不得把污染 tab 保留为 handoff",
            "不要 claim、关闭或修改无法证明属于本 task 的用户 tab",
            "checked_after_model_menu",
            "composer_text_sha256",
            "Temporary Chat",
        ):
            self.assertIn(required, workflow)

    def test_no_personal_absolute_paths(self) -> None:
        forbidden = (
            "C:" + "/Users/",
            "C:" + "\\Users\\",
            "/Users/" + "me/",
            "deepsight_" + "vault",
        )
        for path in SKILL_DIR.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                text = path.read_text(encoding="utf-8", errors="ignore")
                for value in forbidden:
                    self.assertNotIn(value, text, str(path))


if __name__ == "__main__":
    unittest.main()
