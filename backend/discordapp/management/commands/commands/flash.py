import discord
from discord import app_commands
import asyncio
import random

# --- 1. 直接入力用フォーム (Modal) ---
class AnswerModal(discord.ui.Modal):
    def __init__(self, total, parent_portal):
        super().__init__(title="フラッシュ暗算：回答入力")
        self.total = total
        self.parent_portal = parent_portal
        
        # テキスト入力欄の設定
        self.answer_input = discord.ui.TextInput(
            label="計算結果を入力してください",
            placeholder="例: 123",
            min_length=1,
            max_length=10,
            required=True
        )
        self.add_item(self.answer_input)

    async def on_submit(self, it: discord.Interaction):
        val = self.answer_input.value
        # 数字かどうかチェック
        if not val.isdigit():
            await it.response.send_message("数字のみを入力してください。", ephemeral=True)
            return

        await it.response.send_message(f"✅ 回答 `{val}` を送信しました。全員の完了を待っています...", ephemeral=True)
        # 親ポータルに回答を通知
        await self.parent_portal.submit_answer(it.user.id, val)

# --- 2. 回答ポータル (Modalを呼び出すボタン) ---
class AnswerPortalView(discord.ui.View):
    def __init__(self, participants, total):
        super().__init__(timeout=45.0)
        self.participants = participants
        self.total = total
        self.user_answers = {}
        self.all_submitted_event = asyncio.Event()

    @discord.ui.button(label="回答を入力する", style=discord.ButtonStyle.primary, emoji="⌨️")
    async def open_modal(self, it: discord.Interaction, btn: discord.ui.Button):
        # 参加者チェック
        if not any(u.id == it.user.id for u in self.participants):
            await it.response.send_message("参加者ではありません。", ephemeral=True)
            return
        if it.user.id in self.user_answers:
            await it.response.send_message("既に送信済みです。", ephemeral=True)
            return

        # Modal（入力フォーム）を表示
        await it.response.send_modal(AnswerModal(total=self.total, parent_portal=self))

    async def submit_answer(self, user_id, answer):
        self.user_answers[user_id] = answer
        if len(self.user_answers) >= len(self.participants):
            self.all_submitted_event.set()

# --- 3. 設定 ＆ 参加受付 View (前回と同じ) ---
class SetupAndJoinView(discord.ui.View):
    def __init__(self, owner, required_players=3):
        super().__init__(timeout=120.0)
        self.owner = owner
        self.required_players = required_players
        self.participants = []
        self.is_recruiting = False
        self.digits, self.count, self.speed = 2, 5, 0.8

    def make_embed(self):
        if not self.is_recruiting:
            embed = discord.Embed(title="⚙️ フラッシュ暗算設定", color=0x3498db)
            embed.add_field(name="桁数", value=f"**{self.digits}** 桁", inline=True)
            embed.add_field(name="個数", value=f"**{self.count}** 個\n(※3個以上)", inline=True)
            embed.add_field(name="速度", value=f"**{self.speed:.1f}** 秒間隔", inline=True)
            return embed
        else:
            names = "\n".join([f"・{u.display_name}" for u in self.participants]) or "待機中..."
            embed = discord.Embed(title="⚔️ 参加者募集中", color=0xe67e22)
            embed.description = f"**{self.required_players}人**集まったら開始します。"
            embed.add_field(name="現在の参加者", value=names)
            embed.set_footer(text=f"難易度: {self.digits}桁 / {self.count}個(3個〜) / {self.speed}s")
            return embed

    @discord.ui.button(label="桁数＋", row=0)
    async def d_up(self, it, b): self.digits = min(5, self.digits+1); await it.response.edit_message(embed=self.make_embed())
    @discord.ui.button(label="桁数－", row=0)
    async def d_down(self, it, b): self.digits = max(1, self.digits-1); await it.response.edit_message(embed=self.make_embed())
    @discord.ui.button(label="個数＋", row=1)
    async def c_up(self, it, b): self.count = min(20, self.count+1); await it.response.edit_message(embed=self.make_embed())
    @discord.ui.button(label="個数－", row=1)
    async def c_down(self, it, b): 
        if self.count > 3:
            self.count -= 1
            await it.response.edit_message(embed=self.make_embed())
        else:
            await it.response.send_message("個数は3個以上に設定してください。", ephemeral=True)

    @discord.ui.button(label="速度＋ (遅)", row=2)
    async def s_up(self, it, b): self.speed = min(3.0, self.speed+0.1); await it.response.edit_message(embed=self.make_embed())
    @discord.ui.button(label="速度－ (速)", row=2)
    async def s_down(self, it, b): self.speed = max(0.2, self.speed-0.1); await it.response.edit_message(embed=self.make_embed())
    
    @discord.ui.button(label="🚀 募集開始", row=3, style=discord.ButtonStyle.success)
    async def start_recruit(self, it, b):
        if it.user != self.owner: return
        self.is_recruiting = True
        self.clear_items()
        btn = discord.ui.Button(label="参加する！", style=discord.ButtonStyle.primary, emoji="🙋")
        btn.callback = self.join_callback
        self.add_item(btn)
        await it.response.edit_message(embed=self.make_embed(), view=self)

    async def join_callback(self, it: discord.Interaction):
        if not any(u.id == it.user.id for u in self.participants):
            self.participants.append(it.user)
            if len(self.participants) >= self.required_players:
                self.stop()
            await it.response.edit_message(embed=self.make_embed(), view=self)
        else:
            await it.response.send_message("参加済み", ephemeral=True)

