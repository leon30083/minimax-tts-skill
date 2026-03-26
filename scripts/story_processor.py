#!/usr/bin/env python3
"""
故事文本预处理
为儿童故事添加停顿和重音，增强讲述感
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ProcessedText:
    """处理后的文本"""
    original: str
    processed: str
    pauses: List[Tuple[str, float]]  # (位置, 停顿时长)
    emphasis: List[str]  # 重音词


class StoryTextProcessor:
    """故事文本处理器"""
    
    def __init__(self):
        """初始化"""
        # 停顿规则（秒）
        self.pause_rules = {
            "，": 0.4,      # 逗号
            "。": 0.6,      # 句号
            "！": 0.7,      # 感叹号
            "？": 0.8,      # 问号
            "、": 0.3,      # 顿号
            "：": 0.5,      # 冒号
            "；": 0.5,      # 分号
        }
        
        # 特殊词停顿（开头词、语气词等）
        self.special_pauses = {
            "看": 0.6,      # "看，"开头
            "瞧": 0.6,      # "瞧，"开头
            "听": 0.5,      # "听，"开头
            "啊": 0.3,      # 语气词
            "呀": 0.3,      # 语气词
            "呢": 0.3,      # 语气词
            "哦": 0.3,      # 语气词
        }
        
        # 需要重音的词类型
        self.emphasis_patterns = [
            # 形容词（颜色、状态）
            r"(冒热气|金色的|绿色的|亮晶晶|光溜溜|沉甸甸|小小的|美丽的|可爱的)",
            # 强调词
            r"(每一粒|全部|最好|真|非常)",
            # 动作动词
            r"(弯下腰|滴进|吃光|种下)",
            # 时间词
            r"(早春|很久|每天|今天)",
        ]
    
    def process_scene(self, text: str) -> ProcessedText:
        """
        处理单个场景文本
        
        Args:
            text: 原始文本
        
        Returns:
            ProcessedText 对象
        """
        pauses = []
        emphasis_words = []
        processed = text
        
        # 1. 处理标点停顿
        for punct, duration in self.pause_rules.items():
            if punct in processed:
                # 替换为停顿标记
                processed = processed.replace(punct, f"<#{duration:.1f}#>")
                pauses.append((punct, duration))
        
        # 2. 处理特殊词停顿（开头词）
        for word, duration in self.special_pauses.items():
            if processed.startswith(word):
                # 在开头词后添加停顿
                processed = word + f"<#{duration:.1f}#>" + processed[len(word):]
                pauses.append((word, duration))
        
        # 3. 识别重音词
        for pattern in self.emphasis_patterns:
            matches = re.findall(pattern, text)
            emphasis_words.extend(matches)
        
        # 4. 处理引号内的内容（对话）
        if "“" in processed and "”" in processed:
            # 引号内容前后添加停顿
            processed = processed.replace("“", "<#0.3#>“")
            processed = processed.replace("”", "”<#0.3#>")
        
        return ProcessedText(
            original=text,
            processed=processed,
            pauses=pauses,
            emphasis=list(set(emphasis_words))
        )
    
    def process_story(self, scenes: List[Dict]) -> List[Dict]:
        """
        处理完整故事
        
        Args:
            scenes: 场景列表 [{"scene": 1, "text": "..."}, ...]
        
        Returns:
            处理后的场景列表
        """
        processed_scenes = []
        
        for scene in scenes:
            text = scene.get("text", "")
            result = self.process_scene(text)
            
            processed_scenes.append({
                "scene": scene.get("scene"),
                "original_text": result.original,
                "processed_text": result.processed,
                "pauses": result.pauses,
                "emphasis": result.emphasis
            })
        
        return processed_scenes


def format_for_tts(text: str) -> str:
    """
    格式化文本用于 TTS
    
    Args:
        text: 原始文本
    
    Returns:
        格式化后的文本（带停顿标记）
    """
    processor = StoryTextProcessor()
    result = processor.process_scene(text)
    return result.processed


def demo_processing():
    """演示文本处理"""
    processor = StoryTextProcessor()
    
    # 测试场景
    test_scenes = [
        "看，你的小碗里盛着冒热气的白米饭。",
        "你知道这些小米粒是怎么长大的吗？",
        "瞧，小碗的碗底现在变得亮晶晶、光溜溜的！",
    ]
    
    print("="*60)
    print("📖 故事文本处理演示")
    print("="*60)
    
    for text in test_scenes:
        result = processor.process_scene(text)
        
        print(f"\n📝 原文: {result.original}")
        print(f"🎵 处理后: {result.processed}")
        print(f"⏸️ 停顿: {result.pauses}")
        print(f"🔊 重音: {result.emphasis}")


if __name__ == "__main__":
    demo_processing()
