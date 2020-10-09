import asyncio
import numpy as np
from datetime import datetime
from discord.ext import commands, tasks
from src.DataAggregator import DataAggregator

_loop = asyncio.get_event_loop()


class VoiceChatPresenceBot(commands.Cog):
    def __init__(self, bot, voice_channel_id):
        self.bot = bot
        self.voice_channel_id = voice_channel_id
        self.dataAggregator = DataAggregator()
        self.channel_log_id = 763106308458807304
        self.counter = 0
        self.ids = {}
        self.all_time_attendees = set()
        self.attendance = {}
        self.meeting_date = self.meeting_start = self.meeting_end = self.log_channel = self.channel = \
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

    def notify_absents(self, attendees):
        all_attendees = np.array(list(self.all_time_attendees))
        absent_users = all_attendees[np.in1d(all_attendees, attendees, invert=True)]
        for user in absent_users:
            disc_user = self.bot.get_user(self.ids[user])
            asyncio.run_coroutine_threadsafe(disc_user.send("JE SCHUZE TY MAGORE, UZ SI TAM MEL 3 MINUTY BEJT!"), _loop)

    def record_meeting_activity(self):
        self.counter += 1
        voice_channel_members = self.get_voice_channel_members()
        attendees = [attendee.name for attendee in voice_channel_members]
        self.ids = {**self.ids, **{f'{attendee.name}': attendee.id for attendee in voice_channel_members}}
        for attendee in attendees:
            self.attendance[attendee] = self.attendance[attendee] + 1 if attendee in self.attendance else 1
            self.all_time_attendees.add(attendee)

        self.notify_absents(attendees)

        return self.author.send(self.attendance)

    @tasks.loop(seconds=10)
    async def my_background_task(self):
        await self.record_meeting_activity()

    @commands.command(pass_context=True)
    async def start(self, ctx):
        self.author = ctx.author
        self.counter = 0
        now = datetime.now()

        self.meeting_date = now.strftime("%d/%m/%Y")
        self.meeting_start = now.strftime("%H:%M:%S")
        self.meeting_end = None
        self.attendance = dict()

        await self.author.send(self.meeting_date)
        await self.author.send(self.meeting_start)

        self.my_background_task.start()

    @commands.command(pass_context=True)
    async def stop(self, ctx):
        self.my_background_task.cancel()

        now = datetime.now()

        self.meeting_end = now.strftime("%H:%M:%S")

        await self.author.send(self.meeting_end)
        await self.author.send(self.attendance)

        self.dataAggregator.store_attendance(self.meeting_date, self.meeting_start, self.meeting_end, self.attendance,
                                             self.counter)
        self.dataAggregator.save_data()
