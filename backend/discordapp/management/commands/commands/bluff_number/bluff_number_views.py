import asyncio
from typing import Optional

import discord
from discord import ui

from .bluff_number_game import BluffNumberGame, GamePhase

# チャンネルID → ゲームインスタンス
active_games: dict[int, BluffNumberGame] = {}

# チャンネルID → ゲーム中にBotが送ったメッセージ一覧（削除用）
game_messages: dict[int, list[discord.Message]] = {}

TURN_TIMEOUT_SECONDS = 60


def _track_message(channel_id: int, message: discord.Message):
    """ゲーム中のBotメッセージを記録する。"""
    if channel_id not in game_messages:
        game_messages[channel_id] = []
    game_messages[channel_id].append(message)


class LobbyView(ui.View):
    """ゲーム開始前のロビー。参加ボタンを表示する。"""

    def __init__(self, game: BluffNumberGame):
        super().__init__(timeout=120)
        self.game = game

    @ui.button(label="参加する", style=discord.ButtonStyle.primary)
    async def join_button(self, interaction: discord.Interaction, button: ui.Button):
        success, msg = self.game.add_player(
            interaction.user.id, interaction.user.display_name
        )
        if not success:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        embed = self._build_lobby_embed()

        if self.game.can_start():
            self.stop()
            self.game.start_game()
            await interaction.response.edit_message(embed=embed, view=None)
            await send_round_start(interaction.channel, self.game)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    def _build_lobby_embed(self) -> discord.Embed:
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
        player_list = "\n".join(
            f"{i + 1}. {p.display_name}" for i, p in enumerate(self.game.players)
        ) or "まだ誰も参加していません"
        embed.add_field(
            name=f"参加者 ({len(self.game.players)}/3)",
            value=player_list,
            inline=False,
        )
        embed.set_footer(text="3人揃うと自動的にゲームが開始されます")
        return embed

    async def on_timeout(self):
        if self.game.channel_id in active_games:
            del active_games[self.game.channel_id]


class SecretNumberView(ui.View):
    """秘密の数字を確認するためのボタン。"""

    def __init__(self, game: BluffNumberGame):
        super().__init__(timeout=300)
        self.game = game

    @ui.button(label="秘密の数字を見る", style=discord.ButtonStyle.secondary, emoji="\U0001f440")
    async def see_number(self, interaction: discord.Interaction, button: ui.Button):
        player = next(
            (p for p in self.game.players if p.user_id == interaction.user.id), None
        )
        if player is None:
            await interaction.response.send_message(
                "あなたはこのゲームの参加者ではありません。", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"あなたの秘密の数字は **{player.secret_number}** です。",
            ephemeral=True,
        )


def _build_action_embed(game: BluffNumberGame) -> discord.Embed:
    """ターンプレイヤーに表示するアクション用Embed。"""
    embed = discord.Embed(
        title="\U0001f3af あなたのターン",
        color=0xF39C12,
    )
    if game.current_round.current_declaration > 0:
        declarator = game.players[game.current_round.declaring_player_index]
        embed.description = (
            f"現在の宣言: **合計 {game.current_round.current_declaration} 以上**"
            f" (by {declarator.display_name})\n\n"
            "宣言するか、チャレンジしてください。"
        )
    else:
        embed.description = "最初の宣言をしてください。"
    return embed


class TurnWaitView(ui.View):
    """チャンネルに表示する待機用View。ターンプレイヤーだけがボタンを押せる。"""

    def __init__(self, game: BluffNumberGame, channel):
        super().__init__(timeout=TURN_TIMEOUT_SECONDS)
        self.game = game
        self.channel = channel
        self.message: Optional[discord.Message] = None
        self.acted = False

    @ui.button(label="アクションする", style=discord.ButtonStyle.primary)
    async def action_button(self, interaction: discord.Interaction, button: ui.Button):
        current_player = self.game.get_current_turn_player()
        if interaction.user.id != current_player.user_id:
            await interaction.response.send_message(
                f"今は {current_player.display_name} のターンです。",
                ephemeral=True,
            )
            return

        if self.acted:
            await interaction.response.send_message(
                "既にアクション画面を開いています。", ephemeral=True
            )
            return
        self.acted = True

        action_view = TurnActionView(self.game, self.channel, self)
        embed = _build_action_embed(self.game)
        await interaction.response.send_message(
            embed=embed, view=action_view, ephemeral=True
        )

    async def on_timeout(self):
        if self.acted:
            return

        timeout_msg = self.game.timeout_current_player()
        embed = discord.Embed(
            title="\u23f0 タイムアウト",
            description=timeout_msg,
            color=0x95A5A6,
        )
        embed.add_field(
            name="\U0001f4ca 現在のスコア",
            value=self.game.get_scoreboard(),
            inline=False,
        )
        if self.message:
            await self.message.edit(embed=embed, view=None)

        await asyncio.sleep(3)
        continues = self.game.advance_to_next_round_or_end()
        if continues:
            await send_round_start(self.channel, self.game)
        else:
            await send_game_over(self.channel, self.game)


