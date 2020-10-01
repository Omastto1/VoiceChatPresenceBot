from datetime import datetime
from discord.ext import commands, tasks


class VoiceChatPresenceBot(commands.Cog):
    def __init__(self, bot, voice_channel_id):
        self.bot = bot
        self.voice_channel_id = voice_channel_id
        self.channel_log_id = 760601431925063694
        self.counter = 0
        self.meeting_date = self.meeting_start = self.meeting_end = self.attendance = self.log_channel = self.channel = \
            self._last_member = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        print(f'Logged in as ---> {self.bot.user}')
        print(f'Id: {self.bot.user.id}')
        self.log_channel = self.bot.get_channel(self.channel_log_id)

    def get_voice_channel_members(self):
        voice_channel = self.bot.get_channel(self.voice_channel_id)
        if voice_channel:
            return voice_channel.members
        if not voice_channel:
            return []

    @tasks.loop(seconds=10)
    async def my_background_task(self):
        self.counter += 1
        attendees = self.get_voice_channel_members()
        for attendee in attendees:
            self.attendance[attendee.name] = self.attendance[attendee.name] + 1 if attendee.name in self.attendance \
                else 1

        await self.log_channel.send(self.attendance)

    @commands.command(pass_context=True)
    async def start(self, ctx):
        now = datetime.now()

        self.meeting_date = now.strftime("%d/%m/%Y")
        self.meeting_start = now.strftime("%H:%M:%S")
        self.meeting_end = None
        self.attendance = dict()

        await self.log_channel.send(self.meeting_date)
        await self.log_channel.send(self.meeting_start)

        self.my_background_task.start()

    @commands.command(pass_context=True)
    async def stop(self, ctx):
        self.my_background_task.cancel()

        now = datetime.now()

        self.meeting_end = now.strftime("%H:%M:%S")

        await self.log_channel.send(self.meeting_end)
        await self.log_channel.send(self.attendance)
