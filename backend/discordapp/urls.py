from django.urls import include, path

from .views import (
    LoginAPIView,
    OverSleptResultListAPIView,
    OverSleptResultPlusAPIView,
    OverSleptResultRetrieveAPIView,
    PredictionResultListAPIView,
    PredictionResultMinusAPIView,
    PredictionResultPlusAPIView,
    PredictionResultRetrieveAPIView,
    QuizResultListAPIView,
    QuizResultMinusAPIView,
    QuizResultPlusAPIView,
    QuizResultRetrieveAPIView,
)

app_name = "discordapp"
urlpatterns = [
    path("login/", view=LoginAPIView.as_view(), name="login"),
    path(
        "quiz-results/<str:guild_id>/<str:guild_name>/",
        view=QuizResultListAPIView.as_view(),
        name="quiz-result-list",
    ),
    path(
        "quiz-result/<str:discord_id>/<str:username>/",
        view=QuizResultRetrieveAPIView.as_view(),
        name="quiz-result-retrieve",
    ),
    path(
        "quiz-result/<str:discord_id>/<str:username>/plus/",
        view=QuizResultPlusAPIView.as_view(),
        name="quiz-result-plus",
    ),
    path(
        "quiz-result/<str:discord_id>/<str:username>/minus/",
        view=QuizResultMinusAPIView.as_view(),
        name="quiz-result-minus",
    ),
    path(
        "overslept-results/<str:guild_id>/<str:guild_name>/",
        view=OverSleptResultListAPIView.as_view(),
        name="overslept-result-list",
    ),
    path(
        "overslept-result/<str:discord_id>/<str:username>/",
        view=OverSleptResultRetrieveAPIView.as_view(),
        name="overslept-result-retrieve",
    ),
    path(
        "overslept-result/<str:discord_id>/<str:username>/plus/",
        view=OverSleptResultPlusAPIView.as_view(),
        name="overslept-result-plus",
    ),
    path(
        "prediction-results/<str:guild_id>/<str:guild_name>/",
        view=PredictionResultListAPIView.as_view(),
        name="prediction-result-list",
    ),
    path(
        "prediction-result/<str:discord_id>/<str:username>/",
        view=PredictionResultRetrieveAPIView.as_view(),
        name="prediction-result-retrieve",
    ),
    path(
        "prediction-result/<str:discord_id>/<str:username>/plus/",
        view=PredictionResultPlusAPIView.as_view(),
        name="prediction-result-plus",
    ),
    path(
        "prediction-result/<str:discord_id>/<str:username>/minus/",
        view=PredictionResultMinusAPIView.as_view(),
        name="prediction-result-minus",
    ),
]
