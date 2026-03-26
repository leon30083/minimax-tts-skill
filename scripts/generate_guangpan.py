#!/usr/bin/env python3
"""
为《光盘行动》绘本生成音频
使用带停顿标记的文本，增强讲述感
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from tts_client import MiniMaxTTSClient, VoiceSetting

# 配置
SCENES_FILE = Path(__file__).parent.parent / "guangpan_scenes_processed.yaml"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "guangpan_story"


def generate_story(voice_id: str = "Chinese (Mandarin)_Warm_Girl", model: str = "speech-2.6-turbo"):
    """生成《光盘行动》绘本音频"""
    # 加载场景
    with open(SCENES_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    scenes = data.get("scenes", [])
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 初始化客户端
    client = MiniMaxTTSClient()
    
    print("="*60)
    print("🎵 《光盘行动》绘本音频生成")
    print("="*60)
    print(f"\n🎭 音色: {voice_id}")
    print(f"🤖 模型: {model}")
    print(f"📊 场景数: {len(scenes)}")
    print()
    
    results = []
    total_chars = 0
    success_count = 0
    
    for i, scene in enumerate(scenes, 1):
        scene_id = scene.get("scene", i)
        original_text = scene.get("original", "")
        processed_text = scene.get("text", "")
        emphasis = scene.get("emphasis", [])
        note = scene.get("note", "")
        
        print(f"[{i}/{len(scenes)}] 场景 {scene_id}")
        print(f"   原文: {original_text}")
        if emphasis:
            print(f"   重音: {', '.join(emphasis)}")
        if note:
            print(f"   说明: {note}")
        
        # 生成文件名
        output_file = f"scene_{scene_id:02d}.mp3"
        output_path = OUTPUT_DIR / output_file
        
        # 调用 TTS
        result = client.synthesize(
            text=processed_text,
            voice_setting=VoiceSetting(
                voice_id=voice_id,
                speed=1.0,
                vol=1.0,
                pitch=0
            ),
            output_path=output_path,
            model=model
        )
        
        if result.success:
            success_count += 1
            total_chars += result.usage_characters
            print(f"   ✅ 成功 ({result.duration_seconds:.1f}s, {result.file_size_kb:.1f}KB)")
            
            results.append({
                "scene": scene_id,
                "original_text": original_text,
                "processed_text": processed_text,
                "success": True,
                "audio_path": str(output_path),
                "duration_seconds": result.duration_seconds,
                "file_size_kb": result.file_size_kb
            })
        else:
            print(f"   ❌ 失败: {result.error}")
            results.append({
                "scene": scene_id,
                "original_text": original_text,
                "success": False,
                "error": result.error
            })
        
        print()
    
    # 保存报告
    report = {
        "project": "光盘行动绘本",
        "voice_id": voice_id,
        "model": model,
        "generated_at": datetime.now().isoformat(),
        "total_scenes": len(scenes),
        "success_count": success_count,
        "total_chars": total_chars,
        "estimated_cost_cny": (total_chars / 1000) * 0.02 * 7.2,
        "results": results
    }
    
    report_path = OUTPUT_DIR / "generation_report.yaml"
    with open(report_path, "w", encoding="utf-8") as f:
        yaml.dump(report, f, allow_unicode=True, default_flow_style=False)
    
    # 打印总结
    print("="*60)
    print("✨ 生成完成！")
    print("="*60)
    print(f"📊 成功: {success_count}/{len(scenes)}")
    print(f"📝 总字符: {total_chars}")
    print(f"💰 预估费用: ¥{report['estimated_cost_cny']:.4f}")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print()
    
    # 输出音频路径列表
    print("🎵 音频文件列表:")
    print("-"*60)
    for r in results:
        if r.get("success"):
            path = Path(r["audio_path"])
            print(f"场景 {r['scene']:02d}: MEDIA:skills/minimax-tts/outputs/guangpan_story/{path.name}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成光盘行动绘本音频")
    parser.add_argument("--voice", default="Chinese (Mandarin)_Warm_Girl", help="音色 ID")
    parser.add_argument("--model", default="speech-2.6-turbo", help="模型名称")
    
    args = parser.parse_args()
    
    generate_story(voice_id=args.voice, model=args.model)
