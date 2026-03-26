#!/usr/bin/env python3
"""
批量生成器
批量生成多个场景的音频
"""

import sys
import yaml
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

# 配置
OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"

# 导入 TTS 客户端
sys.path.insert(0, str(Path(__file__).parent))
from tts_client import MiniMaxTTSClient, TTSConfig, VoiceSetting


class BatchGenerator:
    """批量生成器"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """初始化"""
        self.tts_client = MiniMaxTTSClient(config)
    
    def generate_from_list(
        self,
        scenes: List[Dict[str, str]],
        voice_id: str,
        project_name: str,
        speed: float = 1.0,
        vol: float = 1.0,
        pitch: int = 0,
        model: str = "speech-2.6-turbo"
    ) -> List[Dict]:
        """
        从场景列表批量生成音频
        
        Args:
            scenes: 场景列表 [{"scene": 1, "text": "..."}, ...]
            voice_id: 音色 ID
            project_name: 项目名称
            speed: 语速
            vol: 音量
            pitch: 音调
            model: 模型
        
        Returns:
            生成结果列表
        """
        # 创建输出目录
        output_dir = OUTPUTS_DIR / project_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        total_chars = 0
        success_count = 0
        
        print("="*60)
        print(f"🎵 批量生成音频")
        print("="*60)
        print(f"\n📁 项目: {project_name}")
        print(f"🎭 音色: {voice_id}")
        print(f"📊 场景数: {len(scenes)}")
        print(f"🤖 模型: {model}")
        print()
        
        for i, scene in enumerate(scenes, 1):
            scene_id = scene.get("scene", i)
            text = scene.get("text", "")
            
            if not text:
                continue
            
            print(f"[{i}/{len(scenes)}] 场景 {scene_id}...")
            
            # 生成文件名
            output_file = f"scene_{scene_id:02d}.mp3"
            output_path = output_dir / output_file
            
            # 调用 TTS
            result = self.tts_client.synthesize(
                text=text,
                voice_setting=VoiceSetting(
                    voice_id=voice_id,
                    speed=speed,
                    vol=vol,
                    pitch=pitch
                ),
                output_path=output_path
            )
            
            result_data = {
                "scene": scene_id,
                "text": text,
                "success": result.success,
                "audio_path": str(result.audio_path) if result.audio_path else None,
                "duration_seconds": result.duration_seconds,
                "file_size_kb": result.file_size_kb,
                "usage_characters": result.usage_characters,
                "error": result.error
            }
            
            results.append(result_data)
            
            if result.success:
                success_count += 1
                total_chars += result.usage_characters
                print(f"  ✅ 成功 ({result.duration_seconds:.1f}s, {result.file_size_kb:.1f}KB)")
            else:
                print(f"  ❌ 失败: {result.error}")
        
        # 生成报告
        report = {
            "project_name": project_name,
            "voice_id": voice_id,
            "model": model,
            "total_scenes": len(scenes),
            "success_count": success_count,
            "total_chars": total_chars,
            "generated_at": datetime.now().isoformat(),
            "results": results
        }
        
        # 保存报告
        report_path = output_dir / "generation_report.yaml"
        with open(report_path, "w", encoding="utf-8") as f:
            yaml.dump(report, f, allow_unicode=True, default_flow_style=False)
        
        # 打印总结
        print()
        print("="*60)
        print(f"✨ 生成完成！")
        print("="*60)
        print(f"📊 成功: {success_count}/{len(scenes)}")
        print(f"📝 总字符: {total_chars}")
        print(f"💰 预估费用: ${self._estimate_cost(total_chars, model):.4f} 元")
        print(f"📁 输出目录: {output_dir}")
        print(f"📋 报告: {report_path.name}")
        
        return results
    
    def _estimate_cost(self, chars: int, model: str) -> float:
        """估算费用"""
        # MiniMax 国际站定价（美元）
        # speech-2.6-turbo: ~$0.02 / 1K 字符
        # speech-2.6-hd: ~$0.035 / 1K 字符
        
        if model == "speech-2.6-turbo":
            rate = 0.02  # 美元/1K字符
        elif model == "speech-2.6-hd":
            rate = 0.035
        else:
            rate = 0.02
        
        # 转换为人民币（假设汇率 1:7.2）
        cost_usd = (chars / 1000) * rate
        cost_cny = cost_usd * 7.2
        
        return cost_cny
    
    def generate_from_file(
        self,
        input_file: Path,
        voice_id: str,
        project_name: str,
        **kwargs
    ) -> List[Dict]:
        """
        从文件批量生成音频
        
        Args:
            input_file: 输入文件（支持 .txt, .yaml, .json）
            voice_id: 音色 ID
            project_name: 项目名称
            **kwargs: 其他参数
        
        Returns:
            生成结果列表
        """
        scenes = self._parse_input_file(input_file)
        return self.generate_from_list(scenes, voice_id, project_name, **kwargs)
    
    def _parse_input_file(self, input_file: Path) -> List[Dict[str, str]]:
        """解析输入文件"""
        if not input_file.exists():
            raise FileNotFoundError(f"文件不存在: {input_file}")
        
        suffix = input_file.suffix.lower()
        
        if suffix == ".txt":
            # 纯文本，每行一个场景
            scenes = []
            with open(input_file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        scenes.append({"scene": i, "text": line})
            return scenes
        
        elif suffix in [".yaml", ".yml"]:
            with open(input_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "scenes" in data:
                return data["scenes"]
            else:
                raise ValueError("YAML 文件格式错误")
        
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批量生成音频")
    parser.add_argument("--voice", required=True, help="音色 ID")
    parser.add_argument("--input", required=True, help="输入文件路径")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--model", default="speech-2.6-turbo", help="模型名称")
    parser.add_argument("--speed", type=float, default=1.0, help="语速")
    parser.add_argument("--vol", type=float, default=1.0, help="音量")
    parser.add_argument("--pitch", type=int, default=0, help="音调")
    
    args = parser.parse_args()
    
    generator = BatchGenerator()
    
    generator.generate_from_file(
        input_file=Path(args.input),
        voice_id=args.voice,
        project_name=args.project,
        speed=args.speed,
        vol=args.vol,
        pitch=args.pitch,
        model=args.model
    )


if __name__ == "__main__":
    main()
