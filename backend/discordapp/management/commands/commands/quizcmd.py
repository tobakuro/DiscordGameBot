import asyncio
import json
import re
from typing import List, Optional

import discord
from discord import app_commands
from google import genai

from .modules import (
    quiz_result_list_request,
    quiz_result_minus_request,
    quiz_result_plus_request,
    quiz_result_retrieve_request,
)

QUESTION = {
    "question": "APIからクイズが取得できませんでした。日本の首都は？",
    "choices": ["大阪", "東京", "京都"],
    "answer": 1,
}


def generate_quiz_request() -> dict:
    client = genai.Client()
    prompt = (
        "あなたはクイズマスターです。3択クイズを出題してください。"
        "クイズは以下のJSONフォーマットで出力してください。"
        "\n{\n"
        '  "question": "クイズの問題文",\n'
        '  "choices": ["選択肢1", "選択肢2", "選択肢3"],\n'
        '  "answer": 正解の選択肢の番号（0, 1, 2のいずれか）\n'
        "}\n"
        "\n例:\n"
        '{\n  "question": "日本の首都はどこですか？",\n  "choices": ["大阪", "東京", "京都"],\n  "answer": 1\n}'
    )
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    content = response.text if hasattr(response, "text") else str(response)
    # 最初に現れる { ... } のJSON部分のみ抽出
    match = re.search(r"({[\s\S]*?})", content)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception as e:
            print(f"JSON parse error: {e}")
    return {}


class QuizView(discord.ui.View):
    def __init__(self, choices: List[str], answer_index: int):
        super().__init__(timeout=60)
        self.answered_users: set[int] = set()
        self.correct_user: Optional[discord.User] = None  # 最初の正解者のみ
        self.answer_index: int = answer_index
        self.stopped: bool = False
        for i, choice in enumerate(choices):
            self.add_item(QuizButton(label=choice, index=i, view=self))

    async def show_result(self, interaction, answer_label: str):
        for item in self.children:
            item.disabled = True
        self.stopped = True
        result_embed = discord.Embed(
            title="⏰ クイズ終了！",
            description=f"**正解:** `{answer_label}`",
            color=0x95A5A6,
        )
        if self.correct_user:
            result_embed.add_field(
                name="正解者", value=self.correct_user.mention, inline=False
            )
            quiz_result_plus_request(
                token=interaction.client.token,
                discord_id=self.correct_user.id,
                username=self.correct_user.display_name,
            )
        else:
            result_embed.add_field(name="正解者", value="該当者なし", inline=False)
        # interaction.response.edit_message()はボタン用、edit_original_response()はコマンド用
        try:
            await interaction.response.edit_message(embed=result_embed, view=self)
        except Exception:
            await interaction.edit_original_response(embed=result_embed, view=self)


class QuizButton(discord.ui.Button):
    def __init__(self, label: str, index: int, view: QuizView):
        super().__init__(label=label, style=discord.ButtonStyle.success)
        self.index = index
        self.quiz_view = view

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in self.quiz_view.answered_users:
            await interaction.response.send_message(
                "すでに回答済みです。", ephemeral=True
            )
            return
        self.quiz_view.answered_users.add(user_id)
        if self.index == self.quiz_view.answer_index:
            if not self.quiz_view.correct_user:
                self.quiz_view.correct_user = interaction.user
                await self.quiz_view.show_result(interaction, self.label)
            else:
                await interaction.response.send_message(
                    "すでに正解者が出ています。", ephemeral=True
                )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(description="❌ 不正解です。", color=0xFF0000),
                ephemeral=True,
            )
            quiz_result_minus_request(
                token=interaction.client.token,
                discord_id=interaction.user.id,
                username=interaction.user.display_name,
            )


@app_commands.command(name="quiz", description="3択クイズを出題します")
async def quiz(interaction: discord.Interaction):
    """3択クイズを出題し、60秒後に結果を表示"""
    await interaction.response.defer()
    try:
        q = await asyncio.to_thread(generate_quiz_request)
        if not q or not all(k in q for k in ("question", "choices", "answer")):
            q = QUESTION
    except Exception:
        q = QUESTION
    embed = discord.Embed(
        title="🧠 3択クイズ",
        description=f"**{q['question']}**",
        color=0x3498DB,
    )
    for i, choice in enumerate(q["choices"]):
        embed.add_field(name=f"選択肢{i+1}", value=f"`{choice}`", inline=False)
    embed.set_footer(text="60秒以内に回答してください！")
    view = QuizView(q["choices"], q["answer"])
    await interaction.followup.send(embed=embed, view=view)
    # 60秒経過時にまだ正解者がいなければ自動で終了
    await asyncio.sleep(60)
    if not view.stopped:
        await view.show_result(interaction, q["choices"][q["answer"]])


@app_commands.command(
    name="quiz-result-list", description="サーバー内のクイズ結果を表示します"
)
async def quiz_result_list(interaction: discord.Interaction):
    """サーバー内のクイズ結果を表示"""
    res = quiz_result_list_request(
        token=interaction.client.token,
        guild_id=interaction.guild.id,
        guild_name=interaction.guild.name,
    )
    if res.status_code == 200:
        data = res.json()
        embed = discord.Embed(
            title="📊 クイズ結果一覧",
            description=f"**{interaction.guild.name}** サーバーのクイズ結果",
            color=0x2ECC71,
        )
        for result in data:
            username = result.get("username", "不明なユーザー")
            correct = result.get("correct_count", 0)
            incorrect = result.get("incorrect_count", 0)
            embed.add_field(
                name=username,
                value=f"正解: {correct} / 不正解: {incorrect}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(
            "クイズ結果の取得に失敗しました。", ephemeral=True
        )


@app_commands.command(name="quiz-result", description="3択クイズの結果を表示します")
async def quiz_result(interaction: discord.Interaction):
    """ユーザーのクイズ結果を表示"""
    res = quiz_result_retrieve_request(
        token=interaction.client.token,
        discord_id=interaction.user.id,
        username=interaction.user.display_name,
    )
    if res.status_code == 200:
        data = res.json()
        correct = data.get("correct_count", 0)
        incorrect = data.get("incorrect_count", 0)
        embed = discord.Embed(
            title="📊 クイズ結果",
            description=f"**{interaction.user.display_name}** さんのクイズ結果",
            color=0x2ECC71,
        )
        embed.add_field(name="正解数", value=str(correct), inline=True)
        embed.add_field(name="不正解数", value=str(incorrect), inline=True)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(
            "クイズ結果の取得に失敗しました。", ephemeral=True
        )
