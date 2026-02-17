import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GamePhase(Enum):
    LOBBY = "lobby"
    TURN = "turn"
    ROUND_END = "round_end"
    GAME_OVER = "game_over"


@dataclass
class Player:
    user_id: int
    display_name: str
    score: int = 0
    secret_number: Optional[int] = None


@dataclass
class RoundLog:
    """1ラウンドの履歴。"""
    round_number: int
    secret_numbers: dict[str, int] = field(default_factory=dict)  # display_name -> number
    declarations: list[str] = field(default_factory=list)  # "A: 12以上" 形式
    result: str = ""  # チャレンジ/タイムアウト結果


@dataclass
class RoundState:
    round_number: int
    current_declaration: int = 0
    declaring_player_index: int = -1
    turn_player_index: int = 0
    turn_count: int = 0


class BluffNumberGame:
    MAX_PLAYERS = 3
    MAX_ROUNDS = 3
    MIN_NUMBER = 1
    MAX_NUMBER = 10

    def __init__(self, channel_id: int, host_user_id: int):
        self.channel_id = channel_id
        self.host_user_id = host_user_id
        self.players: list[Player] = []
        self.phase = GamePhase.LOBBY
        self.current_round: Optional[RoundState] = None
        self.round_number = 0
        self.round_logs: list[RoundLog] = []
        self._current_log: Optional[RoundLog] = None

    def add_player(self, user_id: int, display_name: str) -> tuple[bool, str]:
        if self.phase != GamePhase.LOBBY:
            return False, "ゲームは既に開始されています。"
        if any(p.user_id == user_id for p in self.players):
            return False, "既に参加しています。"
        if len(self.players) >= self.MAX_PLAYERS:
            return False, "プレイヤーは3人までです。"
        self.players.append(Player(user_id=user_id, display_name=display_name))
        return True, f"{display_name} が参加しました！ ({len(self.players)}/{self.MAX_PLAYERS})"

    def can_start(self) -> bool:
        return self.phase == GamePhase.LOBBY and len(self.players) == self.MAX_PLAYERS

    def start_game(self) -> None:
        self.phase = GamePhase.TURN
        self.round_number = 0
        self._start_new_round()

    def _start_new_round(self) -> None:
        self.round_number += 1
        for p in self.players:
            p.secret_number = random.randint(self.MIN_NUMBER, self.MAX_NUMBER)
        first_index = (self.round_number - 1) % self.MAX_PLAYERS
        self.current_round = RoundState(
            round_number=self.round_number,
            turn_player_index=first_index,
        )
        self._current_log = RoundLog(
            round_number=self.round_number,
            secret_numbers={p.display_name: p.secret_number for p in self.players},
        )
        self.phase = GamePhase.TURN

    def get_actual_sum(self) -> int:
        return sum(p.secret_number for p in self.players)

    def get_current_turn_player(self) -> Player:
        return self.players[self.current_round.turn_player_index]

    def get_min_declaration(self) -> int:
        if self.current_round.current_declaration == 0:
            return 3
        return self.current_round.current_declaration + 1

    def get_max_declaration(self) -> int:
        return 30

    def can_challenge(self) -> bool:
        return self.current_round.turn_count > 0

    def make_declaration(self, user_id: int, declared_value: int) -> tuple[bool, str]:
        turn_player = self.get_current_turn_player()
        if turn_player.user_id != user_id:
            return False, "あなたのターンではありません。"
        min_val = self.get_min_declaration()
        if declared_value < min_val:
            return False, f"宣言は {min_val} 以上でなければなりません。"
        if declared_value > self.get_max_declaration():
            return False, f"宣言は {self.get_max_declaration()} 以下でなければなりません。"

        self.current_round.current_declaration = declared_value
        self.current_round.declaring_player_index = self.current_round.turn_player_index
        self.current_round.turn_count += 1
        self.current_round.turn_player_index = (
            (self.current_round.turn_player_index + 1) % self.MAX_PLAYERS
        )
        self._current_log.declarations.append(
            f"{turn_player.display_name}: {declared_value}以上"
        )
        return True, f"{turn_player.display_name} が「合計は {declared_value} 以上」と宣言しました！"

    def make_challenge(self, user_id: int) -> tuple[bool, str, Optional[Player], Optional[Player]]:
        turn_player = self.get_current_turn_player()
        if turn_player.user_id != user_id:
            return False, "あなたのターンではありません。", None, None
        if not self.can_challenge():
            return False, "まだ宣言がされていません。", None, None

        actual_sum = self.get_actual_sum()
        declared = self.current_round.current_declaration
        declarator = self.players[self.current_round.declaring_player_index]
        challenger = turn_player
        numbers_str = " + ".join(str(p.secret_number) for p in self.players)

        if actual_sum < declared:
            declarator.score -= 1
            loser, winner = declarator, challenger
            result_msg = (
                f"宣言: 合計 {declared} 以上\n"
                f"実際の合計: {actual_sum} ({numbers_str})\n\n"
                f"合計が宣言より小さいため、**{challenger.display_name}** のチャレンジ成功！\n"
                f"{declarator.display_name} が -1 ポイント。"
            )
        else:
            challenger.score -= 1
            loser, winner = challenger, declarator
            result_msg = (
                f"宣言: 合計 {declared} 以上\n"
                f"実際の合計: {actual_sum} ({numbers_str})\n\n"
                f"合計が宣言以上のため、**{declarator.display_name}** の宣言は正しかった！\n"
                f"{challenger.display_name} が -1 ポイント。"
            )

        self.phase = GamePhase.ROUND_END
        self._current_log.declarations.append(
            f"{challenger.display_name}: チャレンジ！"
        )
        if actual_sum < declared:
            self._current_log.result = f"チャレンジ成功！ {declarator.display_name} -1点"
        else:
            self._current_log.result = f"チャレンジ失敗！ {challenger.display_name} -1点"
        self.round_logs.append(self._current_log)
        return True, result_msg, loser, winner

    def timeout_current_player(self) -> str:
        current_player = self.get_current_turn_player()
        current_player.score -= 1
        self.phase = GamePhase.ROUND_END
        self._current_log.result = f"タイムアウト！ {current_player.display_name} -1点"
        self.round_logs.append(self._current_log)
        return (
            f"{current_player.display_name} が時間切れ！\n"
            f"{current_player.display_name} が -1 ポイント。"
        )

    def advance_to_next_round_or_end(self) -> bool:
        if self.round_number >= self.MAX_ROUNDS:
            self.phase = GamePhase.GAME_OVER
            return False
        self._start_new_round()
        return True

    def get_scoreboard(self) -> str:
        sorted_players = sorted(self.players, key=lambda p: p.score, reverse=True)
        lines = []
        for i, p in enumerate(sorted_players, 1):
            lines.append(f"{i}. {p.display_name}: {p.score} ポイント")
        return "\n".join(lines)

    def get_final_results(self) -> str:
        sorted_players = sorted(self.players, key=lambda p: p.score, reverse=True)
        winner = sorted_players[0]
        medals = ["\U0001f947", "\U0001f948", "\U0001f949"]
        lines = [f"優勝: **{winner.display_name}**！\n"]
        for i, p in enumerate(sorted_players):
            lines.append(f"{medals[i]} {p.display_name}: {p.score} ポイント")
        return "\n".join(lines)

    def get_game_summary(self) -> str:
        """ゲーム全体のまとめを生成する。"""
        lines = []
        for log in self.round_logs:
            numbers = " / ".join(
                f"{name}:{num}" for name, num in log.secret_numbers.items()
            )
            actual_sum = sum(log.secret_numbers.values())
            lines.append(f"**--- ラウンド {log.round_number} ---**")
            lines.append(f"数字: {numbers} (合計: {actual_sum})")
            lines.append(" \u2192 ".join(log.declarations))
            lines.append(f"**{log.result}**")
            lines.append("")

        sorted_players = sorted(self.players, key=lambda p: p.score, reverse=True)
        medals = ["\U0001f947", "\U0001f948", "\U0001f949"]
        lines.append("**--- 最終結果 ---**")
        for i, p in enumerate(sorted_players):
            lines.append(f"{medals[i]} {p.display_name}: {p.score} ポイント")
        return "\n".join(lines)
