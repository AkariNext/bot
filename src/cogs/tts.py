import asyncio
import discord
import threading
from discord import app_commands, Interaction
from discord.ext import commands
from aivoice_python import AIVoiceTTsControl, HostStatus
from typing import Dict, Any
from ..web_server import create_web_server
from ..database import init_db, close_db
from ..models.voice_settings import VoiceSettings


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
            self.tts_control.connect()
            
            # 音声名マッピングを作成
            self._build_voice_mapping()
            
            # 共用プリセットを作成
            self._create_temp_preset()
            
        except Exception as e:
            print(f"TTS初期化エラー: {e}")
            raise
    
    def _build_voice_mapping(self) -> None:
        """音声名のマッピングを構築"""
        self.voice_names = {}
        for voice_name in self.tts_control.voice_names:
            preset = self.tts_control.get_voice_preset(voice_name)
            self.voice_names[voice_name] = preset["VoiceName"]
    
    def _create_temp_preset(self) -> None:
        """一時プリセットを作成"""
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
    
    def generate_audio(self, text: str, output_file: str = "output.wav") -> bool:
        """音声を生成してファイルに保存"""
        try:
            self.tts_control.text = text
            self.tts_control.save_audio_to_file(output_file)
            return True
        except Exception as e:
            print(f"Audio generation error: {e}")
            return False


# TTSマネージャーのグローバルインスタンス
tts_manager = TTSManager()


class TTSCog(commands.Cog):
    """Discord TTS Bot のメインCogクラス"""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.tts_controls: Dict[int, Dict[str, discord.VoiceClient]] = {}  # サーバーごとのVC管理
        
        # データベース初期化とマイグレーションを非同期で実行
        self.bot.loop.create_task(self._initialize_database())
        
        # Webサーバーを別スレッドで起動
        self._start_web_server()

    async def _initialize_database(self) -> None:
        """データベースの初期化"""
        try:
            await init_db()
        except Exception as e:
            print(f"データベース初期化エラー: {e}")

    def _start_web_server(self) -> None:
        """Webサーバーを別スレッドで起動"""
        def run_server():
            web_server = create_web_server(tts_manager.tts_control)
            web_server.start(host="localhost", port=8080)
        
        web_thread = threading.Thread(target=run_server, daemon=True)
        web_thread.start()
        print("🌟 TTS Web Interface started on http://localhost:8080")

    # 以下のメソッドは削除（DB操作で置き換え）
    # def _load_voice_settings(self) -> Dict[str, Any]:
    # def _save_voice_settings(self) -> None:
    
    async def _get_user_voice_settings(self, user_id: str) -> Dict[str, Any]:
        """指定ユーザーの音声設定を取得（DB から）"""
        try:
            return await VoiceSettings.get_user_settings(user_id)
        except Exception as e:
            print(f"ユーザー設定取得エラー: {e}")
            return {}
    
    async def _save_user_voice_settings(self, user_id: str, settings: Dict[str, Any]) -> None:
        """ユーザーの音声設定を保存（DB へ）"""
        try:
            await VoiceSettings.update_user_settings(user_id, settings)
        except Exception as e:
            print(f"ユーザー設定保存エラー: {e}")

    group = app_commands.Group(name='voice', description='voice commands')

    @group.command(name='join', description='ボイスチャンネルに参加します')
    async def join(self, interaction: Interaction):
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            vc = await channel.connect()
            self.tts_controls[interaction.guild.id] = {
                "vc": vc
            }
            await interaction.response.send_message(f'Joined {channel.name}')
        else:
            await interaction.response.send_message('You are not connected to a voice channel.')

    @group.command(name='leave', description='ボイスチャンネルから退出します')
    async def leave(self, interaction: Interaction):
        if interaction.guild.id in self.tts_controls:
            vc = self.tts_controls[interaction.guild.id]["vc"]
            await vc.disconnect()
            del self.tts_controls[interaction.guild.id]
            await interaction.response.send_message('Disconnected from the voice channel.')
        else:
            await interaction.response.send_message('I am not connected to a voice channel.')

    @group.command(name='set_voice', description='読み上げキャラを設定します')
    @app_commands.choices(voice_name=[
        app_commands.Choice(name=voice, value=voice) for voice in tts_manager.tts_control.voice_names
    ])
    async def set_voice(self, interaction: Interaction, voice_name: app_commands.Choice[str]):
        """音声キャラクターを設定"""
        await self._save_user_voice_settings(str(interaction.user.id), {"voice": voice_name.value})
        await interaction.response.send_message(f"Voice set to {voice_name.value} for {interaction.user.name}.")

    @group.command(name='settings', description='Web画面で詳細な音声設定を行います')
    async def web_settings(self, interaction: Interaction):
        embed = discord.Embed(
            title="🎤 TTS Voice Settings",
            description="Webブラウザで詳細な音声設定を行えます！",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🌟 機能",
            value="• ピッチ調整\n• 速度調整\n• 音量調整\n• 感情パラメータ",
            inline=False
        )
        embed.add_field(
            name="🔗 アクセス",
            value="[Web設定画面を開く](http://localhost:8080)",
            inline=False
        )
        embed.add_field(
            name="🔐 認証",
            value="Discordアカウントでログインして設定を保存できます",
            inline=False
        )
        embed.set_footer(text="💡 Botと同じPCからアクセスしてください")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """メッセージ受信時の音声合成・再生処理"""
        if message.author.bot or message.guild is None:
            return

        if message.guild.id in self.tts_controls:
            await self._process_tts_message(message)
    
    async def _process_tts_message(self, message: discord.Message) -> None:
        """TTS処理を実行"""
        # ユーザー設定を取得（DB から）
        user_settings = await self._get_user_voice_settings(str(message.author.id))
        print(f"ユーザー設定: {user_settings}")
        
        # VoicePresetを作成
        voice_preset = tts_manager.create_voice_preset(user_settings)
        
        # プリセットを適用
        fallback_voice = user_settings.get("voice", list(tts_manager.voice_names.keys())[0] if tts_manager.voice_names else "")
        if not tts_manager.apply_voice_preset(voice_preset, fallback_voice):
            print("VoicePreset適用に失敗しました")
            return
        
        # 音声を生成
        if not tts_manager.generate_audio(message.content):
            print("音声生成に失敗しました")
            return
        
        # Discordで再生
        await self._play_audio_in_discord(message.guild.id)
    
    async def _play_audio_in_discord(self, guild_id: int, audio_file: str = "output.wav") -> None:
        """Discordボイスチャンネルで音声を再生"""
        try:
            vc = self.tts_controls[guild_id]["vc"]
            
            # 現在再生中の音声が終わるまで待機
            while vc.is_playing():
                await asyncio.sleep(0.5)
            
            # 音声を再生
            vc.play(discord.FFmpegPCMAudio(audio_file))
            
        except Exception as e:
            print(f"音声再生エラー: {e}")

    async def cog_unload(self) -> None:
        """Cog のアンロード時にデータベース接続を閉じる"""
        await close_db()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TTSCog(bot))
    print(f'{__name__} loaded successfully.')
