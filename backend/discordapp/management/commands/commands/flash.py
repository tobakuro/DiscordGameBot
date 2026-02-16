import discord
from discord import app_commands
import asyncio
import random

# --- テンキーUI部分の定義 ---
class TenkeyView(discord.ui.View):
    def __init__(self, total, user, timeout=20.0):
        super().__init__(timeout=timeout)
        self.total = total
        self.user = user
        self.current_input = ""

    async def update_message(self, interaction: discord.Interaction):
        # 他のユーザーがボタンを押しても反応しないように制限
        if interaction.user != self.user:
            await interaction.response.send_message("これはあなたのゲームではありません！", ephemeral=True)
            return

        display = self.current_input if self.current_input else "？"
        await interaction.response.edit_message(
            content=f"答えを入力してください：\n# 　{display}　", 
            view=self
        )

    # 数字ボタン (0-9)
    @discord.ui.button(label="1", row=0, style=discord.ButtonStyle.secondary)
    async def btn1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "1"
        await self.update_message(interaction)

    @discord.ui.button(label="2", row=0, style=discord.ButtonStyle.secondary)
    async def btn2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "2"
        await self.update_message(interaction)

    @discord.ui.button(label="3", row=0, style=discord.ButtonStyle.secondary)
    async def btn3(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "3"
        await self.update_message(interaction)

    @discord.ui.button(label="4", row=1, style=discord.ButtonStyle.secondary)
    async def btn4(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "4"
        await self.update_message(interaction)

    @discord.ui.button(label="5", row=1, style=discord.ButtonStyle.secondary)
    async def btn5(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "5"
        await self.update_message(interaction)

    @discord.ui.button(label="6", row=1, style=discord.ButtonStyle.secondary)
    async def btn6(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "6"
        await self.update_message(interaction)

    @discord.ui.button(label="7", row=2, style=discord.ButtonStyle.secondary)
    async def btn7(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "7"
        await self.update_message(interaction)

    @discord.ui.button(label="8", row=2, style=discord.ButtonStyle.secondary)
    async def btn8(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "8"
        await self.update_message(interaction)

    @discord.ui.button(label="9", row=2, style=discord.ButtonStyle.secondary)
    async def btn9(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "9"
        await self.update_message(interaction)

    @discord.ui.button(label="DEL", row=3, style=discord.ButtonStyle.danger)
    async def btn_del(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input = self.current_input[:-1]
        await self.update_message(interaction)

    @discord.ui.button(label="0", row=3, style=discord.ButtonStyle.secondary)
    async def btn0(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_input += "0"
        await self.update_message(interaction)

    @discord.ui.button(label="決定", row=3, style=discord.ButtonStyle.success)
    async def btn_enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("これはあなたのゲームではありません！", ephemeral=True)
            return
            
        if not self.current_input:
            await interaction.response.send_message("数字を入力してください", ephemeral=True)
            return
        
        is_correct = int(self.current_input) == self.total
        if is_correct:
            await interaction.response.edit_message(content=f"✅ **正解！**\n答えは **{self.total}** でした！", view=None)
        else:
            await interaction.response.edit_message(content=f"❌ **残念！**\n正解は **{self.total}** でした。（あなたの回答: {self.current_input}）", view=None)
        self.stop()

    # タイムアウト時の処理
    async def on_timeout(self):
        # 注意: ここでは interaction が取れないため、元のメッセージを更新するには工夫が必要ですが、
        # 一般的にはViewを無効化するのみでOKです。
        pass

# --- メインコマンド部分 ---
@app_commands.command(name="flash", description="フラッシュ暗算を開始します")
@app_commands.describe(
    digits="桁数 (1-5)",
    count="数字の個数 (3-20)",
    speed="表示スピード（秒）"
)
async def flash1(interaction: discord.Interaction, digits: int = 2, count: int = 5, speed: float = 1.0):
    # 範囲制限
    digits = max(1, min(digits, 5))
    count = max(3, min(count, 20))
    speed = max(0.3, speed)

    numbers = [random.randint(10**(digits-1), (10**digits)-1) for _ in range(count)]
    total = sum(numbers)

    # 最初の応答
    await interaction.response.send_message("準備はいいですか？ 3秒後に開始します...")
    msg = await interaction.original_response()
    await asyncio.sleep(3)

    # フラッシュ表示ループ
    for num in numbers:
        await msg.edit(content=f"# 　{num}　")
        await asyncio.sleep(speed)
        await msg.edit(content="# 　 　") 
        await asyncio.sleep(0.1)

    # テンキーViewを表示
    # ここで wait_for(message) を使わず、ボタンによるコールバックに移行します
    view = TenkeyView(total=total, user=interaction.user)
    await msg.edit(content="答えを入力してください：\n# 　？　", view=view)