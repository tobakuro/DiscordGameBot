import asyncio
from typing import Optional

import discord
from discord import ui

from .bluff_number_game import BluffNumberGame, GamePhase

# チャンネルID → ゲームインスタンス
active_games: dict[int, BluffNumberGame] = {}

TURN_TIMEOUT_SECONDS = 60


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
                "**ルール:**\n"
                "・各プレイヤーに1〜10の秘密の数字が配られます\n"
                "・順番に「全員の合計はX以上」と宣言します\n"
                "・宣言は前の数字より大きくなければなりません\n"
                "・チャレンジで宣言が正しいか確認できます\n"
                "・3ラウンド行い、最もポイントが高い人の勝ちです\n"
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

        embed = discord.Embed(
            title="\U0001f4e3 宣言",
            description=msg,
            color=0x3498DB,
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await send_turn_view(interaction.channel, self.game)


class TurnView(ui.View):
    """プレイヤーのターン。宣言セレクトとチャレンジボタンを表示する。"""

    def __init__(self, game: BluffNumberGame, channel):
        super().__init__(timeout=TURN_TIMEOUT_SECONDS)
        self.game = game
        self.channel = channel
        self.message: Optional[discord.Message] = None

        self.add_item(DeclarationSelect(game))

        challenge_btn = ui.Button(
            label="チャレンジ！",
            style=discord.ButtonStyle.danger,
            disabled=not game.can_challenge(),
            row=1,
        )
        challenge_btn.callback = self.challenge_callback
        self.add_item(challenge_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        current_player = self.game.get_current_turn_player()
        if interaction.user.id != current_player.user_id:
            await interaction.response.send_message(
                f"今は {current_player.display_name} のターンです。",
                ephemeral=True,
            )
            return False
        return True

    async def challenge_callback(self, interaction: discord.Interaction):
        success, msg, loser, winner = self.game.make_challenge(interaction.user.id)
        if not success:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        self.stop()

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
        await interaction.response.edit_message(embed=embed, view=None)

        await asyncio.sleep(3)
        continues = self.game.advance_to_next_round_or_end()
        if continues:
            await send_round_start(self.channel, self.game)
        else:
            await send_game_over(self.channel, self.game)

    async def on_timeout(self):
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
    await channel.send(embed=embed)

    secret_view = SecretNumberView(game)
    await channel.send(
        "\U0001f522 下のボタンを押して自分の秘密の数字を確認してください。",
        view=secret_view,
    )

    await asyncio.sleep(3)
    await send_turn_view(channel, game)


async def send_turn_view(channel, game: BluffNumberGame):
    """ターンUIを送信する。"""
    current_player = game.get_current_turn_player()
    embed = discord.Embed(
        title=f"\U0001f3af {current_player.display_name} のターン",
        color=0xF39C12,
    )
    if game.current_round.current_declaration > 0:
        declarator = game.players[game.current_round.declaring_player_index]
        embed.description = (
            f"現在の宣言: **合計 {game.current_round.current_declaration} 以上**"
            f" (by {declarator.display_name})"
        )
    else:
        embed.description = "最初の宣言をしてください。"
    embed.set_footer(text=f"\u23f0 {TURN_TIMEOUT_SECONDS}秒以内にアクションしてください")

    view = TurnView(game, channel)
    msg = await channel.send(
        content=f"{current_player.display_name} のターンです！",
        embed=embed,
        view=view,
    )
    view.message = msg


async def send_game_over(channel, game: BluffNumberGame):
    """ゲーム終了時の結果表示とクリーンアップ。"""
    embed = discord.Embed(
        title="\U0001f3c6 ゲーム終了！",
        description=game.get_final_results(),
        color=0xFFD700,
    )
    await channel.send(embed=embed)
    if game.channel_id in active_games:
        del active_games[game.channel_id]