#!/usr/bin/env python3
"""
样音管理器
管理样音的生成、缓存和查询
"""

import sys
import yaml
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

# 配置
PREVIEWS_DIR = Path(__file__).parent.parent / "previews"
PREVIEWS_YAML = Path(__file__).parent.parent / "assets" / "voice_previews.yaml"
VOICES_YAML = Path(__file__).parent.parent / "assets" / "voices.yaml"

# 导入 TTS 客户端
sys.path.insert(0, str(Path(__file__).parent))
from tts_client import MiniMaxTTSClient, TTSConfig, VoiceSetting

# 默认试听文本
DEFAULT_PREVIEW_TEXT = "你好，这是我的声音试听。欢迎来到儿童故事时间！"


class PreviewManager:
    """样音管理器"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """初始化"""
        self.tts_client = MiniMaxTTSClient(config)
        self.voices = self._load_voices()
        self.previews = self._load_previews()
    
    def _load_voices(self) -> Dict:
        """加载音色库"""
        if not VOICES_YAML.exists():
            return {}
        
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
    
    def _save_previews(self, previews: Dict):
        """保存样音索引"""
        data = {
            "version": 1.0,
            "generated_at": datetime.now().isoformat(),
            "previews": previews,
            "missing_previews": self._get_missing_voice_ids(previews)
        }
        
        with open(PREVIEWS_YAML, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    
    def _get_missing_voice_ids(self, previews: Dict) -> List[str]:
        """获取缺失的音色 ID"""
        return [
            vid for vid in self.voices.keys()
            if vid not in previews
        ]
    
    def list_previews(self) -> List[Dict]:
        """
        列出所有样音
        
        Returns:
            样音列表
        """
        result = []
        
        for voice_id, voice_data in self.voices.items():
            preview_info = self.previews.get(voice_id, {})
            preview_file = preview_info.get("preview_file")
            preview_path = PREVIEWS_DIR / preview_file if preview_file else None
            
            result.append({
                "voice_id": voice_id,
                "voice_name": voice_data.get("name", ""),
                "has_preview": preview_path.exists() if preview_path else False,
                "preview_path": preview_path if preview_path and preview_path.exists() else None,
                "preview_info": preview_info if preview_info else None
            })
        
        return result
    
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
    
    def generate_preview(self, voice_id: str, text: str = DEFAULT_PREVIEW_TEXT) -> Optional[Path]:
        """
        生成样音
        
        Args:
            voice_id: 音色 ID
            text: 试听文本
        
        Returns:
            样音路径或 None
        """
        if voice_id not in self.voices:
            print(f"❌ 音色不存在: {voice_id}")
            return None
        
        voice_data = self.voices[voice_id]
        voice_name = voice_data.get("name", "")
        
        print(f"🎵 生成样音: {voice_name}...")
        
        # 生成文件名
        preview_file = f"preview_{voice_name}.mp3"
        output_path = PREVIEWS_DIR / preview_file
        
        # 调用 TTS
        result = self.tts_client.synthesize(
            text=text,
            voice_setting=VoiceSetting(voice_id=voice_id),
            output_path=output_path
        )
        
        if result.success:
            # 更新索引
            self.previews[voice_id] = {
                "voice_name": voice_name,
                "preview_file": preview_file,
                "preview_text": text,
                "generated_at": datetime.now().isoformat(),
                "file_size_kb": result.file_size_kb,
                "duration_seconds": result.duration_seconds
            }
            self._save_previews(self.previews)
            
            print(f"✅ 生成成功: {output_path.name}")
            return output_path
        else:
            print(f"❌ 生成失败: {result.error}")
            return None
    
    def generate_missing_previews(self) -> List[Path]:
        """
        生成缺失的样音
        
        Returns:
            生成的样音路径列表
        """
        missing = self._get_missing_voice_ids(self.previews)
        
        if not missing:
            print("✅ 所有样音都已生成")
            return []
        
        print(f"\n📋 待生成样音: {len(missing)} 个")
        
        results = []
        for voice_id in missing:
            result = self.generate_preview(voice_id)
            if result:
                results.append(result)
        
        return results
    
    def generate_all_previews(self) -> List[Path]:
        """
        重新生成所有样音
        
        Returns:
            生成的样音路径列表
        """
        print(f"\n📋 重新生成所有样音: {len(self.voices)} 个")
        
        results = []
        for voice_id in self.voices.keys():
            result = self.generate_preview(voice_id)
            if result:
                results.append(result)
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="样音管理器")
    parser.add_argument("action", choices=["list", "generate"], help="操作类型")
    parser.add_argument("--missing", action="store_true", help="只生成缺失的样音")
    parser.add_argument("--all", action="store_true", help="重新生成所有样音")
    parser.add_argument("--voice-id", help="生成指定音色的样音")
    
    args = parser.parse_args()
    
    manager = PreviewManager()
    
    if args.action == "list":
        print("\n📋 样音列表:")
        print("-"*60)
        
        previews = manager.list_previews()
        
        has_preview_count = sum(1 for p in previews if p["has_preview"])
        
        for p in previews:
            status = "✅" if p["has_preview"] else "❌"
            print(f"\n{status} {p['voice_name']}")
            print(f"   ID: {p['voice_id']}")
            if p["has_preview"]:
                print(f"   样音: MEDIA:skills/minimax-tts/previews/{p['preview_path'].name}")
        
        print(f"\n📊 统计: {has_preview_count}/{len(previews)} 已生成")
    
    elif args.action == "generate":
        if args.voice_id:
            manager.generate_preview(args.voice_id)
        elif args.all:
            manager.generate_all_previews()
        elif args.missing:
            manager.generate_missing_previews()
        else:
            print("请指定 --missing、--all 或 --voice-id")


if __name__ == "__main__":
    main()
