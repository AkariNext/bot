"""
A.I.VOICE TTS Manager
"""
from aivoice_python import AIVoiceTTsControl, HostStatus
from typing import Dict, Any


class TTSManager:
    """A.I.VOICE TTS制御のマネージャークラス"""
    
    def __init__(self):
        self.tts_control = None
        self.voice_names: Dict[str, str] = {}
        self.temp_preset_name = "WebUI_TempPreset"
        self._initialize_tts()
    
    def _initialize_tts(self) -> None:
        """TTS制御の初期化"""
        try:
            self.tts_control = AIVoiceTTsControl()
            host_names = self.tts_control.get_available_host_names()
            
            if not host_names:
                raise RuntimeError("No available host names found. Please check your AIVoiceTTsControl configuration.")
            
            self.tts_control.initialize(host_names[0])
            
            if self.tts_control.status == HostStatus.NotRunning:
                self.tts_control.start_host()
            
            print('Connecting to TTS host...')
            # 初期接続テスト
            with self.tts_control.connect():
                print('TTS connection successful!')
            
            # 音声名マッピングを作成
            self._build_voice_mapping()
            
            # 共用プリセットを作成
            self._create_temp_preset()
            
        except Exception as e:
            print(f"TTS初期化エラー: {e}")
            raise
    
    def _build_voice_mapping(self) -> None:
        """音声名のマッピングを構築"""
        with self.tts_control.connect():
            self.voice_names = {}
            for voice_name in self.tts_control.voice_names:
                preset = self.tts_control.get_voice_preset(voice_name)
                self.voice_names[voice_name] = preset["VoiceName"]
    
    def _create_temp_preset(self) -> None:
        """一時プリセットを作成"""
        with self.tts_control.connect():
            if self.temp_preset_name not in self.tts_control.voice_preset_names:
                default_voice = list(self.voice_names.keys())[0] if self.voice_names else None
                if default_voice:
                    self.tts_control.add_voice_preset({
                        "PresetName": self.temp_preset_name,
                        "VoiceName": self.voice_names[default_voice],
                        "Volume": 1.0,
                        "Speed": 1.0,
                        "Pitch": 1.0,
                        "PitchRange": 1.0,
                        "MiddlePause": 150,
                        "LongPause": 300,
                        "Styles": [
                            {"Name": "J", "Value": 0.0},
                            {"Name": "A", "Value": 0.0},
                            {"Name": "S", "Value": 0.0}
                        ]
                    })
    
    def create_voice_preset(self, user_settings: Dict[str, Any]) -> Dict[str, Any]:
        """ユーザー設定からVoicePresetを作成"""
        user_voice = user_settings.get("voice", list(self.voice_names.keys())[0] if self.voice_names else "")
        
        return {
            "PresetName": self.temp_preset_name,
            "VoiceName": self.voice_names.get(user_voice, list(self.voice_names.values())[0] if self.voice_names else ""),
            "Volume": user_settings.get("volume", 1.0),
            "Speed": user_settings.get("speed", 1.0),
            "Pitch": user_settings.get("pitch", 1.0),
            "PitchRange": user_settings.get("pitchRange", 1.0),
            "MiddlePause": int(user_settings.get("middlePause", 150)),
            "LongPause": int(user_settings.get("longPause", 300)),
            "Styles": [
                {"Name": "J", "Value": user_settings.get("styleJ", 0.0)},
                {"Name": "A", "Value": user_settings.get("styleA", 0.0)},
                {"Name": "S", "Value": user_settings.get("styleS", 0.0)}
            ]
        }
    
    def apply_voice_preset(self, voice_preset: Dict[str, Any], fallback_voice: str = None) -> bool:
        """VoicePresetを適用"""
        with self.tts_control.connect():
            try:
                self.tts_control.set_voice_preset(voice_preset)
                self.tts_control.current_voice_preset_name = self.temp_preset_name
                return True
            except Exception as e:
                print(f"Error setting voice preset: {e}")
                if fallback_voice:
                    try:
                        self.tts_control.current_voice_preset_name = fallback_voice
                        return True
                    except Exception as fallback_error:
                        print(f"Fallback error: {fallback_error}")
                return False
    
    def generate_audio(self, text: str, output_file: str = "data/audio/output.wav") -> bool:
        """音声を生成してファイルに保存"""
        with self.tts_control.connect():
            try:
                self.tts_control.text = text
                self.tts_control.save_audio_to_file(output_file)
                return True
            except Exception as e:
                print(f"Audio generation error: {e}")
                return False
    
    def is_connected(self) -> bool:
        """TTS接続状態をチェック"""
        try:
            return self.tts_control and self.tts_control.status == HostStatus.Ready
        except Exception:
            return False
    
    def reconnect(self) -> bool:
        """TTS接続を再試行"""
        try:
            with self.tts_control.connect():
                print('🔄 TTS reconnection successful!')
                return True
        except Exception as e:
            print(f"❌ TTS reconnection failed: {e}")
            return False


# TTSマネージャーのグローバルインスタンス
tts_manager = TTSManager()
