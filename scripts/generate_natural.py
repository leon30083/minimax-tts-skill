#!/usr/bin/env python3
"""
使用自然停顿配置生成音频
停顿规则：更短更自然，符合实际说话习惯
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from tts_client import synthesize_text, TTSResult

# 配置
SCENES_FILE = Path(__file__).parent.parent / "guangpan_scenes_natural.yaml"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "guangpan_natural"


def generate_story(voice_id: str = "Chinese (Mandarin)_Warm_Girl", model: str = "speech-2.6-turbo"):
    """生成音频"""
    with open(SCENES_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    scenes = data.get("scenes", [])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("🎵 《光盘行动》绘本音频生成（自然停顿版）")
    print("="*70)
    print(f"\n🎭 音色: {voice_id}")
    print(f"🤖 模型: {model}")
    print(f"📊 场景数: {len(scenes)}")
    print(f"✨ 特点: 停顿减少40-50%，更自然\n")
    
    results = []
    total_chars = 0
    success_count = 0
    
    for i, scene in enumerate(scenes, 1):
        scene_id = scene.get("scene", i)
        original_text = scene.get("original", "")
        processed_text = scene.get("text", "")
        emphasis = scene.get("emphasis", [])
        tone = scene.get("tone", "中性")
        speed = scene.get("speed", 1.0)
        
        print(f"[{i}/{len(scenes)}] 场景 {scene_id} 【{tone}】")
        print(f"   原文: {original_text}")
        if emphasis:
            print(f"   重音: {', '.join(emphasis)}")
        print(f"   语速: ×{speed}")
        
        output_file = f"scene_{scene_id:02d}.mp3"
        output_path = OUTPUT_DIR / output_file
        
        result = synthesize_text(
            text=processed_text,
            voice_id=voice_id,
            output_path=output_path,
            speed=speed
        )
        
        if result.success:
            success_count += 1
            total_chars += result.usage_characters
            print(f"   ✅ 成功 ({result.duration_seconds:.1f}s, {result.file_size_kb:.1f}KB)")
            
            results.append({
                "scene": scene_id,
                "tone": tone,
                "speed": speed,
                "original": original_text,
                "success": True,
                "duration": result.duration_seconds
            })
        else:
            print(f"   ❌ 失败: {result.error}")
            results.append({
                "scene": scene_id,
                "success": False,
                "error": result.error
            })
        
        print()
    
    # 保存报告
    report = {
        "version": "natural",
        "generated_at": datetime.now().isoformat(),
        "voice_id": voice_id,
        "model": model,
        "total_scenes": len(scenes),
        "success_count": success_count,
        "total_chars": total_chars,
        "estimated_cost_cny": (total_chars / 1000) * 0.02 * 7.2,
        "results": results
    }
    
    with open(OUTPUT_DIR / "report.yaml", "w", encoding="utf-8") as f:
        yaml.dump(report, f, allow_unicode=True, default_flow_style=False)
    
    print("="*70)
    print("✨ 生成完成！")
    print("="*70)
    print(f"📊 成功: {success_count}/{len(scenes)}")
    print(f"💰 预估费用: ¥{report['estimated_cost_cny']:.4f}")
    print(f"📁 输出: {OUTPUT_DIR}\n")
    
    print("🎵 音频列表:")
    for r in results:
        if r.get("success"):
            print(f"   场景 {r['scene']:02d} [{r['tone']}]: MEDIA:skills/minimax-tts/outputs/guangpan_natural/scene_{r['scene']:02d}.mp3")


if __name__ == "__main__":
    generate_story()