# --- 4. メインコマンド /flash ---
@app_commands.command(name="flash", description="テキストフォーム入力式のフラッシュ暗算対戦")
async def flash(interaction: discord.Interaction):
    view = SetupAndJoinView(owner=interaction.user, required_players=3)
    await interaction.response.send_message(embed=view.make_embed(), view=view)
    await view.wait()

    if len(view.participants) < view.required_players: return

    game_config = f"{view.digits}桁 / {view.count}個 / {view.speed:.1f}s"
    msg = await interaction.original_response()
    numbers = [random.randint(10**(view.digits-1), (10**view.digits)-1) for _ in range(view.count)]
    total = sum(numbers)

    # 演出
    for i in range(3, 0, -1):
        await msg.edit(content=f"🔥 **READY... {i}**", embed=None, view=None)
        await asyncio.sleep(1)

    # フラッシュ
    for num in numbers:
        await msg.edit(content=f"# 　{num}　")
        await asyncio.sleep(view.speed)
        await msg.edit(content="# 　 　")
        await asyncio.sleep(0.05)

    # 回答ポータル表示
    portal = AnswerPortalView(participants=view.participants, total=total)
    await msg.edit(content="⌛ **全員回答してください！ 下のボタンから入力できます。**", view=portal)

    try:
        await asyncio.wait_for(portal.all_submitted_event.wait(), timeout=40.0)
    except asyncio.TimeoutError:
        pass 
    
    portal.stop()

    # リザルト
    results = []
    for user in view.participants:
        ans = portal.user_answers.get(user.id, "未入力")
        status = "✅ 正解" if str(ans) == str(total) else "❌ 不正解"
        results.append(f"**{user.display_name}**: {status} (回答: `{ans}`)")

    res_embed = discord.Embed(title="🏆 対戦結果発表", color=0xf1c40f)
    res_embed.add_field(name="📊 プレイ設定", value=f"`{game_config}`", inline=False)
    res_embed.add_field(name="🏁 正解", value=f"# **{total}**", inline=False)
    res_embed.add_field(name="👤 プレイヤー成績", value="\n".join(results), inline=False)
    
    await msg.delete() 
    await interaction.channel.send(embed=res_embed)