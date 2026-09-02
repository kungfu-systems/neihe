#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""Deterministic local runtime for the Neihe shared-brain module."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


CONFIG_SCHEMA = "neihe.shared-brain-locator/v1"
CANDIDATE_SCHEMA = "neihe.experience-candidate/v1"
DEFAULT_CONFIG = Path.home() / ".neihe" / "config.json"
SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "shared-brain"
REQUIRED_FILES = (
    "AGENTS.md",
    "ABOUT_ME.md",
    "PROJECTS.md",
    "EXPERIENCE_CANDIDATES.md",
    "rules/ADOPTED_RULES.md",
)
WRITE_LOCK = ".neihe-write.lock"


class SharedBrainError(RuntimeError):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


def _absolute_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve(strict=False)


def _config_path(argument: str | None) -> Path:
    configured = argument or os.environ.get("NEIHE_CONFIG")
    return _absolute_path(configured) if configured else DEFAULT_CONFIG


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SharedBrainError(
            f"{label}-missing", f"{label}不存在：{path}", path=str(path)
        ) from error
    except (OSError, json.JSONDecodeError) as error:
        raise SharedBrainError(
            f"{label}-invalid", f"无法读取有效的{label}：{path}", path=str(path)
        ) from error
    if not isinstance(value, dict):
        raise SharedBrainError(
            f"{label}-invalid", f"{label}必须是 JSON 对象：{path}", path=str(path)
        )
    return value


def _load_locator(config_path: Path) -> dict[str, Any]:
    value = _load_json(config_path, label="locator")
    if set(value) != {"schema", "shared_brain_path"}:
        raise SharedBrainError(
            "locator-invalid",
            "定位文件字段不符合当前版本。",
            path=str(config_path),
        )
    if value.get("schema") != CONFIG_SCHEMA:
        raise SharedBrainError(
            "locator-schema-unsupported",
            f"不支持的定位文件版本：{value.get('schema')!r}",
            path=str(config_path),
        )
    raw_path = value.get("shared_brain_path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise SharedBrainError(
            "locator-invalid", "定位文件缺少 shared_brain_path。", path=str(config_path)
        )
    return {**value, "shared_brain_path": str(_absolute_path(raw_path))}


def _inspection(brain: Path, config_path: Path) -> dict[str, Any]:
    missing = [
        relative
        for relative in REQUIRED_FILES
        if not (brain / relative).exists() and not (brain / relative).is_symlink()
    ]
    invalid = [
        relative
        for relative in REQUIRED_FILES
        if ((brain / relative).exists() or (brain / relative).is_symlink())
        and ((brain / relative).is_symlink() or not (brain / relative).is_file())
    ]
    return {
        "path": str(brain),
        "config_path": str(config_path),
        "exists": brain.is_dir(),
        "complete": brain.is_dir() and not missing and not invalid,
        "missing_files": missing,
        "invalid_entries": invalid,
        "write_lock_present": (brain / WRITE_LOCK).exists(),
    }


def _read_registered_brain(config_path: Path, *, require_complete: bool) -> tuple[Path, dict[str, Any]]:
    locator = _load_locator(config_path)
    brain = _absolute_path(locator["shared_brain_path"])
    inspection = _inspection(brain, config_path)
    if not inspection["exists"]:
        raise SharedBrainError(
            "shared-brain-missing",
            "定位文件存在，但共享大脑目录已经失效。",
            **inspection,
        )
    if require_complete and not inspection["complete"]:
        raise SharedBrainError(
            "shared-brain-incomplete",
            "共享大脑结构不完整，请先运行 doctor 或重新执行 init。",
            **inspection,
        )
    return brain, inspection


def _atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".config.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        if temporary.exists():
            temporary.unlink()


def _registration_plan(config_path: Path, brain: Path, *, replace: bool) -> dict[str, Any]:
    if config_path.exists():
        current = _load_locator(config_path)
        current_path = _absolute_path(current["shared_brain_path"])
        if current_path != brain and not replace:
            raise SharedBrainError(
                "registration-conflict",
                "已经登记了另一个共享大脑；如需迁移，请显式使用 register --replace。",
                config_path=str(config_path),
                registered_path=str(current_path),
                requested_path=str(brain),
            )
        action = "preserve" if current_path == brain else "replace"
    else:
        action = "create"
    return {
        "action": action,
        "config_path": str(config_path),
        "shared_brain_path": str(brain),
    }


def _write_registration(config_path: Path, brain: Path) -> None:
    _atomic_json_write(
        config_path,
        {"schema": CONFIG_SCHEMA, "shared_brain_path": str(brain)},
    )


def command_locate(args: argparse.Namespace) -> dict[str, Any]:
    config_path = _config_path(args.config)
    brain, inspection = _read_registered_brain(config_path, require_complete=True)
    return {
        "schema": "neihe.shared-brain-command-result/v1",
        "ok": True,
        "command": "locate",
        "shared_brain_path": str(brain),
        "inspection": inspection,
    }


