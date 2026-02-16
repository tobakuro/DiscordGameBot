from rest_framework import serializers

from .models import OverSleptResult, PredictionResult, QuizResult


class QuizResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizResult
        fields = ["user_id", "correct_count", "failed_count"]
