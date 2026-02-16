import discord
from asgiref.sync import sync_to_async
from discord import app_commands
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from .commands.command1 import split_voice
from .commands.quizcmd import quiz

CustomUser = get_user_model()


class MyClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_voice_state_update(self, member, before, after):
        if before.channel is None and after.channel is not None:
            await after.channel.send(
                f"{member.display_name} has joined the voice channel."
            )


client = MyClient(intents=discord.Intents.default())
client.tree.add_command(quiz)
client.tree.add_command(split_voice)


class Command(BaseCommand):
    help = "runs the discord bot"

    def handle(self, *args, **options):
        client.run(settings.DISCORD_BOT_TOKEN)
