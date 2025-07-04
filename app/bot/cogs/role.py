from discord.ext import commands
from discord import Interaction as Inter, Member, app_commands

ROLES = [
    ["Silver", 536065526112452609],
    ["Gold", 536062237731717141],
    ["Platinum", 537826020439359488]
    ]
ROLE_NAMES = [role[0] for role in ROLES]
ROLE_IDS = [role[1] for role in ROLES]
async def role_autocomplete(inter: Inter, current: str) -> list[app_commands.Choice[str]]:
    return [app_commands.Choice(name=role, value=str(ROLE_NAMES.index(role))) for role in ROLE_NAMES if current.lower() in role.lower()]

class RoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    group = app_commands.Group(name='role', description='Role commands')

    @group.command(name='add', description='指定したユーザーにロールを追加します')
    @app_commands.autocomplete(role=role_autocomplete)
    async def role(self, inter: Inter, target: Member, role: str):
        for i in range(int(role)+1):
            print(ROLE_NAMES[i])
        await inter.response.send_message(f'Role {role} added')
    

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleCog(bot))
