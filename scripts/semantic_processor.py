#!/usr/bin/env python3
"""
有声书文本预处理 - 语义分析版
基于有声书演播专业技巧，从语义层面分析停顿和重音

核心原则：
1. 语义停顿 > 标点停顿
2. 主谓之间、动宾之间自然停顿
3. 强调词、转折词前停顿
4. 情感词、形容词重读
5. 讲述感节奏控制
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ProcessedSegment:
    """处理后的文本段"""
    original: str
    processed: str
    pauses: List[Tuple[str, float, str]]  # (位置, 时长, 原因)
    emphasis: List[str]


class SemanticStoryProcessor:
    """语义分析的故事文本处理器"""
    
    def __init__(self):
        """初始化"""
        # 基础停顿规则
        self.base_pauses = {
            "，": 0.3,
            "。": 0.5,
            "！": 0.6,
            "？": 0.7,
            "、": 0.2,
            "：": 0.4,
            "；": 0.4,
        }
        
        # === 语义停顿规则 ===
        
        # 1. 开头引起注意的词（后停顿）
        self.attention_words = {
            "看": 0.5,
            "瞧": 0.5,
            "听": 0.4,
            "哎": 0.4,
            "咦": 0.3,
            "哦": 0.3,
            "哎呀": 0.4,
        }
        
        # 2. 时间词（前停顿，表示时间转换）
        self.time_words = {
            "早春": 0.4,
            "春天": 0.4,
            "夏天": 0.4,
            "秋天": 0.4,
            "冬天": 0.4,
            "很久": 0.4,
            "每天": 0.3,
            "今天": 0.3,
            "现在": 0.3,
            "到了": 0.4,
            "过了": 0.4,
            "一会儿": 0.3,
        }
        
        # 3. 动作词组（主谓分离）
        self.action_patterns = [
            # 主语 + 谓语
            (r"(农民伯伯|小朋友们|我们|你们|他们)(弯下腰|种下|拔草|浇水|吃)", 0.3),
            # 动词 + 宾语
            (r"(种下|变成|滴进|变成)(.+?)(?=<#|，|。|！|？)", 0.2),
        ]
        
        # 4. 并列结构（顿号处理）
        self.list_pause = 0.25
        
        # 5. 转折词（前停顿）
        self.transition_words = {
            "但是": 0.4,
            "可是": 0.4,
            "不过": 0.4,
            "而且": 0.3,
            "然后": 0.3,
            "接着": 0.3,
            "都是": 0.3,
            "就是": 0.3,
        }
        
        # === 重音规则 ===
        
        # 1. 形容词（需要重读）
        self.emphasis_adjectives = [
            # 状态形容词
            "冒热气", "沉甸甸", "亮晶晶", "光溜溜", "金灿灿",
            # 颜色
            "绿色", "金色", "白色", "红色",
            # 程度
            "小小的", "大大的", "满满的",
            # 情感
            "辛苦", "开心", "高兴", "难过",
        ]
        
        # 2. 强调词（需要重读）
        self.emphasis_words = [
            "每一粒", "全部", "所有", "最好", "真", "非常", "特别",
            "就是", "都是", "才",
        ]
        
        # 3. 动作动词（需要重读）
        self.emphasis_verbs = [
            "弯下腰", "种下", "滴进", "吃光", "拔草", "浇水",
        ]
        
        # 4. 情感词（需要重读）
        self.emphasis_emotion = [
            "感谢", "礼物", "辛苦", "香", "甜", "美",
            "明星", "宝贝", "孩子",
        ]
    
    def process_scene(self, text: str, context: Optional[Dict] = None) -> ProcessedSegment:
        """
        处理单个场景，基于语义分析
        
        Args:
            text: 原始文本
            context: 上下文信息（可选）
        
        Returns:
            ProcessedSegment 对象
        """
        pauses = []
        emphasis = []
        processed = text
        
        # === 第一步：基础标点处理 ===
        for punct, duration in self.base_pauses.items():
            if punct in processed:
                processed = processed.replace(punct, f"<#{duration:.1f}#>")
        
        # === 第二步：语义停顿处理 ===
        
        # 2.1 开头引起注意的词
        for word, duration in self.attention_words.items():
            if processed.startswith(word):
                processed = word + f"<#{duration:.1f}#>" + processed[len(word):]
                pauses.append((word, duration, "引起注意"))
                break
        
        # 2.2 时间词（句首或分句首）
        for word, duration in self.time_words.items():
            # 句首时间词
            if processed.startswith(word):
                # 已经在上面处理过开头的词，跳过
                continue
            # 分句中的时间词（前面有停顿标记）
            pattern = f"(?<#{duration:.1f}#>){word}"
            if word in processed and f"<#" in processed[:processed.find(word)]:
                idx = processed.find(word)
                if idx > 0 and processed[idx-1] == ">":
                    processed = processed[:idx] + f"<#{duration:.1f}#>" + processed[idx:]
                    pauses.append((word, duration, "时间转换"))
        
        # 2.3 转折词和连接词
        for word, duration in self.transition_words.items():
            if word in processed:
                # 找到词的位置，在其前面插入停顿
                idx = processed.find(word)
                if idx > 0 and processed[idx-1] != "<":
                    processed = processed[:idx] + f"<#{duration:.1f}#>" + processed[idx:]
                    pauses.append((word, duration, "语义转折"))
        
        # 2.4 "的"字结构（主谓分离）
        # 例："小碗的碗底" -> 在"的"前加微停顿
        if "的" in processed:
            # 只在长修饰语时加停顿
            matches = re.finditer(r"(.{2,})的(.+?)(?=<#|，|。|！|？)", processed)
            for match in matches:
                modifier = match.group(1)
                if len(modifier) >= 2:
                    idx = processed.find(match.group(0))
                    if idx >= 0:
                        de_idx = processed.find("的", idx)
                        if de_idx > 0:
                            processed = processed[:de_idx] + f"<#0.15#>" + processed[de_idx:]
                            pauses.append(("的", 0.15, "修饰语分离"))
                            break
        
        # 2.5 并列结构（顿号已经处理，这里加强）
        if "、" in text:
            pauses.append(("顿号", self.list_pause, "并列成分"))
        
        # === 第三步：重音识别 ===
        
        # 3.1 形容词重音
        for adj in self.emphasis_adjectives:
            if adj in text:
                emphasis.append(adj)
        
        # 3.2 强调词重音
        for word in self.emphasis_words:
            if word in text:
                emphasis.append(word)
        
        # 3.3 动作动词重音
        for verb in self.emphasis_verbs:
            if verb in text:
                emphasis.append(verb)
        
        # 3.4 情感词重音
        for word in self.emphasis_emotion:
            if word in text:
                emphasis.append(word)
        
        # 去重
        emphasis = list(dict.fromkeys(emphasis))
        
        return ProcessedSegment(
            original=text,
            processed=processed,
            pauses=pauses,
            emphasis=emphasis
        )
    
    def analyze_sentence_structure(self, text: str) -> Dict:
        """
        分析句子结构，返回语法成分
        
        Args:
            text: 文本
        
        Returns:
            结构分析结果
        """
        structure = {
            "type": "陈述句",  # 句子类型
            "subject": [],     # 主语
            "predicate": [],   # 谓语
            "object": [],      # 宾语
            "modifiers": [],   # 修饰语
        }
        
        # 简单的句型判断
        if "？" in text or "吗" in text or "怎么" in text:
            structure["type"] = "疑问句"
        elif "！" in text or "呀" in text or "啊" in text:
            structure["type"] = "感叹句"
        
        # 提取主语（简化版）
        subject_patterns = [
            r"^(.+?)(弯下腰|种下|拔草|浇水|吃|变成)",
            r"^(.+?)(是|有|在)",
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, text)
            if match:
                structure["subject"].append(match.group(1))
                break
        
        return structure
    
    def get_emotion_tone(self, text: str) -> Dict:
        """
        分析情感基调
        
        Args:
            text: 文本
        
        Returns:
            情感分析结果
        """
        emotion = {
            "tone": "中性",
            "speed_modifier": 1.0,  # 语速调整
            "energy": "normal",     # 能量级别
        }
        
        # 欢快情感
        happy_words = ["开心", "高兴", "香", "甜", "明星", "亮晶晶"]
        if any(w in text for w in happy_words):
            emotion["tone"] = "欢快"
            emotion["speed_modifier"] = 1.1
            emotion["energy"] = "high"
        
        # 辛苦情感
        hard_words = ["辛苦", "汗水", "烈日", "弯下腰"]
        if any(w in text for w in hard_words):
            emotion["tone"] = "辛苦"
            emotion["speed_modifier"] = 0.9
            emotion["energy"] = "low"
        
        # 感动情感
        moved_words = ["感谢", "礼物", "每一粒"]
        if any(w in text for w in moved_words):
            emotion["tone"] = "感动"
            emotion["speed_modifier"] = 0.95
            emotion["energy"] = "warm"
        
        return emotion


def process_guangpan_scenes():
    """处理《光盘行动》所有场景"""
    processor = SemanticStoryProcessor()
    
    scenes = [
        ("看，你的小碗里盛着冒热气的白米饭。", "引起注意"),
        ("你知道这些小米粒是怎么长大的吗？", "疑问引导"),
        ("早春时节，农民伯伯弯下腰，种下一棵棵小禾苗。", "时间场景"),
        ("烈日当头，汗水滴进了泥土里。", "辛苦场景"),
        ("他们每天都要拔草、浇水，非常辛苦。", "并列动作"),
        ("过了很久，绿色的田野变成了金色的海洋。", "时间转换"),
        ("沉甸甸的稻穗在微风中弯下了腰。", "形象描写"),
        ("每一粒小小的米饭，都是劳动和自然的礼物。", "情感升华"),
        ("到了午饭时间，饭菜的味道闻起来真香呀！", "场景转换"),
        ("让我们用小勺子，把每一粒米饭都吃干净。", "动作引导"),
        ("瞧，小碗的碗底现在变得亮晶晶、光溜溜的！", "成果展示"),
        ("把饭菜全部吃光，就是对农民伯伯最好的感谢。", "情感总结"),
        ("今天，我们都是不剩饭的光盘小明星！", "欢快结尾"),
    ]
    
    print("="*70)
    print("📖 语义分析处理结果")
    print("="*70)
    
    for i, (text, note) in enumerate(scenes, 1):
        result = processor.process_scene(text)
        emotion = processor.get_emotion_tone(text)
        
        print(f"\n【场景 {i}】{note}")
        print(f"原文: {result.original}")
        print(f"处理: {result.processed}")
        print(f"停顿: {[(p[0], f'{p[1]}s', p[2]) for p in result.pauses]}")
        print(f"重音: {result.emphasis}")
        print(f"情感: {emotion['tone']} (语速×{emotion['speed_modifier']})")


if __name__ == "__main__":
    process_guangpan_scenes()
