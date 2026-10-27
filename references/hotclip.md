# HotClip 接入与取舍

仅在用户明确指定 [xixihhhh/hotclip](https://github.com/xixihhhh/hotclip)，且本项目允许使用时读取。先查项目工具采用/停用决定；已有停用决定时，用户明确恢复后再接续，不因仓库、模型或历史脚本仍在而自行试用。不替代本 Skill 的内容完整性、事实与业务效果标准。

## 先确定本次走哪条路

- 已有原文字幕：显式传入 UTF-8 SRT/VTT，跳过重复 ASR；字幕必须对应当前源片。保留句时间，句内字词时间标为估算。导入失败先修工作副本，不静默改用另一份稿。
- 要自动发现候选：配置用户已提供的 LLM，先运行 `highlights`。模型分数是排序辅助，不是爆款概率。审定后冻结片段与顺序，再通过审阅界面或当前版本支持的导出接口执行；`clip` 会再检测，不能假定它沿用上次候选。
- 已有明确剪辑表：使用当前版本审阅/导出接口，或项目内适配器调用 core，不必为了出片再接 LLM。调用 core 时属于受版本约束的源码集成，不能宣称为官方稳定 CLI 子命令。
- 完整技术问答：以理解所需的长度为准。工具默认短片档位、人脸居中裁切与跳剪不必开启；代码、波形、屏幕演示优先保证可读。

## 环境与调用

先记录所用提交和版本，检查 `package.json`、当前 CLI 帮助与本机已有工具，再安装缺少的依赖。不要为一次试剪默认安装桌面端、下载全部模型、注册 MCP 或启动目录监听。

在仓库根目录，已核对的基础入口为：

```text
pnpm cli doctor
pnpm cli transcribe <video> --subtitles <original.srt> --json
pnpm cli highlights <video> --subtitles <original.srt> --max-clips 3 --json
pnpm cli clip <video> --subtitles <original.srt> --no-vertical --out <new-output> --json
```

后两个入口需要 LLM 配置，前两个不需要。`--no-vertical` 不代表其他自动处理全关闭。执行前按当前源码确认实际开关、时长档位与候选处理方式。上游随时可能变化，不只照抄仓库内置 Skill 的旧示例。

依赖安装策略可能跳过 FFmpeg 等二进制的安装脚本。`pnpm install` 成功后仍应检查实际编码器与中文字体；缺少时可在项目适配中使用已安装的工具，不必修改机器全局设置。不要猜密钥或借用其他应用凭证。

## 哪些数据会外发

“本地运行”需按启用能力解释。本地剪辑与字幕可以不联网；云端文本 LLM 会接收转写与相关提示；启用云端视觉扫描/复评会发送抽帧图片；云端封面、配乐等能力还可能调用额外服务。按实际端点与本次授权选择，不能笼统承诺文字、图片都不出电脑。没有适用端点时仍可用已有字幕与明确剪辑表完成本地导出。

## 导出验收

- 保留当前 `clips.json`、同名字幕、完整 MP4 及源时间映射；若有预裁切，追加预裁切时间到原片时间的对应，不能只记录中间文件。
- 明确启用了什么、回退了什么、哪些能力没有运行。附属文件可能写入失败或缺失，逐一确认本次实际需要的文件存在，不以程序退出码代替交付。
- 查看 `qa` 的具体检测区间。`warn` 是复查入口，`null`/缺失是未取得报告；`pass` 只覆盖已执行的机器检测，不证明语义、隐私、字幕或引流效果通过。
- 静态教学画面、等待回答等可能是合理内容。结合画面和声音决定保留或修改，不机械照搬冻结、停顿、视觉变化频率阈值。
- 自动裁边、响度修复会改变输出。保留原候选，复检字幕与剪辑表是否跟随变化；没有新收益时停止修复。

## 值得复用及不宜照搬的部分

可复用其显式字幕导入、时间来源标注、同源缓存、先写临时文件再替换、每片检测报告和可追踪的修改记录。参考视频的时长、语速、构图可作为偏好，不能冒充因果规律。

不把多版本微扰、变形度评分当作原创性或平台通过依据，不采用规避内容识别的改法。内置风险词、平台规格、所谓法规要求须另查一手来源，不能由工具命中直接下结论。其播放互动反馈只能辅助内容诊断，仍需本项目的有效线索、咨询、报名证据。

## 来源与验证边界

2026-10-27 核对上游 v0.33.0、提交 `ebd0dae5b869276b9afdeb7473dad27eb9431b10`：

- [CLI 与字幕参数](https://github.com/xixihhhh/hotclip/blob/ebd0dae5b869276b9afdeb7473dad27eb9431b10/src/cli/index.ts)
- [字幕导入与估算时间](https://github.com/xixihhhh/hotclip/blob/ebd0dae5b869276b9afdeb7473dad27eb9431b10/src/shared/subtitle-import.ts)
- [本地导出与结果报告](https://github.com/xixihhhh/hotclip/blob/ebd0dae5b869276b9afdeb7473dad27eb9431b10/src/core/export.ts)
- [临时文件保护](https://github.com/xixihhhh/hotclip/blob/ebd0dae5b869276b9afdeb7473dad27eb9431b10/src/core/atomic-output.ts)
- [机器检测](https://github.com/xixihhhh/hotclip/blob/ebd0dae5b869276b9afdeb7473dad27eb9431b10/src/core/qa.ts)与[有限修复](https://github.com/xixihhhh/hotclip/blob/ebd0dae5b869276b9afdeb7473dad27eb9431b10/src/core/repair.ts)
- [视觉调用含图片](https://github.com/xixihhhh/hotclip/blob/ebd0dae5b869276b9afdeb7473dad27eb9431b10/src/core/highlight/vision.ts)

本轮本地验证覆盖显式字幕导入、core 导出、字幕/封面/EDL 生成、机器检测与整片解码；相关上游 5 个测试文件共 74 项通过。未验证全自动 ASR、高光模型、云端视觉、平台发布或转化改善。本参考不附业务素材与本机路径，不复制上游代码。
