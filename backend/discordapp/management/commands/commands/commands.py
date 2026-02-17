import discord
from discord import app_commands


@app_commands.command(name="test1", description="テストコマンド")
async def test1(interaction: discord.Interaction):
    embed = discord.Embed(
        title="テストコマンド",
        description="これはテストコマンドです。",
        color=0x00FF00,
    )
    await interaction.response.send_message(embed=embed)
