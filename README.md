# MiniMax TTS Skill

专业的 TTS 语音合成工具，专为有声书、儿童绘本、视频旁白设计。

## 特性

- 🎯 **智能音色推荐** - 根据内容自动推荐最合适的音色
- 🎵 **样音缓存** - 本地缓存样音，避免重复生成
- 📖 **语义分析** - 基于有声书演播规则，智能添加停顿
- 🎭 **情感语速** - 辛苦场景×0.92，欢快场景×1.05
- 📦 **批量生成** - 支持多场景批量生成音频
- 💰 **费用透明** - 实时估算费用

## 安装

```bash
# 克隆仓库
git clone https://github.com/leonluo2008-ops/minimax-tts-skill.git
cd minimax-tts-skill

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env 文件，填入你的 MiniMax API Key
```

## 快速开始

### 1. 推荐音色

```bash
python scripts/voice_selector.py "你的旁白内容"
```

输出：
- 内容分析（类型、受众、情感）
- 推荐音色列表（带样音路径）
- 推荐理由

### 2. 生成样音

```bash
# 查看已有样音
python scripts/preview_manager.py list

# 生成缺失的样音
python scripts/preview_manager.py generate --missing
```

### 3. 批量生成音频

准备场景文件 `scenes.yaml`:

```yaml
scenes:
  - scene: 1
    text: "看，你的小碗里盛着冒热气的白米饭。"
    tone: "中性"
    speed: 1.0
```

运行生成：

```bash
python scripts/batch_generator.py \
  --voice "Chinese (Mandarin)_Warm_Girl" \
  --input scenes.yaml \
  --output ./outputs/my_story
```

## 停顿规则

基于有声书演播专业规则：

| 标点/语义 | 推荐停顿 | 说明 |
|----------|---------|------|
| 逗号 | 0.15秒 | 自然呼吸 |
| 句号 | 0.25秒 | 句子结束 |
| 问号 | 0.35秒 | 问句停顿 |
| 感叹号 | 0.30秒 | 情感表达 |
| 顿号 | 0.12秒 | 并列成分 |
| 语义停顿 | 0.1-0.2秒 | 主谓分离、时间转换 |

### 使用停顿标记

```yaml
text: "看<#0.2#><#0.15#>你的小碗里盛着冒热气的白米饭<#0.25#>"
```

## 音色库

### 推荐中文音色

| 音色 | 特点 | 适用场景 |
|------|------|----------|
| 温暖女声 | 温暖亲切、治愈 | 儿童故事、绘本旁白 |
| 可爱精灵 | 可爱俏皮、活泼 | 童话故事、动画配音 |
| 甜美女声 | 甜美动人、温柔 | 儿童故事、情感内容 |
| 温和青年 | 温和亲切、友好 | 儿童故事、科普视频 |

## 实战案例

### 《光盘行动》绘本

- **场景数**：13
- **音色**：温暖女声
- **总时长**：~58秒
- **费用**：¥0.10
- **效果评分**：88/100

完整案例见 `examples/guangpan/`

## 定价

MiniMax 国际站 TTS 定价：

| 模型 | 单价 |
|------|------|
| speech-2.6-turbo | ~$0.02 / 1K 字符 |
| speech-2.6-hd | ~$0.035 / 1K 字符 |

## 文件结构

```
minimax-tts-skill/
├── SKILL.md                    # OpenClaw Skill 文档
├── README.md                   # 本文档
├── .env.example               # 配置模板
├── requirements.txt           # Python 依赖
├── assets/
│   ├── voices.yaml            # 音色库定义
│   └── voice_previews.yaml    # 样音索引
├── previews/                   # 样音缓存
├── scripts/
│   ├── tts_client.py          # TTS 核心客户端
│   ├── voice_selector.py      # 音色推荐引擎
│   ├── semantic_processor.py  # 语义分析处理器
│   ├── preview_manager.py     # 样音管理
│   └── batch_generator.py     # 批量生成器
└── examples/                   # 实战案例
    └── guangpan/
```

## 开发

```bash
# 运行测试
python -m pytest tests/

# 代码格式化
black scripts/
```

## License

MIT

## 致谢

- [MiniMax](https://minimax.io) - TTS API
- 有声书演播专业规则

---

Made with ❤️ by [leonluo2008-ops](https://github.com/leonluo2008-ops)
