import discord
import requests
from asgiref.sync import sync_to_async
from discord import app_commands
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from .commands.bluff_number.bluff_number import bluff_number
from .commands.quizcmd import quiz

CustomUser = get_user_model()


class MyClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)
        self.token = self.get_token()

    def get_token(self) -> str:
        # r = requests.post(
        #     f"http://127.0.0.1:8000/api/login/",
        #     json={"username": "arcsino", "password": "testpass123"},
        # )
        # return r.json().get("token", "")
        pass

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_member_join(self, member):
        for _ in range(3):
            r = requests.post(
                f"http://127.0.0.1:8000/api/quiz-result/{member.id}/{member.display_name}/"  # ちがう
            )
            if not r.status_code == 401:
                break

    async def on_voice_state_update(self, member, before, after):
        if before.channel is None and after.channel is not None:
            await after.channel.send(
                f"{member.display_name} has joined the voice channel."
            )


client = MyClient(intents=discord.Intents.default())
client.tree.add_command(quiz)
client.tree.add_command(bluff_number)


class Command(BaseCommand):
    help = "runs the discord bot"

    def handle(self, *args, **options):
        client.run(settings.DISCORD_BOT_TOKEN)