class DeclarationSelect(ui.Select):
    """宣言値を選ぶドロップダウン。"""

    def __init__(self, game: BluffNumberGame):
        self.game = game
        min_val = game.get_min_declaration()
        max_val = game.get_max_declaration()
        options = []
        for v in range(min_val, min(min_val + 25, max_val + 1)):
            options.append(discord.SelectOption(label=str(v), value=str(v)))
        super().__init__(
            placeholder=f"宣言する数を選択 ({min_val}〜{min(min_val + 24, max_val)})",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        declared_value = int(self.values[0])
        success, msg = self.game.make_declaration(interaction.user.id, declared_value)
        if not success:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        self.view.stop()
        self.view.wait_view.stop()

        # ephemeralメッセージを更新（本人のみ）
        await interaction.response.edit_message(
            content="宣言しました！", embed=None, view=None
        )

        # チャンネルの待機メッセージを宣言結果に更新
        embed = discord.Embed(
            title="\U0001f4e3 宣言",
            description=msg,
            color=0x3498DB,
        )
        if self.view.wait_view.message:
            await self.view.wait_view.message.edit(
                content=None, embed=embed, view=None
            )

        await send_turn_view(interaction.channel, self.game)


class TurnActionView(ui.View):
    """ターンプレイヤーにephemeralで表示するアクションView。"""

    def __init__(self, game: BluffNumberGame, channel, wait_view: TurnWaitView):
        super().__init__(timeout=TURN_TIMEOUT_SECONDS)
        self.game = game
        self.channel = channel
        self.wait_view = wait_view

        self.add_item(DeclarationSelect(game))

        challenge_btn = ui.Button(
            label="チャレンジ！",
            style=discord.ButtonStyle.danger,
            disabled=not game.can_challenge(),
            row=1,
        )
        challenge_btn.callback = self.challenge_callback
        self.add_item(challenge_btn)

    async def challenge_callback(self, interaction: discord.Interaction):
        success, msg, loser, winner = self.game.make_challenge(interaction.user.id)
        if not success:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        self.stop()
        self.wait_view.stop()

        # ephemeralメッセージを更新（本人のみ）
        await interaction.response.edit_message(
            content="チャレンジしました！", embed=None, view=None
        )

        # チャンネルにチャレンジ結果を表示
        embed = discord.Embed(
            title="\u26a1 チャレンジ結果",
            description=msg,
            color=0xE74C3C,
        )
        embed.add_field(
            name="\U0001f4ca 現在のスコア",
            value=self.game.get_scoreboard(),
            inline=False,
        )
        if self.wait_view.message:
            await self.wait_view.message.edit(
                content=None, embed=embed, view=None
            )

        await asyncio.sleep(3)
        continues = self.game.advance_to_next_round_or_end()
        if continues:
            await send_round_start(self.channel, self.game)
        else:
            await send_game_over(self.channel, self.game)


async def send_round_start(channel, game: BluffNumberGame):
    """ラウンド開始時の処理。秘密の数字確認ボタンを表示し、ターンを開始する。"""
    embed = discord.Embed(
        title=f"\U0001f3b2 ラウンド {game.current_round.round_number}/{game.MAX_ROUNDS}",
        description="各プレイヤーに秘密の数字が配られました！",
        color=0x2ECC71,
    )
    embed.add_field(
        name="\U0001f4ca 現在のスコア",
        value=game.get_scoreboard(),
        inline=False,
    )
    msg1 = await channel.send(embed=embed)
    _track_message(game.channel_id, msg1)

    secret_view = SecretNumberView(game)
    msg2 = await channel.send(
        "\U0001f522 下のボタンを押して自分の秘密の数字を確認してください。",
        view=secret_view,
    )
    _track_message(game.channel_id, msg2)

    await asyncio.sleep(3)
    await send_turn_view(channel, game)


async def send_turn_view(channel, game: BluffNumberGame):
    """ターンUIを送信する。チャンネルには待機メッセージのみ表示。"""
    current_player = game.get_current_turn_player()
    embed = discord.Embed(
        title=f"\U0001f3af {current_player.display_name} のターン",
        description=f"{current_player.display_name} がアクションを選択中...",
        color=0xF39C12,
    )
    if game.current_round.current_declaration > 0:
        declarator = game.players[game.current_round.declaring_player_index]
        embed.add_field(
            name="現在の宣言",
            value=f"**合計 {game.current_round.current_declaration} 以上** (by {declarator.display_name})",
            inline=False,
        )
    embed.set_footer(text=f"\u23f0 {TURN_TIMEOUT_SECONDS}秒以内にアクションしてください")

    view = TurnWaitView(game, channel)
    msg = await channel.send(embed=embed, view=view)
    view.message = msg
    _track_message(game.channel_id, msg)


async def send_game_over(channel, game: BluffNumberGame):
    """ゲーム中のログを削除し、まとめを投稿してクリーンアップ。"""
    # ゲーム中のBotメッセージを一括削除
    messages = game_messages.pop(game.channel_id, [])
    for msg in messages:
        try:
            await msg.delete()
        except discord.NotFound:
            pass

    # まとめを1つの投稿にまとめる
    embed = discord.Embed(
        title="\U0001f3b2 ブラフナンバー - ゲーム結果",
        description=game.get_game_summary(),
        color=0xFFD700,
    )
    await channel.send(embed=embed)

    if game.channel_id in active_games:
        del active_games[game.channel_id]