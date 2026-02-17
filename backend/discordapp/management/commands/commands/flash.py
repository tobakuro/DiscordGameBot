import discord
from discord import app_commands
import asyncio
import random

# --- 1. 個別回答用テンキーUI (本人にしか見えないエフェメラル用) ---
class MultiTenkeyView(discord.ui.View):
    def __init__(self, total, user, timeout=30.0):
        super().__init__(timeout=timeout)
        self.total = total
        self.user = user
        self.answer = ""
        self.submitted = False

    async def update_message(self, it: discord.Interaction):
        display = self.answer if self.answer else "？"
        await it.response.edit_message(content=f"あなたの回答を入力中: `{display}`", view=self)

    # 数字ボタン配置 (Row 0-2: 1-9, Row 3: CLEAR, 0, ENTER)
    @discord.ui.button(label="1", row=0)
    async def btn1(self, it, btn): self.answer += "1"; await self.update_message(it)
    @discord.ui.button(label="2", row=0)
    async def btn2(self, it, btn): self.answer += "2"; await self.update_message(it)
    @discord.ui.button(label="3", row=0)
    async def btn3(self, it, btn): self.answer += "3"; await self.update_message(it)
    @discord.ui.button(label="4", row=1)
    async def btn4(self, it, btn): self.answer += "4"; await self.update_message(it)
    @discord.ui.button(label="5", row=1)
    async def btn5(self, it, btn): self.answer += "5"; await self.update_message(it)
    @discord.ui.button(label="6", row=1)
    async def btn6(self, it, btn): self.answer += "6"; await self.update_message(it)
    @discord.ui.button(label="7", row=2)
    async def btn7(self, it, btn): self.answer += "7"; await self.update_message(it)
    @discord.ui.button(label="8", row=2)
    async def btn8(self, it, btn): self.answer += "8"; await self.update_message(it)
    @discord.ui.button(label="9", row=2)
    async def btn9(self, it, btn): self.answer += "9"; await self.update_message(it)
    @discord.ui.button(label="0", row=3)
    async def btn0(self, it, btn): self.answer += "0"; await self.update_message(it)
    
    @discord.ui.button(label="CLEAR", row=3, style=discord.ButtonStyle.danger)
    async def btn_cl(self, it, btn): self.answer = ""; await self.update_message(it)

    @discord.ui.button(label="決定", row=3, style=discord.ButtonStyle.success)
    async def btn_ent(self, it, btn):
        self.submitted = True
        await it.response.edit_message(content=f"✅ 回答 `{self.answer}` を送信しました！", view=None)
        self.stop()

# --- 2. 回答ポータル (全員が見える場所に表示) ---
class AnswerPortalView(discord.ui.View):
    def __init__(self, participants, total):
        super().__init__(timeout=30.0)
        self.participants = participants
        self.total = total
        self.user_answers = {} # {user_id: answer_text}

    @discord.ui.button(label="回答を入力する", style=discord.ButtonStyle.primary, emoji="⌨️")
    async def open_keypad(self, it: discord.Interaction, btn: discord.ui.Button):
        # 参加者かどうかIDでチェック
        is_participant = any(u.id == it.user.id for u in self.participants)
        if not is_participant:
            await it.response.send_message("あなたは今回の対戦に参加していません。", ephemeral=True)
            return
        
        if it.user.id in self.user_answers:
            await it.response.send_message("既に回答を送信済みです。", ephemeral=True)
            return

        # ボタンを押した本人専用のテンキーを表示
        view = MultiTenkeyView(total=self.total, user=it.user)
        await it.response.send_message("制限時間内に回答を入力してください：", view=view, ephemeral=True)
        
        await view.wait()
        if view.submitted:
            self.user_answers[it.user.id] = view.answer

