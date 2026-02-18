import discord
from discord import app_commands
import asyncio
import random
import time

# --- 募集用 View ---
class HayaoshiView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.participants = []
        self.game_started = False

    @discord.ui.button(label="参加する (0/3)", style=discord.ButtonStyle.primary)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participants:
            return await interaction.response.send_message("既に参加しています。", ephemeral=True)
        if len(self.participants) >= 3:
            return await interaction.response.send_message("定員です。", ephemeral=True)

        self.participants.append(interaction.user)
        button.label = f"参加する ({len(self.participants)}/3)"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="ゲーム開始！", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.participants:
            return await interaction.response.send_message("参加者がいません！", ephemeral=True)
        
        if self.game_started: return
        self.game_started = True

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="**まもなく開始します... 集中してください！**", view=self)

        push_view = PushButtonView(self.participants)
        msg = await interaction.followup.send("準備はいいですか？", view=push_view)
        push_view.message = msg
        
        asyncio.create_task(push_view.run_logic())

# --- 早押し本番用 View ---
class PushButtonView(discord.ui.View):
    def __init__(self, participants):
        super().__init__(timeout=30)
        self.participants = participants
        self.start_time = None
        self.results = []  # [(member, time), ...]
        self.is_active = False 
        self.dq_members = [] # お手付きした人

    @discord.ui.button(label="まだ押すな...", style=discord.ButtonStyle.danger)
    async def push_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            return await interaction.response.send_message("あなたは参加者ではありません。", ephemeral=True)

        if any(res[0] == interaction.user for res in self.results) or interaction.user in self.dq_members:
            return await interaction.response.send_message("あなたは既にアクション済みです。", ephemeral=True)

        if not self.is_active:
            self.dq_members.append(interaction.user)
            await interaction.response.send_message(f"🚨 {interaction.user.display_name} がお手付き！失格です！", ephemeral=False)
            await self.check_all_finished()
            return

        elapsed = time.time() - self.start_time
        self.results.append((interaction.user, elapsed))
        await interaction.response.send_message(f"✅ {len(self.results)}番目にPUSH！ ({elapsed:.3f}秒)", ephemeral=True)
        await self.check_all_finished()

    async def check_all_finished(self):
        total_acted = len(self.results) + len(self.dq_members)
        if total_acted >= len(self.participants):
            await self.show_final_results()

    async def run_logic(self):
        wait_time = random.uniform(3.0, 7.0)
        await asyncio.sleep(wait_time)

        self.is_active = True
        self.start_time = time.time()
        
        self.push_button.style = discord.ButtonStyle.success
        self.push_button.label = "今だ！！押せ！！"
        await self.message.edit(content="🔥 **GO!!!** 🔥", view=self)
        
        await asyncio.sleep(30)
        if len(self.results) + len(self.dq_members) < len(self.participants):
            await self.show_final_results()

    async def show_final_results(self):
        if self.push_button.disabled: return 
        self.stop()

        self.push_button.disabled = True
        self.push_button.label = "終了"
        await self.message.edit(view=self)

        embed = discord.Embed(title="🏁 早押し順位発表！", color=0xFFD700)
        ranking_text = ""
        for i, (member, elapsed) in enumerate(self.results, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}位")
            ranking_text += f"{medal} **{member.display_name}**: `{elapsed:.3f}秒` \n"
        
        if not self.results:
            ranking_text = "完走者なし\n"

        if self.dq_members:
            dq_text = ", ".join([m.display_name for m in self.dq_members])
            embed.add_field(name="🚨 失格（お手付き）", value=dq_text, inline=False)

        acted_ids = [r[0].id for r in self.results] + [d.id for d in self.dq_members]
        timeout_members = [m for m in self.participants if m.id not in acted_ids]
        if timeout_members:
            tm_text = ", ".join([m.display_name for m in timeout_members])
            embed.add_field(name="💤 タイムアウト", value=tm_text, inline=False)

        embed.description = ranking_text
        await self.message.channel.send(embed=embed)

# --- ここが足りなかった部分です：コマンド定義 ---
@app_commands.command(name="speedstar", description="早押しゲームを開始します（最大3人）")
async def speedstar(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ 早押しスピードスター ⚡",
        description="参加ボタンを押してください。人数が揃うか、「開始」を押すと始まります。",
        color=0x00FF00,
    )
    view = HayaoshiView()
    await interaction.response.send_message(embed=embed, view=view)