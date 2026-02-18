from .models import (
    BluffNumberResult,
    DiscordGuild,
    DiscordUser,
    FlashResult,
    OverSleptResult,
    PredictionResult,
    QuizResult,
)


def create_or_update_discord_user(discord_id: str, username: str) -> DiscordUser:
    """DiscordUserを作成または更新する"""
    try:
        user = DiscordUser.objects.get(discord_id=discord_id)
        if user.username != username:
            user.username = username
            user.save()
    except DiscordUser.DoesNotExist:
        user = DiscordUser.objects.create(discord_id=discord_id, username=username)
    return user


def create_or_update_discord_guild(guild_id: str, name: str) -> DiscordGuild:
    """DiscordGuildを作成または更新する"""
    try:
        guild = DiscordGuild.objects.get(guild_id=guild_id)
        if guild.name != name:
            guild.name = name
            guild.save()
    except DiscordGuild.DoesNotExist:
        guild = DiscordGuild.objects.create(guild_id=guild_id, name=name)
    return guild


def create_quiz_result(user: DiscordUser) -> QuizResult:
    """QuizResultを作成または取得する"""
    try:
        quiz_result = QuizResult.objects.get(user=user)
    except QuizResult.DoesNotExist:
        quiz_result = QuizResult.objects.create(
            user=user, correct_count=0, failed_count=0
        )
    return quiz_result


def create_overslept_result(user: DiscordUser) -> OverSleptResult:
    """OverSleptResultを作成または取得する"""
    try:
        overslept_result = OverSleptResult.objects.get(user=user)
    except OverSleptResult.DoesNotExist:
        overslept_result = OverSleptResult.objects.create(user=user, overslept_count=0)
    return overslept_result


def create_prediction_result(user: DiscordUser) -> PredictionResult:
    """PredictionResultを作成または取得する"""
    try:
        prediction_result = PredictionResult.objects.get(user=user)
    except PredictionResult.DoesNotExist:
        prediction_result = PredictionResult.objects.create(
            user=user, correct_count=0, failed_count=0
        )
    return prediction_result


def create_bluff_number_result(user: DiscordUser) -> BluffNumberResult:
    """BluffNumberResultを作成または取得する"""
    try:
        bluff_number_result = BluffNumberResult.objects.get(user=user)
    except BluffNumberResult.DoesNotExist:
        bluff_number_result = BluffNumberResult.objects.create(
            user=user, play_count=0, win_count=0
        )
    return bluff_number_result


def create_flash_result(user: DiscordUser) -> FlashResult:
    """FlashResultを作成または取得する"""
    try:
        flash_result = FlashResult.objects.get(user=user)
    except FlashResult.DoesNotExist:
        flash_result = FlashResult.objects.create(
            user=user, play_count=0, correct_count=0
        )
    return flash_result
