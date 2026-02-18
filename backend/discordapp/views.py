from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    BluffNumberResult,
    DiscordGuild,
    DiscordUser,
    OverSleptResult,
    PredictionResult,
    QuizResult,
)
from .serializers import (
    BluffNumberResultSerializer,
    LoginSerializer,
    OverSleptResultSerializer,
    PredictionResultSerializer,
    QuizResultSerializer,
)


def create_or_update_discord_user(discord_id: str, username: str) -> DiscordUser:
    try:
        user = DiscordUser.objects.get(discord_id=discord_id)
        if user.username != username:
            user.username = username
            user.save()
    except DiscordUser.DoesNotExist:
        user = DiscordUser.objects.create(discord_id=discord_id, username=username)
    return user


def create_or_update_discord_guild(guild_id: str, name: str) -> DiscordGuild:
    try:
        guild = DiscordGuild.objects.get(guild_id=guild_id)
        if guild.name != name:
            guild.name = name
            guild.save()
    except DiscordGuild.DoesNotExist:
        guild = DiscordGuild.objects.create(guild_id=guild_id, name=name)
    return guild


def create_quiz_result(user: DiscordUser) -> QuizResult:
    try:
        quiz_result = QuizResult.objects.get(user=user)
    except QuizResult.DoesNotExist:
        quiz_result = QuizResult.objects.create(
            user=user, correct_count=0, failed_count=0
        )
    return quiz_result


def create_overslept_result(user: DiscordUser) -> OverSleptResult:
    try:
        overslept_result = OverSleptResult.objects.get(user=user)
    except OverSleptResult.DoesNotExist:
        overslept_result = OverSleptResult.objects.create(user=user, overslept_count=0)
    return overslept_result


def create_prediction_result(user: DiscordUser) -> PredictionResult:
    try:
        prediction_result = PredictionResult.objects.get(user=user)
    except PredictionResult.DoesNotExist:
        prediction_result = PredictionResult.objects.create(
            user=user, correct_count=0, failed_count=0
        )
    return prediction_result


def create_bluff_number_result(user: DiscordUser) -> BluffNumberResult:
    try:
        bluff_number_result = BluffNumberResult.objects.get(user=user)
    except BluffNumberResult.DoesNotExist:
        bluff_number_result = BluffNumberResult.objects.create(
            user=user, play_count=0, win_count=0
        )
    return bluff_number_result


class LoginAPIView(generics.GenericAPIView):
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
