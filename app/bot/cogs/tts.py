import asyncio
import re
import discord
import threading
from discord import app_commands, Interaction
from discord.ext import commands
from typing import Dict, Any
from ...web.server import create_web_server
from ...database.config import init_db, close_db
from ...database.models.voice_settings import VoiceSettings
from ...core.tts_manager import TTSManager

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
        
        # メッセージの前処理（メンション・絵文字・URL置き換え）
        processed_content = message.content
        
        # メンションを表示名に置き換え
        for mention in message.mentions:
            print(f"メンション置き換え: {mention.mention} -> {mention.display_name}")
            processed_content = processed_content.replace(mention.mention, mention.display_name)
        
        # 絵文字をテキストに置き換え
        processed_content = re.sub(r'<a?:([^:]+):(\d+)>', r'[\1]', processed_content)
        
        # URLは読み上げ時に「URL省略」とする
        processed_content = re.sub(r'https?://\S+', '[URL省略]', processed_content)
        
        # 処理されたコンテンツをメッセージに設定
        message.content = processed_content
        
        print(f"元メッセージ: {message.content} -> 処理後: {processed_content}")

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
    
    async def _play_audio_in_discord(self, guild_id: int, audio_file: str = "data/audio/output.wav") -> None:
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
