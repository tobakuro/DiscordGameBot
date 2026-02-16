from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DiscordUser


def create_or_update_user(user_id: int, username: str) -> None:
    DiscordUser.objects.update_or_create(
        discord_id=user_id, defaults={"username": username}
    )


class QuizResultListAPIView(generics.ListAPIView):
    queryset = DiscordUser.objects.all()
    serializer_class = None  # 適切なシリアライザを指定してください
    permission_classes = [IsAuthenticated]
