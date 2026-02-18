from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .mixins import (
    create_bluff_number_result,
    create_flash_result,
    create_or_update_discord_guild,
    create_or_update_discord_user,
    create_overslept_result,
    create_prediction_result,
    create_quiz_result,
)
from .models import (
    BluffNumberResult,
    FlashResult,
    OverSleptResult,
    PredictionResult,
    QuizResult,
)
from .serializers import (
    BluffNumberResultSerializer,
    FlashResultSerializer,
    LoginSerializer,
    OverSleptResultSerializer,
    PredictionResultSerializer,
    QuizResultSerializer,
)


class LoginAPIView(generics.GenericAPIView):
    """ログイン用のAPIビュー"""

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )


class AddMemberToGuildAPIView(generics.GenericAPIView):
    """ギルドにメンバーを追加するAPIビュー"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        guild_id = request.data.get("guild_id")
        guild_name = request.data.get("guild_name", "")
        discord_id = request.data.get("discord_id")
        username = request.data.get("username")
        guild = create_or_update_discord_guild(guild_id, guild_name)
        user = create_or_update_discord_user(discord_id, username)
        guild.members.add(user)
        guild.save()
        return Response({"message": "Member added to guild"}, status=status.HTTP_200_OK)


class RemoveMemberFromGuildAPIView(generics.GenericAPIView):
    """ギルドからメンバーを削除するAPIビュー"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        guild_id = request.data.get("guild_id")
        guild_name = request.data.get("guild_name", "")
        discord_id = request.data.get("discord_id")
        username = request.data.get("username")
        guild = create_or_update_discord_guild(guild_id, guild_name)
        user = create_or_update_discord_user(discord_id, username)
        guild.members.remove(user)
        guild.save()
        return Response(
            {"message": "Member removed from guild"}, status=status.HTTP_200_OK
        )


class QuizResultListAPIView(generics.GenericAPIView):
    """QuizResultの一覧を取得するAPIビュー"""

    queryset = QuizResult.objects.all()
    serializer_class = QuizResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guild_id = request.data.get("guild_id")
        guild_name = request.data.get("guild_name", "")
        guild = create_or_update_discord_guild(guild_id, guild_name)
        members = guild.members.all()
        serializers = self.get_serializer(
            [create_quiz_result(member) for member in members], many=True
        )
        return Response(serializers.data)


class QuizResultRetrieveAPIView(generics.RetrieveAPIView):
    """QuizResultを取得するAPIビュー"""

    queryset = QuizResult.objects.all()
    serializer_class = QuizResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        username = request.data.get("username")
        user = create_or_update_discord_user(discord_id, username)
        quiz_result = create_quiz_result(user)
        serializer = self.get_serializer(quiz_result)
        return Response(serializer.data)


class QuizResultPlusAPIView(generics.UpdateAPIView):
    """QuizResultの正解数を増加させるAPIビュー"""

    queryset = QuizResult.objects.all()
    serializer_class = QuizResultSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = create_or_update_discord_user(
            request.data.get("discord_id"), request.data.get("username")
        )
        quiz_result = create_quiz_result(user)
        quiz_result.correct_count += 1
        quiz_result.save()
        serializer = self.get_serializer(quiz_result)
        return Response(serializer.data)


class QuizResultMinusAPIView(generics.UpdateAPIView):
    """QuizResultの不正解数を増加させるAPIビュー"""

    queryset = QuizResult.objects.all()
    serializer_class = QuizResultSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = create_or_update_discord_user(
            request.data.get("discord_id"), request.data.get("username")
        )
        quiz_result = create_quiz_result(user)
        quiz_result.failed_count += 1
        quiz_result.save()
        serializer = self.get_serializer(quiz_result)
        return Response(serializer.data)


class OverSleptResultListAPIView(generics.GenericAPIView):
    """OverSleptResultの一覧を取得するAPIビュー"""

    queryset = OverSleptResult.objects.all()
    serializer_class = OverSleptResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guild_id = request.data.get("guild_id")
        guild_name = request.data.get("guild_name", "")
        guild = create_or_update_discord_guild(guild_id, guild_name)
        members = guild.members.all()
        serializers = self.get_serializer(
            [create_overslept_result(member) for member in members], many=True
        )
        return Response(serializers.data)


class OverSleptResultRetrieveAPIView(generics.RetrieveAPIView):
    """OverSleptResultを取得するAPIビュー"""

    queryset = OverSleptResult.objects.all()
    serializer_class = OverSleptResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = create_or_update_discord_user(
            request.data.get("discord_id"), request.data.get("username")
        )
        overslept_result = create_overslept_result(user)
        serializer = self.get_serializer(overslept_result)
        return Response(serializer.data)


class OverSleptResultPlusAPIView(generics.UpdateAPIView):
    """OverSleptResultの寝坊数を増加させるAPIビュー"""

    queryset = OverSleptResult.objects.all()
    serializer_class = OverSleptResultSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = create_or_update_discord_user(
            request.data.get("discord_id"), request.data.get("username")
        )
        overslept_result = create_overslept_result(user)
        overslept_result.overslept_count += 1
        overslept_result.save()
        serializer = self.get_serializer(overslept_result)
        return Response(serializer.data)


class PredictionResultListAPIView(generics.GenericAPIView):
    """PredictionResultの一覧を取得するAPIビュー"""

    queryset = PredictionResult.objects.all()
    serializer_class = PredictionResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guild_id = request.data.get("guild_id")
        guild_name = request.data.get("guild_name", "")
        guild = create_or_update_discord_guild(guild_id, guild_name)
        members = guild.members.all()
        serializers = self.get_serializer(
            [create_prediction_result(member) for member in members], many=True
        )
        return Response(serializers.data)


