from discord.ext import commands, tasks


class VoiceChatPresenceBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.counter = 0

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        print(f'Looged in as ---> {self.bot.user}')
        print(f'Id: {self.bot.user.id}')

    @tasks.loop(seconds=2)
    async def my_background_task(self):
        channel = self.bot.get_channel(760601431925063694)  # channel ID goes here
        self.counter += 1
        print(self.counter)
        await channel.send(self.counter)

    @commands.command(pass_context=True)
    async def start(self, ctx):
        self.my_background_task.start()

    @commands.command(pass_context=True)
    async def stop(self, ctx):
        self.my_background_task.stop()

