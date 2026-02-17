import uuid

from django.db import models


class DiscordUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    discord_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Discordユーザー"
        verbose_name_plural = "Discordユーザー一覧"

    def __str__(self):
        return self.username


class DiscordGuild(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guild_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(DiscordUser, related_name="guilds")

    class Meta:
        verbose_name = "Discordギルド"
        verbose_name_plural = "Discordギルド一覧"

    def __str__(self):
        return self.name


class QuizResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE)
    correct_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "クイズ結果"
        verbose_name_plural = "クイズ結果一覧"

    def __str__(self):
        return self.user.username


class OverSleptResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE)
    overslept_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "寝坊結果"
        verbose_name_plural = "寝坊結果一覧"

    def __str__(self):
        return self.user.username


class PredictionResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE)
    correct_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "予測結果"
        verbose_name_plural = "予測結果一覧"

    def __str__(self):
        return self.user.username


class BluffNumberResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE)
    play_count = models.IntegerField(default=0)
    win_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "ブラフナンバー結果"
        verbose_name_plural = "ブラフナンバー結果一覧"

    def __str__(self):
        return self.user.username
