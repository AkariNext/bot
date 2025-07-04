import discord
import json
from discord import app_commands, Interaction
from discord.ext import commands
from aivoice_python import AIVoiceTTsControl
from pathlib import Path

class TTSCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.tts_control = AIVoiceTTsControl()  # クラス全体で共有するインスタンス
        self.tts_controls = {}  # サーバーごとのVC管理のみ
        self.voice_settings_path = Path("voice_settings.json")
        self.voice_settings = self.load_voice_settings()

    def load_voice_settings(self):
        if self.voice_settings_path.exists():
            with open(self.voice_settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_voice_settings(self):
        with open(self.voice_settings_path, "w", encoding="utf-8") as f:
            json.dump(self.voice_settings, f, ensure_ascii=False, indent=4)

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
        app_commands.Choice(name=voice, value=voice) for voice in AIVoiceTTsControl().voice_names
    ])
    async def set_voice(self, interaction: Interaction, voice_name: app_commands.Choice[str]):
        self.voice_settings[str(interaction.user.id)] = voice_name.value
        self.save_voice_settings()
        await interaction.response.send_message(f"Voice set to {voice_name.value} for {interaction.user.name}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        if message.guild.id in self.tts_controls:
            user_voice = self.voice_settings.get(str(message.author.id), self.tts_control.voice_names[0])
            self.tts_control.current_voice_preset_name = user_voice
            self.tts_control.text = message.content
            self.tts_control.save_audio_to_file("output.wav")
            vc = self.tts_controls[message.guild.id]["vc"]
            vc.play(discord.FFmpegPCMAudio("output.wav"))

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TTSCog(bot))
    print(f'{__name__} loaded successfully.')