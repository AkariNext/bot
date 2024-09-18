from prisma import Prisma


async def init():
    prisma = Prisma(auto_register=True)
    await prisma.connect()
