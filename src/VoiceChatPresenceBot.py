import asyncio
import numpy as np
from datetime import datetime
from discord.ext import commands, tasks
from src.DataAggregator import DataAggregator

_loop = asyncio.get_event_loop()


class VoiceChatPresenceBot(commands.Cog):
    def __init__(self, bot, groups):
        """

        :param bot: discord Bot
        :param groups: dict with group names and their respective voice channel ids
        """
        self.bot = bot
        self.dataAggregator = DataAggregator(groups.keys())
        self.ids = {}
        self._last_member = self.main_author = None
        self.groups = groups
        for group in self.groups:
            groups[group]['name'] = group
            group = groups[group]
            group['counter'] = 0
            group['is_running'] = False
            group['attendance'] = {}
            group['all_time_attendees'] = set()
            group['meeting_date'] = group['meeting_start'] = group['meeting_end'] = group['author'] = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        print(f'Logged in as ---> {self.bot.user}')
        print(f'Id: {self.bot.user.id}')

    def get_voice_channel_members(self, channel_id):
        """Method returns list of members of channel with given id

        :param
            channel_id: id of channel
        :return:
            list of discord.Members in channel if there are some and channel exists
        """
        voice_channel = self.bot.get_channel(channel_id)
        if voice_channel:
            return voice_channel.members
        if not voice_channel:
            return []

    def notify_absents(self, attendees, group_name):
        """Notifies absent attendees by msg

        :param attendees: list of Discord.members in voice chat
        :param group_name: name of voice chat
        """
        all_attendees = np.array(list(self.groups[group_name]['all_time_attendees']))
        absent_users = all_attendees[np.in1d(all_attendees, attendees, invert=True)]
        for user in absent_users:
            disc_user = self.bot.get_user(self.ids[user])
            asyncio.run_coroutine_threadsafe(disc_user.send("JE SCHUZE TY MAGORE, UZ SI TAM MEL 3 MINUTY BEJT!"), _loop)

    def record_meeting_activity(self, group):
        """Record presence/absence of users in voice chat meeting

        :param group: dict with group description
        :return: log to be send to author of meeting recording
        """
        group['counter'] += 1
        voice_channel_members = self.get_voice_channel_members(group['voice_channel_id'])
        attendees = [attendee.name for attendee in voice_channel_members]
        self.ids = {**self.ids, **{f'{attendee.name}': attendee.id for attendee in voice_channel_members}}
        for attendee in attendees:
            group['attendance'][attendee] = group['attendance'][attendee] + 1 if attendee in group['attendance'] else 1
            group['all_time_attendees'].add(attendee)

        self.notify_absents(attendees, group['name'])

        return group['author'].send(f"{group['name']} attendance: {group['attendance']}")

    @tasks.loop(seconds=10)
    async def my_background_task(self):
        """Run members presence each x seconds/minutes

        """
        for group in self.groups:
            group = self.groups[group]
            print(group)
            if group['is_running']:
                await self.record_meeting_activity(group)

    @commands.command(pass_context=True)
    async def start(self, ctx, *args):
        """Starts members presence

        """
        author = ctx.author
        if len(args) == 0:
            print("Missing group name argument")
            await author.send("Missing group name argument")
        else:
            group_name = args[0]
            if group_name in self.groups.keys():
                if self.groups[group_name]['is_running']:
                    print(f"{group_name} is already running")
                    return

                print(f'Starting {group_name} meeting!')
                group = self.groups[group_name]
                group['author'] = author
                group['is_running'] = True
                print(f"zapinam is running: {group['is_running']}")
                group['counter'] = 0
                print(f"zapinam counter: {group['counter']}")
                now = datetime.now()

                group['meeting_date'] = now.strftime("%d/%m/%Y")
                group['meeting_start'] = now.strftime("%H:%M:%S")
                group['meeting_end'] = None
                group['attendance'] = dict()

                await group['author'].send(f'Starting {group_name} meeting!')
                await group['author'].send(group['meeting_date'])
                await group['author'].send(group['meeting_start'])

                if not self.my_background_task.is_running():
                    self.my_background_task.start()
                else:
                    print("background task is already started")
            else:
                await author.send(f'Wrong group name: {group_name}')

    @commands.command(pass_context=True)
    async def stop(self, ctx, *args):
        """Stops members presence

        """
        author = ctx.author
        if len(args) == 0:
            print("Missing group name argument")
            await author.send("Missing group name argument")
        else:
            group_name = args[0]
            if group_name in self.groups.keys():
                if not self.groups[group_name]['is_running']:
                    print(f"{group_name} is already stopped")
                    return

                print(f'Stopping {group_name} meeting!')
                group = self.groups[group_name]
                group['is_running'] = False
                print(f"vypinam is running: {group['is_running']}")

                is_running = np.array([self.groups[temp_group_name]['is_running'] for temp_group_name in self.groups.keys()])
                print(is_running)
                print(np.any(is_running))
                if np.any(is_running):
                    print("?????")
                else:
                    self.my_background_task.cancel()

                now = datetime.now()

                group['meeting_end'] = now.strftime("%H:%M:%S")

                await group['author'].send(f'Ending {group_name} meeting!')
                await group['author'].send(group['meeting_end'])
                await group['author'].send(group['attendance'])

                self.dataAggregator.update_attendance(group)
            else:
                await author.send(f'Wrong group name: {group_name}')
