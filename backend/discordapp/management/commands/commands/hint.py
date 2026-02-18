import discord
from discord import app_commands


@app_commands.command(name="hint", description="ヒントを表示するコマンド")
async def hint(interaction: discord.Interaction):
    embed = discord.Embed(
        title="このbotが利用できるコマンド一覧を表示します。",
        description="/wakewake：ボイスチャンネルのメンバーを3人以上で分割して移動します\n/mezamasi：目覚ましを設定します。時間内に起きてVCに参加しましょう（寝坊したら晒し上げます）\n/flash：テキストフォーム入力式のフラッシュ暗算対戦\n/bluff_number：ブラフ数当てゲーム\n/hint：このコマンド\n/speedstar：早押し勝負を始めます\n/quiz：３択のクイズを出題します",
        color=0x00FF00,
    )
    await interaction.response.send_message(embed=embed)
