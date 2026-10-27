# video-clips 视频切片与引流复盘

把直播、访谈或讲解里的有用内容剪成完整短视频，再根据发布数据改下一批。

这是一套给 AI 助手用的 Skill，整理了选片、剪辑、字幕核对和发布后复盘的方法。适合有长视频素材，希望持续做切片的创作者、讲师和运营团队。

## 能帮你做什么

- 找出值得单独讲清楚的片段，注明原片时间和选择理由。
- 调整开头、删掉重复，保留关键解释、实例和适用条件，交付完整视频。
- 按目标平台准备标题、封面、字幕和发布文案。
- 复盘播放与留存，并在有可靠业务记录时分析有效咨询、线索和成交。

方法里特别强调两件事。剪完之后，观众要能听懂原本的问题和回答；复盘时，要把播放量、评论互动和实际线索分别看清楚。

## 先了解使用条件

需要一个能读取本地文件、执行命令并支持 Skills 的 AI 助手。本仓库按 Codex 的 Skill 结构整理，其他助手需按各自的安装方式使用，未逐个平台验证。

实际出片需要可用的视频处理工具，例如 FFmpeg，以及素材、字幕或转写能力。仓库提供方法、模板和一个复盘脚本，不附带剪辑软件、模型、API 密钥或视频素材。没有出片工具时，助手应明确交付范围，不能把选段建议当作已剪好的视频。

HotClip 是可选工具，见 [接入说明](references/hotclip.md)。不使用 HotClip 也可以按本 Skill 工作。云端模型等服务可能另行收费，是否使用取决于你的环境和选择。

## 安装到 Codex

最省事的方式是在 Codex 中发送下面这句话，让内置安装工具读取整个仓库。

```text
使用 $skill-installer，从 https://github.com/xingmou123/video-clips 安装 video-clips，保留完整的 references、assets、scripts 和 agents 目录。
```

也可以下载 [版本安装包](https://github.com/xingmou123/video-clips/releases/latest)，解压后将完整的 `video-clips` 文件夹放到用户技能目录。

- Windows 用 `%USERPROFILE%\.agents\skills\video-clips`
- macOS / Linux 用 `~/.agents/skills/video-clips`
- 只供当前项目使用时，放到项目的 `.agents/skills/video-clips`

最终应能找到 `video-clips/SKILL.md`。不要只复制这一份文件，也不要把同名 Skill 重复装到多个位置。安装后在技能列表里确认能找到它；未出现时重启 Codex。安装位置与发现方式参考 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)，2026-10-27 核对。

## 装好后怎么说

第一次剪片，把原视频放在当前项目能访问的位置，然后告诉助手素材在哪里、给谁看、希望观众看完做什么。

```text
使用 $video-clips，从 ./sources/直播回放.mp4 中挑选适合新手看的片段。
先给我候选和原片时间，选定后剪成完整视频，配字幕、标题和封面。
保留能讲清问题的解释和实例。
```

如果已经有字幕或剪辑表，一起提供，避免重复转写或重新选段。

发布后可以这样复盘。

```text
使用 $video-clips，根据 ./work/发布数据 里的记录，复盘这一批切片。
把播放、留存和实际线索分开分析，指出证据不足的地方，给出下一批具体改法。
```

第一次使用时，助手可从 [项目配置模板](assets/clip-project.template.json) 建立项目入口。里面填你自己的素材位置、目标人群和数据来源，不需要复制以前的聊天。

## 复盘脚本怎么跑

脚本只用 Python 标准库，建议 Python 3.10 或更新版本。它读取你提供的 JSON，不登录平台，也不自动抓取后台数据。

在本仓库目录运行。

```bash
python scripts/review_metrics.py examples/demo-snapshot.json --output review.json
```

[示例数据](examples/demo-snapshot.json) 全部为虚构演示。示例视频长 100 秒，平均观看 20 秒，脚本会算出平均观看占比 20%；示例中精确播放 1000 次、同窗口确认有效线索 3 条，会算出每千次播放有效线索 3 条。它们不代表真实账号效果。

使用自己的数据时，从 [快照模板](assets/snapshot.template.json) 复制修改。缺少的数据保留 `null`，不要填成零；线索归属不清、播放数被取整或窗口不一致时，脚本会保留计算限制，不强行评出赢家。

复核现有脚本的边界行为可运行以下命令。

```bash
python -m unittest discover -s tests -v
```

## 文件入口

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | AI 助手读取的总入口 |
| [剪辑方法](references/editing.md) | 选片、开头、正文取舍、画面声音和成片检查 |
| [交付与发布](references/delivery.md) | 标题封面、承接方式与发布核对 |
| [指标与诊断](references/measurement.md) | 数据口径、线索归属和下一批改法 |
| [迭代与团队](references/learning.md) | 团队接续、实验和有依据的方法更新 |
| [HotClip 接入](references/hotclip.md) | 可选工具的字幕复用、选段和导出 |

## 使用边界

这套方法不保证播放量或成交。自动字幕要对照音频，技术结论和个人经历要回到原始材料核实。发布、私信、评论或投流按你给助手的实际授权执行。

Skill 本身不会定时运行。需要周期复盘时，另行配置宿主支持的定时任务，并确认数据权限和实际运行结果。

仓库只包含通用方法、空白模板、脚本和虚构示例。你自己的账号、客户资料和后台导出留在业务项目中。若启用云端模型，要按实际功能确认会发送哪些文字或图片。

## 许可

采用 [MIT License](LICENSE)，可使用、修改和分享，分发时保留许可与版权声明。外部工具、模型及你处理的素材遵循各自的许可和授权范围。
