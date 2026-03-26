#!/usr/bin/env python3
"""
重新生成失败的场景
"""

import sys
import time
sys.path.insert(0, str(Path(__file__).parent))
from pathlib import Path
from tts_client import synthesize_text

OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "guangpan_natural"

# 失败的场景
scenes = [
    (4, "烈日<#0.1#>当头<#0.15#>汗水<#0.1#>滴进了泥土里<#0.25#>", 0.92),
    (6, "过了很久<#0.2#>绿色的田野<#0.15#>变成了金色的海洋<#0.25#>", 1.0),
    (8, "每一粒<#0.1#>小小的米饭<#0.15#><#0.15#>都是劳动和自然的礼物<#0.25#>", 0.95),
    (9, "到了午饭时间<#0.2#>饭菜的味道<#0.1#>闻起来<#0.1#>真香呀<#0.3#>", 1.05),
    (10, "让我们用小勺子<#0.15#>把每一粒米饭都吃干净<#0.25#>", 1.0),
    (11, "瞧<#0.2#><#0.15#>小碗的碗底<#0.1#>现在变得<#0.1#>亮晶晶<#0.12#>光溜溜的<#0.3#>", 1.05),
]

print("="*50)
print("🔄 重新生成失败的场景")
print("="*50)

for scene_id, text, speed in scenes:
    print(f"\n场景 {scene_id}: ", end="")
    
    output_path = OUTPUT_DIR / f"scene_{scene_id:02d}.mp3"
    
    result = synthesize_text(
        text=text,
        voice_id="Chinese (Mandarin)_Warm_Girl",
        output_path=output_path,
        speed=speed
    )
    
    if result.success:
        print(f"✅ 成功 ({result.duration_seconds:.1f}s)")
    else:
        print(f"❌ 失败: {result.error}")
    
    time.sleep(1)

print("\n" + "="*50)
print("✨ 完成！")
print("="*50)
