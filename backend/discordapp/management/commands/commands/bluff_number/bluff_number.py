import discord
from discord import app_commands

from .bluff_number_game import BluffNumberGame
from .bluff_number_views import LobbyView, active_games, game_messages


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
            "**数字のハッタリで相手を騙せ！**\n\n"
            "1. 全員に秘密の数字(1〜10)が配られる\n"
            "2. 「3人の合計は **X以上** だ！」と順番に宣言\n"
            "3. 前の人より**大きい数**を言うか、**チャレンジ**する\n"
            "4. チャレンジ → 答え合わせ！ ハズした方が **-1点**\n\n"
            "```\n"
            "例) A:7 B:3 C:5 のとき (合計15)\n"
            " A「12以上！」→ B「16以上！」→ C「チャレンジ！」\n"
            " → 合計15 < 16 なのでBのハッタリ失敗！B: -1点\n"
            "```\n"
            "**3ラウンド**で最もポイントが高い人の勝ち！"
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

    # ロビーメッセージを記録
    lobby_msg = await interaction.original_response()
    game_messages[channel_id] = [lobby_msg]