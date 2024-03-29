import asyncio
import json
import numpy as np
import discord
import os
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
        self.main_author = None
        self.groups = groups
        for group in self.groups:
            groups[group]['name'] = group
            group = groups[group]
            group['counter'] = 0
            group['is_running'] = False
            group['attendance'] = {}
            group['all_time_attendees'] = set()
            group['meeting_date'] = group['meeting_start'] = group['meeting_end'] = group['author'] = None
            group['absents_pinged'] = set()

            group['members'] = set()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        print(f'Logged in as ---> {self.bot.user}')
        print(f'Id: {self.bot.user.id}')

        self.eforce_server = discord.utils.get(self.bot.guilds, name='eForce')

        all_time_attendees = self.dataAggregator.load_data()
        for group in all_time_attendees:
            self.groups[group]['all_time_attendees'] = all_time_attendees[group]

        with open(f"data/ids.json", 'r', encoding='utf-8') as f:
            self.ids = json.load(f)

        await self.get_user_group_membership()

        print(self.groups)

    @commands.Cog.listener()
    async def on_disconnect(self):
        print("ERROR!")
        await self.main_author.send("disconnected")

    @commands.Cog.listener()
    async def on_error(self):
        print("ERROR!")

    @commands.command()
    @commands.has_any_role('Illuminati', 'Vedouci', 'Správce Discordu')
    async def export_xlsx(self, ctx, *args):
        """Exports xlsx attendance file of given group

        :param *args: has to contain name of group for which export is desired
        """
        author = ctx.author
        if len(args) == 0:
            print("Missing group name argument")
            await author.send("Missing group name argument")
        else:
            group_name = args[0]
            file = f"data/{group_name}_aggregated_meetings_attendance.xlsx"
            if os.path.exists(file):
                with open(file, 'rb') as f:
                    await ctx.author.send(file=discord.File(f, f"{group_name}_attendance.xlsx"))
            else:
                await author.send(f"Record of **{group_name}**'s attendance does not exist!")

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
            if user not in self.groups[group_name]['absents_pinged']:
                self.groups[group_name]['absents_pinged'].add(user)
                disc_user = self.bot.get_user(self.ids[user])
                asyncio.run_coroutine_threadsafe(disc_user.send("JE SCHUZE TY MAGORE, UZ SI TAM MEL 3 MINUTY BEJT!"),
                                                 _loop)

    def record_meeting_activity(self, group):
        """Record presence/absence of users in voice chat meeting

        :param group: dict with group description
        :return: log to be send to author of meeting recording
        """
        group['counter'] += 1
        voice_channel_members = self.get_voice_channel_members(group['voice_channel_id'])
        attendees = [attendee.name for attendee in voice_channel_members]

        new_attendees = {f'{attendee.name}': attendee.id for attendee in voice_channel_members}
        if new_attendees:
            self.ids = {**self.ids, **new_attendees}
            self.dataAggregator.update_ids(self.ids)

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
            if group['is_running']:
                await self.record_meeting_activity(group)

    @commands.command()
    @commands.has_any_role('Illuminati', 'Vedouci', 'Správce Discordu')
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
                self.groups[group_name]['absents_pinged'] = set()
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

    @commands.command()
    @commands.has_any_role('Illuminati', 'Vedouci', 'Správce Discordu')
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

                is_running = np.array(
                    [self.groups[temp_group_name]['is_running'] for temp_group_name in self.groups.keys()])

                if not np.any(is_running):
                    self.my_background_task.cancel()

                now = datetime.now()

                group['meeting_end'] = now.strftime("%H:%M:%S")

                await group['author'].send(f'Ending {group_name} meeting!')
                await group['author'].send(group['meeting_end'])
                await group['author'].send(group['attendance'])

                self.dataAggregator.update_attendance(group)
            else:
                await author.send(f'Wrong group name: {group_name}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.channel.send("I do not answer to peasants like you.\n"
                                   "Came back when you become **Illuminati**, **Vedouci** or **Správce Discordu**.")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        print(f"Member {after.name} updated their info.")

        if len(before.roles) > len(after.roles):
            print(f"Role {set(before.roles).difference(set(after.roles)).pop().name} deleted")
            changed_role = set(before.roles).difference(set(after.roles)).pop().name
            self.groups[changed_role]['members'].remove(after.name)
        elif len(before.roles) < len(after.roles):
            print(f"Role {set(after.roles).difference(set(before.roles)).pop().name} added")
            changed_role = set(after.roles).difference(set(before.roles)).pop().name
            self.groups[changed_role]['members'].add(after.name)

    async def get_user_group_membership(self):
        print("Assigning members to their groups")
        self.bot.get_channel
        for group in self.groups:
            role = discord.utils.get(self.eforce_server.roles, name=group)
            for member in self.eforce_server.members:
                if role in member.roles:
                    self.groups[group]['members'].add(member.name)