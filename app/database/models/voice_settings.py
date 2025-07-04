"""
TTS音声設定のデータベースモデル
"""
from tortoise.models import Model
from tortoise import fields
from typing import Dict, Any


class VoiceSettings(Model):
    """ユーザーの音声設定モデル"""
    
    id = fields.IntField(pk=True)
    user_id = fields.CharField(max_length=20, unique=True, description="Discord User ID")
    voice = fields.CharField(max_length=100, null=True, description="選択された音声キャラクター")
    
    # 音声パラメータ
    volume = fields.FloatField(default=1.0, description="音量 (0.0-2.0)")
    speed = fields.FloatField(default=1.0, description="速度 (0.5-4.0)")
    pitch = fields.FloatField(default=1.0, description="ピッチ (0.5-2.0)")
    pitch_range = fields.FloatField(default=1.0, description="ピッチレンジ (0.0-2.0)")
    
    # ポーズ設定
    middle_pause = fields.IntField(default=150, description="短いポーズ (ms)")
    long_pause = fields.IntField(default=300, description="長いポーズ (ms)")
    
    # 感情スタイル
    style_j = fields.FloatField(default=0.0, description="Joyful スタイル (0.0-1.0)")
    style_a = fields.FloatField(default=0.0, description="Angry スタイル (0.0-1.0)")
    style_s = fields.FloatField(default=0.0, description="Sad スタイル (0.0-1.0)")
    
    # メタデータ
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "voice_settings"
        ordering = ["-updated_at"]
    
    def __str__(self) -> str:
        return f"VoiceSettings(user_id={self.user_id}, voice={self.voice})"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（既存コードとの互換性のため）"""
        return {
            "voice": self.voice,
            "volume": self.volume,
            "speed": self.speed,
            "pitch": self.pitch,
            "pitchRange": self.pitch_range,
            "middlePause": self.middle_pause,
            "longPause": self.long_pause,
            "styleJ": self.style_j,
            "styleA": self.style_a,
            "styleS": self.style_s,
        }
    
    @classmethod
    async def get_user_settings(cls, user_id: str) -> Dict[str, Any]:
        """ユーザー設定を取得（存在しない場合はデフォルト値）"""
        try:
            settings = await cls.get(user_id=user_id)
            return settings.to_dict()
        except cls.DoesNotExist:
            return {}
    
    @classmethod
    async def update_user_settings(cls, user_id: str, settings: Dict[str, Any]) -> "VoiceSettings":
        """ユーザー設定を更新または作成"""
        # None値やキーが存在しない場合のデフォルト値処理
        defaults = {
            "voice": settings.get("voice") if settings.get("voice") is not None else None,
            "volume": float(settings.get("volume", 1.0)),
            "speed": float(settings.get("speed", 1.0)),
            "pitch": float(settings.get("pitch", 1.0)),
            "pitch_range": float(settings.get("pitchRange", 1.0)),
            "middle_pause": int(settings.get("middlePause", 150)),
            "long_pause": int(settings.get("longPause", 300)),
            "style_j": float(settings.get("styleJ", 0.0)),
            "style_a": float(settings.get("styleA", 0.0)),
            "style_s": float(settings.get("styleS", 0.0)),
        }
        
        obj, created = await cls.update_or_create(
            user_id=user_id,
            defaults=defaults
        )
        return obj
