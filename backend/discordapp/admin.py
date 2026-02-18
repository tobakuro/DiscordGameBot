from django.contrib import admin

from .models import (
    BluffNumberResult,
    DiscordGuild,
    DiscordUser,
    FlashResult,
    OverSleptResult,
    PredictionResult,
    QuizResult,
)


@admin.register(DiscordUser)
class DiscordUserAdmin(admin.ModelAdmin):
    list_display = ("username", "discord_id")


@admin.register(DiscordGuild)
class DiscordGuildAdmin(admin.ModelAdmin):
    list_display = ("name", "guild_id")
    filter_horizontal = ("members",)


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ("user", "correct_count", "failed_count")


@admin.register(OverSleptResult)
class OverSleptResultAdmin(admin.ModelAdmin):
    list_display = ("user", "overslept_count")


@admin.register(PredictionResult)
class PredictionResultAdmin(admin.ModelAdmin):
    list_display = ("user", "correct_count", "failed_count")


@admin.register(BluffNumberResult)
class BluffNumberResultAdmin(admin.ModelAdmin):
    list_display = ("user", "play_count", "win_count")


@admin.register(FlashResult)
class FlashResultAdmin(admin.ModelAdmin):
    list_display = ("user", "play_count", "correct_count")
