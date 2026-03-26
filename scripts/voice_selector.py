#!/usr/bin/env python3
"""
音色推荐引擎
根据内容特征推荐最合适的音色
"""

import sys
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

# 配置
VOICES_YAML = Path(__file__).parent.parent / "assets" / "voices.yaml"
PREVIEWS_YAML = Path(__file__).parent.parent / "assets" / "voice_previews.yaml"
PREVIEWS_DIR = Path(__file__).parent.parent / "previews"


@dataclass
class ContentAnalysis:
    """内容分析结果"""
    content_type: str  # 内容类型
    target_audience: str  # 目标受众
    emotion: str  # 情感基调
    keywords: List[str]  # 关键词
    style: List[str]  # 风格标签


@dataclass
class VoiceRecommendation:
    """音色推荐"""
    voice_id: str
    voice_name: str
    score: int
    reasons: List[str]
    preview_path: Optional[Path] = None
    has_preview: bool = False


class VoiceSelector:
    """音色选择器"""
    
    def __init__(self):
        """初始化"""
        self.voices = self._load_voices()
        self.previews = self._load_previews()
    
    def _load_voices(self) -> Dict:
        """加载音色库"""
        if not VOICES_YAML.exists():
                raise FileNotFoundError(f"音色库文件不存在: {VOICES_YAML}")
        
        with open(VOICES_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        return {v["id"]: v for v in data.get("voices", [])}
    
    def _load_previews(self) -> Dict:
        """加载样音索引"""
        if not PREVIEWS_YAML.exists():
                return {}
        
        with open(PREVIEWS_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        return data.get("previews", {})
    
    def analyze_content(self, content: str) -> ContentAnalysis:
        """
        分析内容特征
        
        Args:
            content: 文本内容
        
        Returns:
            ContentAnalysis 对象
        """
        # 内容类型检测
        content_type = "通用"
        type_keywords = {
            "儿童故事": ["从前", "很久以前", "公主", "王子", "小动物", "童话", "魔法", "森林", "小朋友", "宝贝", "儿童", "孩子"],
            "新闻播报": ["今日", "据报道", "消息", "新闻", "发布会", "声明", "宣布"],
            "企业宣传": ["公司", "企业", "产品", "服务", "团队", "创新", "发展", "战略"],
            "情感故事": ["爱情", "思念", "回忆", "感动", "温暖", "幸福", "遗憾"],
            "科普教育": ["原理", "知识", "学习", "了解", "科学", "研究", "发现"],
            "纪录片": ["历史", "文化", "传承", "岁月", "时代", "变迁"],
        }
        
        for ctype, keywords in type_keywords.items():
            if any(kw in content for kw in keywords):
                content_type = ctype
                break
        
        # 目标受众检测
        target_audience = "成人"
        if any(kw in content for kw in ["小朋友", "宝贝", "儿童", "宝宝", "孩子", "小动物"]):
            target_audience = "儿童"
        elif any(kw in content for kw in ["年轻人", "青春", "校园"]):
            target_audience = "青年"
        
        # 情感基调检测
        emotion = "中性"
        if any(kw in content for kw in ["开心", "快乐", "欢笑", "幸福", "美好", "可爱"]):
            emotion = "欢快"
        elif any(kw in content for kw in ["悲伤", "难过", "遗憾", "思念", "泪水"]):
            emotion = "悲伤"
        elif any(kw in content for kw in ["激动", "兴奋", "热血", "奋斗"]):
            emotion = "激情"
        elif any(kw in content for kw in ["温柔", "温暖", "柔和", "安静", "宁静"]):
            emotion = "温柔"
        
        # 提取关键词
        keywords = []
        for word in content:
            if len(word) >= 2 and word not in ["的", "了", "是", "在", "有", "和"]:
                keywords.append(word)
        
        return ContentAnalysis(
            content_type=content_type,
            target_audience=target_audience,
            emotion=emotion,
            keywords=list(set(keywords))[:10],
            style=[]
        )
    
    def recommend_voices(self, content: str, top_n: int = 5) -> List[VoiceRecommendation]:
        """
        推荐音色
        
        Args:
            content: 文本内容
            top_n: 返回前 N 个推荐
        
        Returns:
            推荐音色列表
        """
        analysis = self.analyze_content(content)
        
        recommendations = []
        
        for voice_id, voice_data in self.voices.items():
            score = 0
            reasons = []
            
            voice = voice_data
            tags = voice.get("tags", [])
            scenes = voice.get("scenes", [])
            
            # 1. 内容类型匹配
            if analysis.content_type in scenes:
                score += 30
                reasons.append(f"适合「{analysis.content_type}」场景")
            
            # 2. 目标受众匹配
            if analysis.target_audience == "儿童":
                if "儿童故事" in scenes or "童话故事" in scenes or "绘本旁白" in scenes:
                    score += 25
                    reasons.append("适合儿童内容")
                if voice.get("gender") == "female" and voice.get("age") == "young":
                    score += 10
            elif analysis.target_audience == "青年":
                if voice.get("age") == "young":
                    score += 15
                    reasons.append("声音年轻有活力")
            
            # 3. 情感基调匹配
            if analysis.emotion == "欢快":
                if any(tag in tags for tag in ["活泼", "活力", "阳光", "俏皮"]):
                    score += 20
                    reasons.append("声音活泼欢快")
            elif analysis.emotion == "温柔":
                if any(tag in tags for tag in ["温柔", "温和", "柔和", "甜美"]):
                    score += 20
                    reasons.append("声音温柔细腻")
            elif analysis.emotion == "悲伤":
                if any(tag in tags for tag in ["抒情", "情感", "温柔"]):
                    score += 15
                    reasons.append("声音富有情感")
            elif analysis.emotion == "激情":
                if any(tag in tags for tag in ["活力", "阳光", "专业"]):
                    score += 15
                    reasons.append("声音有感染力")
            
            # 4. 质量评分
            score += voice.get("quality_score", 0)
            
            if score > 0:
                # 检查样音
                preview_info = self.previews.get(voice_id, {})
                preview_file = preview_info.get("preview_file") if preview_info else None
                preview_path = PREVIEWS_DIR / preview_file if preview_file else None
                
                has_preview = preview_path.exists() if preview_path else False
                
                recommendations.append(VoiceRecommendation(
                    voice_id=voice_id,
                    voice_name=voice.get("name", ""),
                    score=score,
                    reasons=reasons,
                    preview_path=preview_path if has_preview else None,
                    has_preview=has_preview
                ))
        
        # 按分数排序
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return recommendations[:top_n]
    
    def get_preview(self, voice_id: str) -> Optional[Path]:
        """
        获取样音路径
        
        Args:
            voice_id: 音色 ID
        
        Returns:
            样音路径或 None
        """
        preview_info = self.previews.get(voice_id, {})
        preview_file = preview_info.get("preview_file")
        
        if preview_file:
            preview_path = PREVIEWS_DIR / preview_file
            if preview_path.exists():
                return preview_path
        
        return None


def main():
    """主函数"""
    if len(sys.argv) > 1:
        content = " ".join(sys.argv[1:])
        
        selector = VoiceSelector()
        
        print("="*60)
        print("🎙️ MiniMax 音色推荐")
        print("="*60)
        print()
        print(f"📝 内容分析中...")
        
        analysis = selector.analyze_content(content)
        
        print(f"\n📊 分析结果:")
        print(f"   - 内容类型: {analysis.content_type}")
        print(f"   - 目标受众: {analysis.target_audience}")
        print(f"   - 情感基调: {analysis.emotion}")
        
        print(f"\n🎯 推荐音色:")
        
        recommendations = selector.recommend_voices(content, top_n=5)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. 【{rec.voice_name}】 ⭐ 推荐指数: {rec.score}")
            print(f"   推荐理由: {'、'.join(rec.reasons)}")
            print(f"   ID: {rec.voice_id}")
            if rec.has_preview:
                print(f"   🎵 样音: MEDIA:skills/minimax-tts/previews/{rec.preview_path.name}")
            else:
                print(f"   ⚠️ 暂无样音")
    else:
        print("用法: python voice_selector.py <内容文本>")
        print("\n示例:")
        print('  python voice_selector.py "从前有一只可爱的小兔子"')


if __name__ == "__main__":
    main()