class PredictionResultRetrieveAPIView(generics.RetrieveAPIView):
    """PredictionResultを取得するAPIビュー"""

    queryset = PredictionResult.objects.all()
    serializer_class = PredictionResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = create_or_update_discord_user(
            request.data.get("discord_id"), request.data.get("username")
        )
        prediction_result = create_prediction_result(user)
        serializer = self.get_serializer(prediction_result)
        return Response(serializer.data)


class PredictionResultPlusAPIView(generics.UpdateAPIView):
    """PredictionResultの正解数を増加させるAPIビュー"""

    queryset = PredictionResult.objects.all()
    serializer_class = PredictionResultSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = create_or_update_discord_user(
            request.data.get("discord_id"), request.data.get("username")
        )
        prediction_result = create_prediction_result(user)
        prediction_result.correct_count += 1
        prediction_result.save()
        serializer = self.get_serializer(prediction_result)
        return Response(serializer.data)


class PredictionResultMinusAPIView(generics.UpdateAPIView):
    """PredictionResultの不正解数を増加させるAPIビュー"""

    queryset = PredictionResult.objects.all()
    serializer_class = PredictionResultSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = create_or_update_discord_user(
            request.data.get("discord_id"), request.data.get("username")
        )
        prediction_result = create_prediction_result(user)
        prediction_result.failed_count += 1
        prediction_result.save()
        serializer = self.get_serializer(prediction_result)
        return Response(serializer.data)


class BluffNumberResultListAPIView(generics.GenericAPIView):
    """BluffNumberResultの一覧を取得するAPIビュー"""

    queryset = BluffNumberResult.objects.all()
    serializer_class = BluffNumberResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guild_id = request.data.get("guild_id")
        guild_name = request.data.get("guild_name", "")
        guild = create_or_update_discord_guild(guild_id, guild_name)
        members = guild.members.all()
        serializers = self.get_serializer(
            [create_bluff_number_result(member) for member in members], many=True
        )
        return Response(serializers.data)


class BluffNumberResultRetrieveAPIView(generics.RetrieveAPIView):
    """BluffNumberResultを取得するAPIビュー"""

    queryset = BluffNumberResult.objects.all()
    serializer_class = BluffNumberResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        username = request.data.get("username")
        user = create_or_update_discord_user(discord_id, username)
        bluff_number_result = create_bluff_number_result(user)
        serializer = self.get_serializer(bluff_number_result)
        return Response(serializer.data)


class BluffNumberPlayAPIView(generics.UpdateAPIView):
    """BluffNumberResultのプレイ数を増加させるAPIビュー"""

    queryset = BluffNumberResult.objects.all()
    serializer_class = BluffNumberResultSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        username = request.data.get("username")
        user = create_or_update_discord_user(discord_id, username)
        bluff_number_result = create_bluff_number_result(user)
        bluff_number_result.play_count += 1
        bluff_number_result.save()
        serializer = self.get_serializer(bluff_number_result)
        return Response(serializer.data)


class BluffNumberWinAPIView(generics.UpdateAPIView):
    """BluffNumberResultの勝利数を増加させるAPIビュー"""

    queryset = BluffNumberResult.objects.all()
    serializer_class = BluffNumberResultSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        username = request.data.get("username")
        user = create_or_update_discord_user(discord_id, username)
        bluff_number_result = create_bluff_number_result(user)
        bluff_number_result.win_count += 1
        bluff_number_result.save()
        serializer = self.get_serializer(bluff_number_result)
        return Response(serializer.data)


class FlashResultListAPIView(generics.GenericAPIView):
    """FlashResultの一覧を取得するAPIビュー"""

    queryset = FlashResult.objects.all()
    serializer_class = FlashResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guild_id = request.data.get("guild_id")
        guild_name = request.data.get("guild_name", "")
        guild = create_or_update_discord_guild(guild_id, guild_name)
        members = guild.members.all()
        serializers = self.get_serializer(
            [create_flash_result(member) for member in members], many=True
        )
        return Response(serializers.data)


class FlashResultRetrieveAPIView(generics.RetrieveAPIView):
    """FlashResultを取得するAPIビュー"""

    queryset = FlashResult.objects.all()
    serializer_class = FlashResultSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        username = request.data.get("username")
        user = create_or_update_discord_user(discord_id, username)
        flash_result_instance = create_flash_result(user)
        serializer = self.get_serializer(flash_result_instance)
        return Response(serializer.data)


class FlashplayAPIView(generics.UpdateAPIView):
    """FlashResultのプレイ数を増加させるAPIビュー"""

    queryset = FlashResult.objects.all()
    serializer_class = FlashResultSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        username = request.data.get("username")
        user = create_or_update_discord_user(discord_id, username)
        flash_result_instance = create_flash_result(user)
        flash_result_instance.play_count += 1
        flash_result_instance.save()
        serializer = self.get_serializer(flash_result_instance)
        return Response(serializer.data)


class FlashCorrectAPIView(generics.UpdateAPIView):
    """FlashResultの正解数を増加させるAPIビュー"""

    queryset = FlashResult.objects.all()
    serializer_class = FlashResultSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        discord_id = request.data.get("discord_id")
        username = request.data.get("username")
        user = create_or_update_discord_user(discord_id, username)
        flash_result_instance = create_flash_result(user)
        flash_result_instance.correct_count += 1
        flash_result_instance.save()
        serializer = self.get_serializer(flash_result_instance)
        return Response(serializer.data)
