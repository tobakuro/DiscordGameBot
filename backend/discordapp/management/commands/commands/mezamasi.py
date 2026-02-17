import discord
from discord import app_commands
import asyncio
import json
import os
from datetime import datetime, timedelta

# --- データ保存用 ---
DATA_FILE = "morning_stats.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"losses": {}, "predictions": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_stats(user_id, user_name, stat_type):
    data = load_data()
    uid = str(user_id)
    if uid not in data[stat_type]:
        data[stat_type][uid] = {"name": user_name, "count": 0}
    data[stat_type][uid]["count"] += 1
    data[stat_type][uid]["name"] = user_name
    save_data(data)

# --- 予想用ボタンUI ---
class PredictionView(discord.ui.View):
    def __init__(self, timeout_seconds):
        super().__init__(timeout=timeout_seconds)
        self.votes = {"wakeup": [], "sleep": []}

    @discord.ui.button(label="起きる！", style=discord.ButtonStyle.green)
    async def predict_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.votes["wakeup"] and interaction.user not in self.votes["sleep"]:
            self.votes["wakeup"].append(interaction.user)
            await interaction.response.send_message("「起きる」に賭けました！", ephemeral=True)
        else:
            await interaction.response.send_message("既に投票済みです。", ephemeral=True)

    @discord.ui.button(label="寝坊する", style=discord.ButtonStyle.red)
    async def predict_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.votes["wakeup"] and interaction.user not in self.votes["sleep"]:
            self.votes["sleep"].append(interaction.user)
            await interaction.response.send_message("「寝坊」に賭けました！", ephemeral=True)
        else:
            await interaction.response.send_message("既に投票済みです。", ephemeral=True)

# --- 実行メインロジック ---
async def start_morning_mission(interaction, target_time_str):
    channel = interaction.channel
    now = datetime.now()
    try:
        t = datetime.strptime(target_time_str, "%H:%M")
    except ValueError:
        return

    target_dt = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
    if target_dt < now: target_dt += timedelta(days=1)

    has_woken_up = False
    member = interaction.user
    
    # 判定終了（設定1分後）までの時間を計算
    end_time = target_dt + timedelta(minutes=1)
    view_timeout = (end_time - now).total_seconds()
    
    view = PredictionView(timeout_seconds=view_timeout)
    await channel.send(
        f"📊 **予想受付開始！**\n{member.mention} さんが **{target_time_str}** までに起きられるか予想してください！\n（判定：設定5分前から1分後の間）",
        view=view
    )

    # --- 監視ループ ---
    while datetime.now() < end_time:
        current_now = datetime.now()
        diff = (target_dt - current_now).total_seconds()
        
        # DM通知
        if 299 < diff <= 300:
            try: await member.send(f"⏰ あと5分です！そろそろVCに入りましょう。")
            except: pass
        elif 59 < diff <= 60:
            try: await member.send(f"⏰ あと1分！ラストスパートです！")
            except: pass
        elif -1 < diff <= 0:
            try: await member.send(f"⏰ 設定時刻の {target_time_str} です！")
            except: pass

        # 起床判定 (5分前から1分後までVCをチェック)
        if current_now >= (target_dt - timedelta(minutes=5)):
            if member.voice:
                has_woken_up = True
        
        await asyncio.sleep(1)

    # --- 最終判定と特大晒し（ここを統合しました） ---
    winners = []
    losers = []
    
    if not has_woken_up:
        # 【寝坊確定時】
        add_stats(member.id, member.display_name, "losses")
        winners = view.votes["sleep"]   # 寝坊に賭けた人が勝ち
        losers = view.votes["wakeup"]  # 起きるに賭けた人が負け
        
        data = load_data()
        count = data["losses"].get(str(member.id), {}).get("count", 0)

        # 🚨 特大晒しEmbedの構築
        embed = discord.Embed(
            title="🚨🚨🚨 【 最終宣告：寝坊確定 】 🚨🚨🚨",
            description=f"# {member.mention} の敗北\n\n設定時刻になっても、一度も姿を現しませんでした。\n## 累計不名誉記録：**{count}回**",
            color=0xff0000 # 警告の赤
        )
        
        # アイコンをデカデカと表示
        embed.set_image(url=member.display_avatar.url)
        
        # メンションのリスト作成
        winner_mentions = ", ".join([w.mention for w in winners]) if winners else "なし"
        loser_mentions = ", ".join([l.mention for l in losers]) if losers else "なし"
        
        embed.add_field(name="🎯 鋭い洞察で見抜いた的中者", value=winner_mentions, inline=False)
        embed.add_field(name="🤡 甘い期待を抱いてしまった敗北者", value=loser_mentions, inline=False)
        embed.set_footer(text="サーバーの皆さんは、彼（彼女）を温かい目で見守ってあげてください。")

        # 的中者（寝坊に賭けた人）に実績加算
        for winner in winners:
            add_stats(winner.id, winner.display_name, "predictions")

        await channel.send(content=f"@everyone 📢 **寝坊者報告！**", embed=embed)

    else:
        # 【起床成功時】
        winners = view.votes["wakeup"]
        
        # 的中者（起きるに賭けた人）に実績加算
        for winner in winners:
            add_stats(winner.id, winner.display_name, "predictions")

        embed = discord.Embed(
            title="☀️ 【 起床成功 】 ☀️",
            description=f"## {member.mention} 勝利の帰還\n\n見事に自分に打ち勝ち、VCへの接続が確認されました！",
            color=0x00ff00 # 成功の緑
        )
        # 成功時はアバターを右上に小さく
        embed.set_thumbnail(url=member.display_avatar.url)
        
        winner_mentions = ", ".join([w.mention for w in winners]) if winners else "なし"
        embed.add_field(name="🎯 彼を信じていた同志たち", value=winner_mentions, inline=False)
        
        await channel.send(embed=embed)

# --- モーダル & コマンド ---
class WakeUpModal(discord.ui.Modal, title='起床時間の登録'):
    time_input = discord.ui.TextInput(label='起床時刻 (例 07:30)', placeholder='07:30', min_length=5, max_length=5)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"✅ {self.time_input.value} にセットしました。判定を開始します。", ephemeral=True)
        asyncio.create_task(start_morning_mission(interaction, self.time_input.value))

@app_commands.command(name="mezamasi", description="自分の起床時間をセットします")
async def mezamasi(interaction: discord.Interaction):
    await interaction.response.send_modal(WakeUpModal())

@app_commands.command(name="ranking", description="的中王と寝坊王を表示")
async def ranking(interaction: discord.Interaction):
    data = load_data()
    embed = discord.Embed(title="📊 あささん ランキング", color=0xffa500)
    for key, label in [("predictions", "🎯 予想的中王"), ("losses", "💤 寝坊キング")]:
        sorted_list = sorted(data[key].items(), key=lambda x: x[1]['count'], reverse=True)[:3]
        text = "\n".join([f"{i+1}位: {info['name']} ({info['count']}回)" for i, (uid, info) in enumerate(sorted_list)]) or "なし"
        embed.add_field(name=label, value=text, inline=False)
    await interaction.response.send_message(embed=embed)