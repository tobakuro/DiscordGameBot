import discord
from discord import app_commands
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from .commands import modules, quizcmd
from .commands.bluff_number.bluff_number import bluff_number
from .commands.flash import flash
from .commands.nyaagenesis import nyaagenesis
from .commands.wakewake import wake1

CustomUser = get_user_model()


class MyClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)
        self.token = self.get_token()

    def get_token(self) -> str:
        res = modules.login_request()
        return res.json().get("token", "")

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_member_join(self, member):
        """メンバーがサーバーに参加したときのイベント"""
        res = modules.add_member_to_guild_request(
            guild_id=member.guild.id,
            guild_name=member.guild.name,
            discord_id=str(member.id),
            username=member.display_name,
        )

    async def on_member_remove(self, member):
        """メンバーがサーバーから退出したときのイベント"""
        res = modules.remove_member_from_guild_request(
            guild_id=member.guild.id,
            guild_name=member.guild.name,
            discord_id=str(member.id),
            username=member.display_name,
        )

    async def on_voice_state_update(self, member, before, after):
        """ユーザーがボイスチャンネルに参加したときのイベント"""
        if before.channel is None and after.channel is not None:
            await after.channel.send(
                f"{member.display_name} has joined the voice channel."
            )


client = MyClient(intents=discord.Intents.all())
client.tree.add_command(quizcmd.quiz)
client.tree.add_command(quizcmd.quiz_result_list)
client.tree.add_command(quizcmd.quiz_result)
client.tree.add_command(wake1)
client.tree.add_command(flash)
client.tree.add_command(bluff_number)
client.tree.add_command(nyaagenesis)


class Command(BaseCommand):
    help = "runs the discord bot"

    def handle(self, *args, **options):
        client.run(settings.DISCORD_BOT_TOKEN)
