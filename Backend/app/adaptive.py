"""Pick a consultation mode from measured bandwidth, latency, and loss."""

from app.schemas import QualityDecision

PROFILES = {
    "store_and_forward": QualityDecision(
        mode="store_and_forward",
        quality_profile="offline_sync",
        max_video_bitrate_kbps=0,
        resolution="none",
        fps=0,
        audio_bitrate_kbps=0,
        use_store_and_forward=True,
        reason="Link is too weak for a live session. Queue compressed records and chat.",
    ),
    "chat_only": QualityDecision(
        mode="chat_only",
        quality_profile="text",
        max_video_bitrate_kbps=0,
        resolution="none",
        fps=0,
        audio_bitrate_kbps=0,
        use_store_and_forward=True,
        reason="Use compact text chat; sync undelivered messages when the link returns.",
    ),
    "audio_only": QualityDecision(
        mode="audio_only",
        quality_profile="voice_low",
        max_video_bitrate_kbps=0,
        resolution="none",
        fps=0,
        audio_bitrate_kbps=16,
        use_store_and_forward=False,
        reason="Voice-only Opus at 16 kbps is more reliable than video on this link.",
    ),
    "ultra_low": QualityDecision(
        mode="video",
        quality_profile="ultra_low",
        max_video_bitrate_kbps=80,
        resolution="160x120",
        fps=8,
        audio_bitrate_kbps=16,
        use_store_and_forward=False,
        reason="Very low-resolution, low-FPS video with tight bitrate caps.",
    ),
    "low": QualityDecision(
        mode="video",
        quality_profile="low",
        max_video_bitrate_kbps=200,
        resolution="320x240",
        fps=12,
        audio_bitrate_kbps=24,
        use_store_and_forward=False,
        reason="Low-bandwidth video suitable for rural 2G/3G links.",
    ),
    "medium": QualityDecision(
        mode="video",
        quality_profile="medium",
        max_video_bitrate_kbps=500,
        resolution="640x360",
        fps=15,
        audio_bitrate_kbps=32,
        use_store_and_forward=False,
        reason="Stable enough for modest video with adaptive bitrate.",
    ),
}


def decide_quality(bandwidth_kbps: float, latency_ms: float, packet_loss: float) -> QualityDecision:
    unstable = latency_ms >= 800 or packet_loss >= 0.15
    very_weak = bandwidth_kbps < 32 or (unstable and bandwidth_kbps < 80)

    if very_weak:
        return PROFILES["store_and_forward"]
    if bandwidth_kbps < 48 or (unstable and bandwidth_kbps < 120):
        return PROFILES["chat_only"]
    if bandwidth_kbps < 120 or latency_ms >= 500:
        return PROFILES["audio_only"]
    if bandwidth_kbps < 250:
        return PROFILES["ultra_low"]
    if bandwidth_kbps < 500:
        return PROFILES["low"]
    return PROFILES["medium"]
