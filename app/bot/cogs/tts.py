import asyncio
import re
import discord
import threading
import hashlib
import os
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
        self.audio_cache_dir = "data/audio/cache"  # キャッシュディレクトリ
        
        # キャッシュディレクトリを作成
        os.makedirs(self.audio_cache_dir, exist_ok=True)
        
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
    
    def _generate_cache_key(self, text: str, voice_preset: Dict[str, Any]) -> str:
        """テキストとプリセットからキャッシュキーを生成"""
        # プリセットを文字列化してソート（辞書の順序に依存しないように）
        preset_str = str(sorted(voice_preset.items()))
        
        # テキストとプリセットを結合してハッシュ化
        combined = f"{text}:{preset_str}"
        cache_key = hashlib.md5(combined.encode('utf-8')).hexdigest()
        
        return cache_key
    
    def _get_cached_audio_path(self, cache_key: str) -> str:
        """キャッシュキーから音声ファイルパスを取得"""
        return os.path.join(self.audio_cache_dir, f"{cache_key}.wav")
    
    def _is_audio_cached(self, cache_key: str) -> bool:
        """音声ファイルがキャッシュされているかチェック"""
        cache_path = self._get_cached_audio_path(cache_key)
        return os.path.exists(cache_path)
    
    def _save_to_cache(self, cache_key: str, source_file: str = "data/audio/output.wav") -> str:
        """生成された音声ファイルをキャッシュに保存"""
        cache_path = self._get_cached_audio_path(cache_key)
        
        try:
            # 元ファイルをキャッシュにコピー
            import shutil
            shutil.copy2(source_file, cache_path)
            print(f"💾 音声ファイルをキャッシュに保存: {cache_key}")
            return cache_path
        except Exception as e:
            print(f"❌ キャッシュ保存エラー: {e}")
            return source_file

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
    
    @group.command(name='clear_cache', description='音声キャッシュをクリアします（管理者のみ）')
    @app_commands.default_permissions(administrator=True)
    async def clear_cache(self, interaction: Interaction):
        """音声キャッシュをクリア"""
        try:
            cache_files = [f for f in os.listdir(self.audio_cache_dir) if f.endswith('.wav')]
            deleted_count = 0
            
            for cache_file in cache_files:
                cache_path = os.path.join(self.audio_cache_dir, cache_file)
                try:
                    os.remove(cache_path)
                    deleted_count += 1
                except OSError:
                    continue
            
            embed = discord.Embed(
                title="🗑️ キャッシュクリア完了",
                description=f"削除したファイル数: {deleted_count}個",
                color=discord.Color.green()
            )
            embed.add_field(
                name="💡 効果",
                value="次回のTTS生成時に新しい音声ファイルが作成されます",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"🗑️ キャッシュクリア完了: {deleted_count}ファイル削除")
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ キャッシュクリアでエラーが発生しました: {e}", 
                ephemeral=True
            )
    
    @group.command(name='cache_info', description='キャッシュ情報を表示します')
    async def cache_info(self, interaction: Interaction):
        """キャッシュ情報を表示"""
        try:
            cache_files = [f for f in os.listdir(self.audio_cache_dir) if f.endswith('.wav')]
            total_files = len(cache_files)
            
            total_size = 0
            for cache_file in cache_files:
                cache_path = os.path.join(self.audio_cache_dir, cache_file)
                try:
                    total_size += os.path.getsize(cache_path)
                except OSError:
                    continue
            
            # バイトサイズを人間が読みやすい形式に変換
            size_mb = total_size / (1024 * 1024)
            
            embed = discord.Embed(
                title="📊 音声キャッシュ情報",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="📁 キャッシュファイル数",
                value=f"{total_files}個",
                inline=True
            )
            embed.add_field(
                name="💾 合計サイズ",
                value=f"{size_mb:.2f} MB",
                inline=True
            )
            embed.add_field(
                name="📂 保存場所",
                value=f"`{self.audio_cache_dir}`",
                inline=False
            )
            embed.set_footer(text="💡 同じ設定・内容の読み上げは高速化されます")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ キャッシュ情報取得でエラーが発生しました: {e}", 
                ephemeral=True
            )

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
        """TTS処理を実行（キャッシュ対応）"""
        # ユーザー設定を取得（DB から）
        user_settings = await self._get_user_voice_settings(str(message.author.id))
        print(f"ユーザー設定: {user_settings}")
        
        # VoicePresetを作成
        voice_preset = tts_manager.create_voice_preset(user_settings)
        
        # キャッシュキーを生成
        cache_key = self._generate_cache_key(message.content, voice_preset)
        
        # キャッシュされた音声ファイルがあるかチェック
        if self._is_audio_cached(cache_key):
            print(f"🎵 キャッシュされた音声を使用: {cache_key}")
            cached_audio_path = self._get_cached_audio_path(cache_key)
            await self._play_audio_in_discord(message.guild.id, cached_audio_path)
            return
        
        print(f"🔄 新しい音声を生成中: {cache_key}")
        
        # プリセットを適用
        fallback_voice = user_settings.get("voice", list(tts_manager.voice_names.keys())[0] if tts_manager.voice_names else "")
        if not tts_manager.apply_voice_preset(voice_preset, fallback_voice):
            print("VoicePreset適用に失敗しました")
            return
        
        # 音声を生成
        if not tts_manager.generate_audio(message.content):
            print("音声生成に失敗しました")
            return
        
        # 生成された音声をキャッシュに保存
        cached_audio_path = self._save_to_cache(cache_key)
        
        # Discordで再生
        await self._play_audio_in_discord(message.guild.id, cached_audio_path)
    
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
