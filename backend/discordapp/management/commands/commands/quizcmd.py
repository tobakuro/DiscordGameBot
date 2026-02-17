import asyncio
import random
from typing import Dict, List, Optional

import discord
from discord import app_commands

QUESTIONS: List[Dict] = [
    {
        "question": "日本の首都は？",
        "choices": ["大阪", "東京", "京都"],
        "answer": 1,
    },
    {
        "question": "Pythonのロゴの色は？",
        "choices": ["赤と青", "青と黄", "緑と黒"],
        "answer": 1,
    },
    # ...他の問題...
]


class QuizView(discord.ui.View):
    def __init__(self, choices: List[str], answer_index: int):
        super().__init__(timeout=60)  # 60秒でViewが無効化
        self.answered_users: set[int] = set()
        self.correct_users: list[discord.User] = []  # 正解者の順番記録
        self.answer_index: int = answer_index
        self.stopped: bool = False
        for i, choice in enumerate(choices):
            self.add_item(QuizButton(label=choice, index=i, view=self))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        self.stopped = True


class QuizButton(discord.ui.Button):
    def __init__(self, label: str, index: int, view: QuizView):
        super().__init__(label=label, style=discord.ButtonStyle.success)
        self.index = index
        self.quiz_view = view

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in self.quiz_view.answered_users:
            # 既に回答済み
            if self.index == self.quiz_view.answer_index:
                # 正解ボタンを再度押した場合は順位を表示
                if interaction.user in self.quiz_view.correct_users:
                    rank = self.quiz_view.correct_users.index(interaction.user) + 1
                    await interaction.response.send_message(
                        f"すでに正解しています！あなたは{rank}番目の正解者です。",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        "すでに回答済みです。", ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "すでに回答済みです。", ephemeral=True
                )
            return
        self.quiz_view.answered_users.add(user_id)
        if self.index == self.quiz_view.answer_index:
            self.quiz_view.correct_users.append(interaction.user)
            rank = len(self.quiz_view.correct_users)
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"🎉 正解！あなたは{rank}番目の正解者です！",
                    color=0x00FF00,
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(description="❌ 不正解です。", color=0xFF0000),
                ephemeral=True,
            )


@app_commands.command(name="quiz", description="3択クイズを出題します")
async def quiz(interaction: discord.Interaction):
    """3択クイズを出題し、60秒後に結果を表示"""
    q = random.choice(QUESTIONS)
    embed = discord.Embed(
        title="🧠 3択クイズ",
        description=f"**{q['question']}**",
        color=0x3498DB,
    )
    for i, choice in enumerate(q["choices"]):
        embed.add_field(name=f"選択肢{i+1}", value=f"`{choice}`", inline=False)
    embed.set_footer(text="60秒以内に回答してください！")
    view = QuizView(q["choices"], q["answer"])
    await interaction.response.send_message(embed=embed, view=view)
    await asyncio.sleep(60)
    await view.on_timeout()
    # 結果表示用Embed
    result_embed = discord.Embed(
        title="⏰ クイズ終了！",
        description=f"**正解:** `{q['choices'][q['answer']]}`",
        color=0x95A5A6,
    )
    # 上位3名を表示
    if view.correct_users:
        for i, user in enumerate(view.correct_users[:3]):
            result_embed.add_field(name=f"{i+1}位", value=user.mention, inline=False)
    else:
        result_embed.add_field(name="正解者", value="該当者なし", inline=False)
    await interaction.edit_original_response(embed=result_embed, view=view)
