import discord
from discord import app_commands
from django.conf import settings


@app_commands.command(name="nyaagenesis", description="ニャージェネシスのコマンド")
async def nyaagenesis(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ニャージェネシス",
        description=f"以下のURLをクリックして、ニャージェネシスのゲームを開始してください！\n{settings.NYA_GENESIS_URL}",
        color=0x00FF00,
    )
    await interaction.response.send_message(embed=embed)
