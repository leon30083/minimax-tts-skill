#!/usr/bin/env python3
"""
MiniMax TTS 客户端
"""

import requests
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import yaml
import json

@dataclass
class TTSConfig:
    """TTS 配置"""
    api_key: str
    base_url: str = "https://api.minimax.io"
    model: str = "speech-2.6-turbo"
    sample_rate: int = 32000
    bitrate: int = 128000
    format: str = "mp3"
    channel: int = 1

@dataclass
class VoiceSetting:
    """音色设置"""
    voice_id: str
    speed: float = 1.0
    vol: float = 1.0
    pitch: int = 0  # 必须是整数

@dataclass
class TTSResult:
    """TTS 结果"""
    success: bool
    audio_path: Optional[Path] = None
    audio_hex: Optional[str] = None
    duration_seconds: float = 0.0
    file_size_kb: float = 0.0
    usage_characters: int = 0
    error: Optional[str] = None


class MiniMaxTTSClient:
    """MiniMax TTS 客户端"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """初始化客户端"""
        if config is None:
            config = self._load_config_from_env()
        self.config = config
    
    def _load_config_from_env(self) -> TTSConfig:
        """从环境变量加载配置"""
        # 尝试从 .env 文件加载
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
        
        return TTSConfig(
            api_key=os.getenv("MINIMAX_API_KEY", ""),
            base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io"),
            model=os.getenv("DEFAULT_MODEL", "speech-2.6-turbo"),
            sample_rate=int(os.getenv("DEFAULT_SAMPLE_RATE", "32000")),
            bitrate=int(os.getenv("DEFAULT_BITRATE", "128000")),
            format=os.getenv("DEFAULT_FORMAT", "mp3"),
            channel=int(os.getenv("DEFAULT_CHANNEL", "1"))
        )
    
    def synthesize(
        self,
        text: str,
        voice_setting: VoiceSetting,
        output_path: Optional[Path] = None,
        model: Optional[str] = None
    ) -> TTSResult:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            voice_setting: 音色设置
            output_path: 输出路径（可选）
            model: 模型名称（可选）
        
        Returns:
            TTSResult 对象
        """
        url = f"{self.config.base_url}/v1/t2a_v2"
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.config.model,
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_setting.voice_id,
                "speed": voice_setting.speed,
                "vol": voice_setting.vol,
                "pitch": voice_setting.pitch  # 必须是整数
            },
            "audio_setting": {
                "sample_rate": self.config.sample_rate,
                "bitrate": self.config.bitrate,
                "format": self.config.format,
                "channel": self.config.channel
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                return TTSResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
            
            result = response.json()
            
            # 检查 API 错误
            if "base_resp" in result:
                status_code = result.get("base_resp", {}).get("status_code", 0)
                if status_code != 0:
                    return TTSResult(
                        success=False,
                        error=result.get("base_resp", {}).get("status_msg", "Unknown error")
                    )
            
            # 提取音频数据
            if "data" not in result or "audio" not in result.get("data", {}):
                return TTSResult(
                    success=False,
                    error="No audio data in response"
                )
            
            audio_hex = result["data"]["audio"]
            audio_bytes = bytes.fromhex(audio_hex)
            
            # 获取额外信息
            extra_info = result.get("extra_info", {})
            duration_ms = extra_info.get("audio_length", 0)
            file_size = extra_info.get("audio_size", 0)
            usage_chars = extra_info.get("usage_characters", 0)
            
            # 保存文件
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
            
            return TTSResult(
                success=True,
                audio_path=output_path,
                audio_hex=audio_hex,
                duration_seconds=duration_ms / 1000,
                file_size_kb=file_size / 1024,
                usage_characters=usage_chars
            )
        
        except requests.exceptions.RequestException as e:
            return TTSResult(success=False, error=f"Request failed: {e}")
        except Exception as e:
            return TTSResult(success=False, error=f"Error: {e}")
    
    def estimate_cost(self, characters: int, model: Optional[str] = None) -> Dict[str, float]:
        """
        估算费用
        
        Args:
            characters: 字符数
            model: 模型名称
        
        Returns:
            费用信息字典
        """
        model = model or self.config.model
        
        # 定价（美元 / 1K 字符）
        pricing = {
            "speech-2.6-turbo": 0.02,
            "speech-2.6-hd": 0.035
        }
        
        rate = pricing.get(model, 0.02)
        cost_usd = (characters / 1000) * rate
        cost_cny = cost_usd * 7.2  # 假设汇率
        
        return {
            "characters": characters,
            "model": model,
            "cost_usd": cost_usd,
            "cost_cny": cost_cny,
            "rate_per_1k": rate
        }


# 便捷函数
def create_client() -> MiniMaxTTSClient:
    """创建 TTS 客户端"""
    return MiniMaxTTSClient()


def synthesize_text(
    text: str,
    voice_id: str,
    output_path: Optional[Path] = None,
    speed: float = 1.0,
    vol: float = 1.0,
    pitch: int = 0
) -> TTSResult:
    """
    合成文本（便捷函数）
    
    Args:
        text: 要合成的文本
        voice_id: 音色 ID
        output_path: 输出路径
        speed: 语速
        vol: 音量
        pitch: 音调
    
    Returns:
        TTSResult 对象
    """
    client = create_client()
    voice_setting = VoiceSetting(
        voice_id=voice_id,
        speed=speed,
        vol=vol,
        pitch=pitch
    )
    return client.synthesize(text, voice_setting, output_path)


if __name__ == "__main__":
    # 测试
    client = create_client()
    
    result = synthesize_text(
        text="你好，这是一个测试。",
        voice_id="Chinese (Mandarin)_Warm_Girl",
        output_path=Path("/tmp/test_tts.mp3")
    )
    
    if result.success:
        print(f"✅ 成功！")
        print(f"   时长: {result.duration_seconds:.2f}s")
        print(f"   大小: {result.file_size_kb:.2f}KB")
        print(f"   字符: {result.usage_characters}")
        print(f"   路径: {result.audio_path}")
    else:
        print(f"❌ 失败: {result.error}")