def command_doctor(args: argparse.Namespace) -> dict[str, Any]:
    config_path = _config_path(args.config)
    brain, inspection = _read_registered_brain(config_path, require_complete=False)
    ok = bool(inspection["complete"] and not inspection["write_lock_present"])
    return {
        "schema": "neihe.shared-brain-command-result/v1",
        "ok": ok,
        "command": "doctor",
        "shared_brain_path": str(brain),
        "inspection": inspection,
        "recommendation": (
            "ready"
            if ok
            else "重新执行 init 补齐缺失文件；写锁存在时先确认没有其它 Agent 正在写入。"
        ),
    }


def _template_plan(brain: Path) -> list[dict[str, str]]:
    if brain.is_symlink():
        raise SharedBrainError(
            "shared-brain-symlink-refused",
            "共享大脑目标本身不能是符号链接。",
            path=str(brain),
        )
    if brain.exists() and not brain.is_dir():
        raise SharedBrainError(
            "shared-brain-not-directory",
            "共享大脑目标存在但不是目录。",
            path=str(brain),
        )
    plan: list[dict[str, str]] = []
    for relative in REQUIRED_FILES:
        source = TEMPLATE_ROOT / relative
        destination = brain / relative
        if not source.is_file():
            raise SharedBrainError(
                "template-missing", "Skill 缺少共享大脑模板。", path=str(source)
            )
        if destination.is_symlink() or (destination.exists() and not destination.is_file()):
            raise SharedBrainError(
                "destination-conflict",
                "目标位置存在同名符号链接或非文件条目，拒绝继续。",
                path=str(destination),
            )
        plan.append(
            {
                "path": str(destination),
                "action": "preserve" if destination.is_file() else "create",
            }
        )
    return plan


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    config_path = _config_path(args.config)
    brain = _absolute_path(args.path)
    files = _template_plan(brain)
    registration = _registration_plan(config_path, brain, replace=False)
    if args.apply:
        brain.mkdir(parents=True, exist_ok=True)
        for relative in REQUIRED_FILES:
            source = TEMPLATE_ROOT / relative
            destination = brain / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                with source.open("rb") as incoming, destination.open("xb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
        _write_registration(config_path, brain)
    return {
        "schema": "neihe.shared-brain-command-result/v1",
        "ok": True,
        "command": "init",
        "mode": "applied" if args.apply else "dry-run",
        "shared_brain_path": str(brain),
        "files": files,
        "registration": registration,
    }


def command_register(args: argparse.Namespace) -> dict[str, Any]:
    config_path = _config_path(args.config)
    brain = _absolute_path(args.path)
    inspection = _inspection(brain, config_path)
    if not inspection["complete"]:
        raise SharedBrainError(
            "shared-brain-incomplete",
            "只能登记结构完整的共享大脑；请先运行 init。",
            **inspection,
        )
    registration = _registration_plan(config_path, brain, replace=args.replace)
    if args.apply:
        _write_registration(config_path, brain)
    return {
        "schema": "neihe.shared-brain-command-result/v1",
        "ok": True,
        "command": "register",
        "mode": "applied" if args.apply else "dry-run",
        "shared_brain_path": str(brain),
        "registration": registration,
    }


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SharedBrainError(
            "candidate-invalid", f"经验候选字段必须是非空文本：{field}", field=field
        )
    if "\x00" in value:
        raise SharedBrainError(
            "candidate-invalid", f"经验候选字段包含非法空字符：{field}", field=field
        )
    return value.strip()


def _text_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise SharedBrainError(
            "candidate-invalid", f"经验候选字段必须是文本数组：{field}", field=field
        )
    result = [_required_text(item, field) for item in value]
    if not result and not allow_empty:
        raise SharedBrainError(
            "candidate-invalid", f"经验候选字段不能为空数组：{field}", field=field
        )
    return result


def _candidate(path: Path) -> dict[str, Any]:
    value = _load_json(path, label="candidate")
    allowed = {
        "schema",
        "title",
        "source_task",
        "what_happened",
        "facts",
        "inferences",
        "candidate_rule",
        "trigger_conditions",
        "not_applicable",
        "next_validation",
    }
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise SharedBrainError(
            "candidate-invalid", "经验候选包含未知字段。", unknown_fields=unknown
        )
    if value.get("schema") != CANDIDATE_SCHEMA:
        raise SharedBrainError(
            "candidate-schema-unsupported",
            f"不支持的经验候选版本：{value.get('schema')!r}",
        )
    normalized = {
        "schema": CANDIDATE_SCHEMA,
        "title": _required_text(value.get("title"), "title"),
        "source_task": _required_text(value.get("source_task"), "source_task"),
        "what_happened": _required_text(value.get("what_happened"), "what_happened"),
        "facts": _text_list(value.get("facts"), "facts"),
        "inferences": _text_list(value.get("inferences"), "inferences", allow_empty=True),
        "candidate_rule": _required_text(value.get("candidate_rule"), "candidate_rule"),
        "trigger_conditions": _text_list(value.get("trigger_conditions"), "trigger_conditions"),
        "not_applicable": _text_list(value.get("not_applicable"), "not_applicable"),
        "next_validation": _required_text(value.get("next_validation"), "next_validation"),
    }
    return normalized


def _candidate_id(candidate: dict[str, Any]) -> str:
    encoded = json.dumps(
        candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _bullet(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\n  ")


def _candidate_markdown(candidate: dict[str, Any], identifier: str) -> str:
    def bullets(values: list[str]) -> str:
        return "\n".join(f"  - {_bullet(item)}" for item in values) if values else "  - 无"

    return (
        f"\n## 候选经验：{_bullet(candidate['title'])}\n\n"
        f"- 候选 ID：`{identifier}`\n"
        f"- 来源任务：{_bullet(candidate['source_task'])}\n"
        f"- 当时发生了什么：{_bullet(candidate['what_happened'])}\n"
        f"- 什么是事实：\n{bullets(candidate['facts'])}\n"
        f"- 什么仍是推断：\n{bullets(candidate['inferences'])}\n"
        f"- 候选规则：{_bullet(candidate['candidate_rule'])}\n"
        f"- 触发条件：\n{bullets(candidate['trigger_conditions'])}\n"
        f"- 不适用范围：\n{bullets(candidate['not_applicable'])}\n"
        f"- 下一次如何验证：{_bullet(candidate['next_validation'])}\n"
        "- 状态：候选\n"
        "- 人工审查：待审核\n"
    )


def _append_candidate(target: Path, marker: str, markdown: str) -> str:
    lock = target.parent / WRITE_LOCK
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise SharedBrainError(
            "shared-brain-busy",
            "共享大脑正被另一个 Agent 写入；本次没有修改文件。",
            lock_path=str(lock),
        ) from error
    try:
        current = target.read_text(encoding="utf-8")
        if marker in current:
            return "already-present"
        with target.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(markdown)
        return "appended"
    finally:
        lock.rmdir()


def command_candidate_add(args: argparse.Namespace) -> dict[str, Any]:
    config_path = _config_path(args.config)
    brain, _inspection_value = _read_registered_brain(config_path, require_complete=True)
    candidate = _candidate(_absolute_path(args.input))
    identifier = _candidate_id(candidate)
    marker = f"- 候选 ID：`{identifier}`"
    markdown = _candidate_markdown(candidate, identifier)
    target = brain / "EXPERIENCE_CANDIDATES.md"
    current = target.read_text(encoding="utf-8")
    state = "already-present" if marker in current else "would-append"
    if args.apply and state != "already-present":
        state = _append_candidate(target, marker, markdown)
    return {
        "schema": "neihe.shared-brain-command-result/v1",
        "ok": True,
        "command": "candidate-add",
        "mode": "applied" if args.apply else "dry-run",
        "candidate_id": identifier,
        "state": state,
        "target": str(target),
        "adopted_rules_modified": False,
        "preview": markdown if not args.apply else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Neihe shared-brain locator and safe file runtime"
    )
    parser.add_argument(
        "--config",
        help="Locator file override. Defaults to NEIHE_CONFIG or ~/.neihe/config.json.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("locate", help="Locate and verify the registered shared brain.")
    commands.add_parser("doctor", help="Inspect the registered shared-brain structure.")

    current = commands.add_parser("init", help="Plan or create the minimal shared brain.")
    current.add_argument("--path", required=True, help="Shared-brain directory.")
    current.add_argument("--apply", action="store_true", help="Apply the displayed plan.")

    current = commands.add_parser(
        "register", help="Plan or register an existing complete shared brain."
    )
    current.add_argument("--path", required=True, help="Existing shared-brain directory.")
    current.add_argument("--replace", action="store_true", help="Replace a different registration.")
    current.add_argument("--apply", action="store_true", help="Apply the displayed plan.")

    current = commands.add_parser(
        "candidate-add", help="Plan or append one structured experience candidate."
    )
    current.add_argument("--input", required=True, help="Candidate JSON input file.")
    current.add_argument("--apply", action="store_true", help="Append the candidate.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "locate": command_locate,
        "doctor": command_doctor,
        "init": command_init,
        "register": command_register,
        "candidate-add": command_candidate_add,
    }
    try:
        result = handlers[args.command](args)
        code = 0 if result.get("ok") else 1
    except SharedBrainError as error:
        result = {
            "schema": "neihe.shared-brain-command-result/v1",
            "ok": False,
            "command": args.command,
            "code": error.code,
            "message": error.message,
            **error.details,
        }
        code = 2
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
