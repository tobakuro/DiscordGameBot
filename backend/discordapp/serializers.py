from rest_framework import serializers

from .models import DiscordUser, OverSleptResult, PredictionResult, QuizResult


class LoginSerializer(serializers.Serializer):
    """ログイン用のシリアライザ"""

    username = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        fields = ["username", "password"]


class DiscordUserSerializer(serializers.ModelSerializer):
    """ "DiscordUserモデルのシリアライザ"""

    class Meta:
        model = DiscordUser
        fields = ["discord_id", "username"]


class QuizResultSerializer(serializers.ModelSerializer):
    """QuizResultモデルのシリアライザ"""

    discord_id = serializers.CharField(source="user.discord_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = QuizResult
        fields = ["discord_id", "username", "correct_count", "failed_count"]


class OverSleptResultSerializer(serializers.ModelSerializer):
    """OverSleptResultモデルのシリアライザ"""

    discord_id = serializers.CharField(source="user.discord_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = OverSleptResult
        fields = ["discord_id", "username", "overslept_count"]


class PredictionResultSerializer(serializers.ModelSerializer):
    """PredictionResultモデルのシリアライザ"""

    discord_id = serializers.CharField(source="user.discord_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = PredictionResult
        fields = ["discord_id", "username", "correct_count", "failed_count"]


class BluffNumberResultSerializer(serializers.Serializer):
    """BluffNumberResultモデルのシリアライザ"""

    discord_id = serializers.CharField(source="user.discord_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    play_count = serializers.IntegerField()
    win_count = serializers.IntegerField()

    class Meta:
        fields = ["discord_id", "username", "play_count", "win_count"]


class FlashResultSerializer(serializers.Serializer):
    """FlashResultモデルのシリアライザ"""

    discord_id = serializers.CharField(source="user.discord_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    play_count = serializers.IntegerField()
    correct_count = serializers.IntegerField()

    class Meta:
        fields = ["discord_id", "username", "play_count", "correct_count"]
