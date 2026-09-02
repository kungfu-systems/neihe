# 共享大脑与经验蒸馏

## 何时使用

用户经常向新 Agent 重复交代背景，想跨会话保留方向和规则，或希望把一次工作经验变成后续可复用能力时使用。

## 一句话定义

共享大脑是人和多个 Agent 都会回读的长期工作说明书。它保存方向、规则、项目坐标、状态、证据坐标和经过人工采纳的经验，而不是收藏所有文件和聊天记录。

学员版口诀：

> 一个大脑源，多个工作仓；中央存规则和坐标，项目存正文和成果。

## 使用体验

本模块通过 `scripts/shared_brain.py` 提供确定性的跨会话定位。不要依赖模型凭记忆猜测目录，也不要扫描整台电脑。

当用户提到“共享大脑”“长期规则”或“经验蒸馏”时：

1. 先解析当前已安装 Neihe Skill 的目录；脚本路径始终相对于本文件所属 Skill 根目录。
2. 优先运行 `locate`。定位成功后，再读取当前任务需要的共享大脑文件。
3. 定位文件不存在或失效时，直接说明情况，并询问用户要创建或重新登记的位置。
4. 任何创建、重新登记或追加经验的操作都先运行 dry-run，把完整目标路径和计划展示给用户；得到明确确认后才添加 `--apply`。

普通 SkillHub 安装的脚本通常位于 `~/.hermes/skills/neihe/scripts/shared_brain.py`。如果 Hermes 使用外部 Skill 目录，以 `skill_view` 返回的实际 Skill 位置为准，不猜测路径。

以下示例使用 `python3`。Windows 环境如果只有 `python` 或 `py -3`，使用已经随 Hermes 可用的解释器；不要为了本模块自动安装或替换系统 Python。

```bash
# 新会话先定位；只读，不修改文件
python3 "<Neihe Skill目录>/scripts/shared_brain.py" --pretty locate

# 检查定位和文件结构；只读
python3 "<Neihe Skill目录>/scripts/shared_brain.py" --pretty doctor
```

默认定位文件是 `~/.neihe/config.json`。它只保存 schema 和共享大脑的绝对路径，不保存个人正文。测试或多配置场景可以在子命令前传入 `--config <路径>`，也可以设置 `NEIHE_CONFIG`。

## 最小结构

```text
我的AI共享大脑/
├── AGENTS.md
├── ABOUT_ME.md
├── PROJECTS.md
├── EXPERIENCE_CANDIDATES.md
└── rules/
    └── ADOPTED_RULES.md
```

| 文件 | 作用 |
| --- | --- |
| `AGENTS.md` | 所有 Agent 应先遵守的协作方式、边界和安全红线 |
| `ABOUT_ME.md` | 长期方向、稳定偏好、明确禁区和待核验画像 |
| `PROJECTS.md` | 项目用途、权威路径、当前状态、风险和下一步 |
| `EXPERIENCE_CANDIDATES.md` | 可能值得复用、但尚未被永久采纳的经验 |
| `ADOPTED_RULES.md` | 已经人工确认、能够改变未来行为的规则 |

首次建立时先创建最小骨架，不要求用户一次填满全部文件。已有同名文件时先读取和比较，不直接覆盖。

首次创建必须先预览，再由用户确认执行：

```bash
python3 "<Neihe Skill目录>/scripts/shared_brain.py" --pretty init \
  --path "<用户选择的位置>/我的AI共享大脑"

python3 "<Neihe Skill目录>/scripts/shared_brain.py" --pretty init \
  --path "<用户选择的位置>/我的AI共享大脑" \
  --apply
```

`init` 只创建缺失文件，已有文件一律保留；定位文件已经指向另一个目录时会停止。迁移现有共享大脑时，先用 `register` dry-run，得到用户明确确认后再同时使用 `--replace --apply`。

```bash
python3 "<Neihe Skill目录>/scripts/shared_brain.py" --pretty register \
  --path "<现有共享大脑目录>"

python3 "<Neihe Skill目录>/scripts/shared_brain.py" --pretty register \
  --path "<现有共享大脑目录>" \
  --replace \
  --apply
```

## 经验蒸馏闭环

```text
真实工作经验
  → 保留发生了什么和可查证据
  → Agent 提出候选规则
  → 人工检查来源、范围和风险
  → 下一次类似任务试跑
  → 采纳、修订、废弃或继续保持候选
```

候选经验至少记录：

```markdown
## 候选经验：标题

- 来源任务：
- 当时发生了什么：
- 什么是事实：
- 什么仍是推断：
- 候选规则：
- 触发条件：
- 不适用范围：
- 下一次如何验证：
- 状态：候选
- 人工审查：待审核
```

没有来源、触发条件、不适用范围或验证方法的内容，继续保留为候选，不直接写入高优先级规则。

需要让脚本追加候选时，先准备一个临时 JSON 文件：

```json
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
  "next_validation": "比较两种开场前十分钟的提问情况。"
}
```

先预览，确认后追加：

```bash
python3 "<Neihe Skill目录>/scripts/shared_brain.py" --pretty candidate-add \
  --input "<临时候选文件.json>"

python3 "<Neihe Skill目录>/scripts/shared_brain.py" --pretty candidate-add \
  --input "<临时候选文件.json>" \
  --apply
```

相同候选会得到相同内容哈希并保持幂等。脚本只写入 `EXPERIENCE_CANDIDATES.md`，不提供自动采纳命令，也不会修改 `ADOPTED_RULES.md`。

## 安全边界

- 不把共享大脑变成所有聊天记录和文件的垃圾场。
- 不因一次情绪或一次对话永久定义用户性格。
- 不默认写入密码、Token、Cookie、医疗信息、学员隐私或私密原文。
- Agent 可以提出规则候选，但不能替用户宣布永久采纳。
- Python 脚本只负责定位、校验、初始化和追加候选；它不能自行判断一条经验已经成为正式规则。
- 新建或修改真实文件前，先说明目标位置和将要写入的内容；已有内容时优先给出合并建议。
