from prisma.models import Guild

class GuildRepository:
    @staticmethod
    async def create(discordId: int):
        return await Guild.prisma().create({
                'discordId': discordId
        })

