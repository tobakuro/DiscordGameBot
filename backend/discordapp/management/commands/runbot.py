import discord
from asgiref.sync import sync_to_async
from discord import app_commands
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

CustomUser = get_user_model()

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

    # スラッシュコマンドを同期
    await tree.sync()


# @app_commands.default_permissions(administrator=True)
# @tree.command(name="sendembed", description="特定の埋め込みメッセージを送信します")
# async def send_embed_message(ctx:discord.Interaction, message_key:int):
#     pass


class Command(BaseCommand):
    help = "runs the discord bot"

    def handle(self, *args, **options):
        client.run(settings.DISCORD_BOT_TOKEN)
