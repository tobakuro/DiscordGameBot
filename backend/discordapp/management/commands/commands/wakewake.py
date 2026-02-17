import discord
from discord import app_commands


@app_commands.command(
    name="wakewake",
    description="ボイスチャンネルのメンバーを3人以上で分割して移動します",
)
async def wake1(interaction: discord.Interaction):
    user = interaction.user
    if not user.voice or not user.voice.channel:
        await interaction.response.send_message(
            "ボイスチャンネルに参加してから実行してください。", ephemeral=True
        )
        return

    src_channel = user.voice.channel
    members = [m for m in src_channel.members if not m.bot]
    n = len(members)
    if n < 6:
        await interaction.response.send_message(
            "6人以上のメンバーが必要です。", ephemeral=True
        )
        return

    # 3人以上のグループで分割し、1グループ3人未満にならないようにする
    # 例: 6→[3,3], 7→[4,3], 8→[4,4], 9→[3,3,3], 10→[4,3,3], ...
    groups = []
    rest = n
    idx = 0
    sorted_members = members.copy()
    while rest >= 3:
        if rest in (3, 4, 5):
            groups.append(sorted_members[idx : idx + rest])
            rest = 0
            idx += rest
        else:
            groups.append(sorted_members[idx : idx + 3])
            rest -= 3
            idx += 3
    # すべてのグループが3人以上かチェック
    if any(len(g) < 3 for g in groups):
        await interaction.response.send_message(
            "全てのグループが3人以上になるように分割できません。", ephemeral=True
        )
        return

    # サーバー内の他のボイスチャンネルを取得（src_channel以外）
    guild = interaction.guild
    voice_channels = [ch for ch in guild.voice_channels if ch != src_channel]

    if len(voice_channels) < len(groups):
        await interaction.response.send_message(
            "十分な空きボイスチャンネルがありません。", ephemeral=True
        )
        return

    # 各グループを別のチャンネルへ移動
    for group, dest_channel in zip(groups, voice_channels):
        for member in group:
            await member.move_to(dest_channel)

    await interaction.response.send_message(
        "メンバーを分割して移動しました。", ephemeral=True
    )