# --- 3. 設定 ＆ 参加受付 View ---
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
            embed = discord.Embed(title="⚙️ フラッシュ暗算：難易度設定", color=discord.Color.blue())
            embed.description = f"ホスト: {self.owner.mention}\n設定を調整して「募集開始」を押してください。"
            embed.add_field(name="🔢 桁数", value=f"**{self.digits}** 桁", inline=True)
            embed.add_field(name="📦 個数", value=f"**{self.count}** 個", inline=True)
            embed.add_field(name="⚡ 速度", value=f"**{self.speed:.1f}** 秒", inline=True)
            return embed
        else:
            names = "\n".join([f"・{u.display_name}" for u in self.participants]) or "（待機中...）"
            embed = discord.Embed(title="⚔️ 参加者募集中！", color=discord.Color.orange())
            embed.description = f"**{self.required_players}人**集まったら自動で開始します。\n難易度: `{self.digits}桁 / {self.count}個 / {self.speed}s`"
            embed.add_field(name=f"参加者 ({len(self.participants)}/{self.required_players})", value=names)
            return embed

    # --- 設定ボタン群 ---
    @discord.ui.button(label="桁数 ＋", row=0, style=discord.ButtonStyle.secondary)
    async def d_up(self, it, b): self.digits = min(5, self.digits + 1); await it.response.edit_message(embed=self.make_embed())
    @discord.ui.button(label="桁数 －", row=0, style=discord.ButtonStyle.secondary)
    async def d_down(self, it, b): self.digits = max(1, self.digits - 1); await it.response.edit_message(embed=self.make_embed())

    @discord.ui.button(label="個数 ＋", row=1, style=discord.ButtonStyle.secondary)
    async def c_up(self, it, b): self.count = min(20, self.count + 1); await it.response.edit_message(embed=self.make_embed())
    @discord.ui.button(label="個数 －", row=1, style=discord.ButtonStyle.secondary)
    async def c_down(self, it, b): self.count = max(3, self.count - 1); await it.response.edit_message(embed=self.make_embed())

    @discord.ui.button(label="速度 ＋ (遅)", row=2, style=discord.ButtonStyle.secondary)
    async def s_up(self, it, b): self.speed = min(3.0, self.speed + 0.1); await it.response.edit_message(embed=self.make_embed())
    @discord.ui.button(label="速度 － (速)", row=2, style=discord.ButtonStyle.secondary)
    async def s_down(self, it, b): self.speed = max(0.2, self.speed - 0.1); await it.response.edit_message(embed=self.make_embed())
    
    @discord.ui.button(label="🚀 募集開始", row=3, style=discord.ButtonStyle.success)
    async def start_recruit(self, it, b):
        if it.user != self.owner:
            await it.response.send_message("ホストのみ設定可能です。", ephemeral=True)
            return
        self.is_recruiting = True
        self.clear_items()
        btn = discord.ui.Button(label="参加する！", style=discord.ButtonStyle.primary, emoji="🙋")
        btn.callback = self.join_callback
        self.add_item(btn)
        await it.response.edit_message(embed=self.make_embed(), view=self)

    async def join_callback(self, it: discord.Interaction):
        if any(u.id == it.user.id for u in self.participants):
            await it.response.send_message("既に参加しています。", ephemeral=True)
            return
        
        self.participants.append(it.user)
        if len(self.participants) >= self.required_players:
            await it.response.edit_message(embed=self.make_embed(), view=None)
            self.stop()
        else:
            await it.response.edit_message(embed=self.make_embed(), view=self)

# --- 4. メインコマンド /flash ---
@app_commands.command(name="flash", description="設定・募集を行ってみんなでフラッシュ暗算対戦！")
async def flash(interaction: discord.Interaction):
    # 【ステップ1】設定 ＆ 募集
    view = SetupAndJoinView(owner=interaction.user, required_players=3)
    await interaction.response.send_message(embed=view.make_embed(), view=view)
    
    # 募集完了を待機
    await view.wait()

    if len(view.participants) < view.required_players:
        return # 募集人数に満たずタイムアウトした場合など

    # 【ステップ2】ゲーム開始準備
    msg = await interaction.original_response()
    numbers = [random.randint(10**(view.digits-1), (10**view.digits)-1) for _ in range(view.count)]
    total = sum(numbers)

    await msg.edit(content="🔥 **メンバー確定！対戦を開始します...**", embed=None, view=None)
    await asyncio.sleep(2)

    for i in range(3, 0, -1):
        await msg.edit(content=f"READY... **{i}**")
        await asyncio.sleep(1)

    # 【ステップ3】フラッシュ表示
    for num in numbers:
        await msg.edit(content=f"# 　{num}　")
        await asyncio.sleep(view.speed)
        await msg.edit(content="# 　 　")
        await asyncio.sleep(0.05)

    # 【ステップ4】回答フェーズ (ポータル表示)
    portal = AnswerPortalView(participants=view.participants, total=total)
    await msg.edit(content="⌛ **回答時間 (25秒)！ 下のボタンを押して手元で入力してください！**", view=portal)
    
    await asyncio.sleep(25) # 回答待機時間
    portal.stop()

    # 【ステップ5】結果発表
    results = []
    for user in view.participants:
        ans = portal.user_answers.get(user.id, "未入力")
        is_correct = str(ans) == str(total)
        status = "✅ 正解！" if is_correct else "❌ 不正解"
        results.append(f"**{user.display_name}**: {status} (回答: `{ans}`)")

    res_embed = discord.Embed(title="🏆 対戦結果発表", description=f"正解は **{total}** でした！", color=discord.Color.gold())
    res_embed.add_field(name="プレイヤーの結果", value="\n".join(results) or "参加者なし")
    
    await interaction.channel.send(embed=res_embed)