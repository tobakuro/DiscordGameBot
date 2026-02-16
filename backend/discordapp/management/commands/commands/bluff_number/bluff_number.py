import discord
from discord import app_commands

from .bluff_number_game import BluffNumberGame
from .bluff_number_views import LobbyView, active_games


@app_commands.command(
    name="bluff_number", description="ブラフナンバーゲームを開始します（3人用）"
)
async def bluff_number(interaction: discord.Interaction):
    channel_id = interaction.channel_id

    if channel_id in active_games:
        await interaction.response.send_message(
            "このチャンネルでは既にゲームが進行中です。", ephemeral=True
        )
        return

    game = BluffNumberGame(channel_id=channel_id, host_user_id=interaction.user.id)
    active_games[channel_id] = game

    # コマンド実行者を自動参加
    game.add_player(interaction.user.id, interaction.user.display_name)

    embed = discord.Embed(
        title="\U0001f3b2 ブラフナンバー",
        description=(
            "ブラフナンバーゲームを開始します！\n\n"
            "**ルール:**\n"
            "・各プレイヤーに1〜10の秘密の数字が配られます\n"
            "・順番に「全員の合計はX以上」と宣言します\n"
            "・宣言は前の数字より大きくなければなりません\n"
            "・チャレンジで宣言が正しいか確認できます\n"
            "・3ラウンド行い、最もポイントが高い人の勝ちです\n"
        ),
        color=0x3498DB,
    )
    embed.add_field(
        name="参加者 (1/3)",
        value=f"1. {interaction.user.display_name}",
        inline=False,
    )
    embed.set_footer(text="3人揃うと自動的にゲームが開始されます")

    view = LobbyView(game)
    await interaction.response.send_message(embed=embed, view=view)