import requests
from django.conf import settings


def login_request():
    for _ in range(3):
        res = requests.post(
            f"http://127.0.0.1:8000/api/login/",
            json={
                "username": settings.ADMIN_USERNAME,
                "password": settings.ADMIN_PASSWORD,
            },
        )
        if res.status_code == 200:
            break
    return res


def add_member_to_guild_request(token, guild_id, guild_name, discord_id, username):
    for _ in range(3):
        res = requests.post(
            f"http://127.0.0.1:8000/api/guild/add-member/",
            headers={"Authorization": f"Token {token}"},
            json={
                "guild_id": guild_id,
                "guild_name": guild_name,
                "discord_id": discord_id,
                "username": username,
            },
        )
        if res.status_code == 200:
            break
    return res


def remove_member_from_guild_request(token, guild_id, guild_name, discord_id, username):
    for _ in range(3):
        res = requests.post(
            f"http://127.0.0.1:8000/api/guild/remove-member/",
            headers={"Authorization": f"Token {token}"},
            json={
                "guild_id": guild_id,
                "guild_name": guild_name,
                "discord_id": discord_id,
                "username": username,
            },
        )
        if res.status_code == 200:
            break
    return res


def quiz_result_list_request(token, guild_id, guild_name):
    for _ in range(3):
        res = requests.get(
            f"http://127.0.0.1:8000/api/quiz-results/",
            headers={"Authorization": f"Token {token}"},
            json={"guild_id": guild_id, "guild_name": guild_name},
        )
        if res.status_code == 200:
            break
    return res


def quiz_result_retrieve_request(token, discord_id, username):
    for _ in range(3):
        res = requests.get(
            f"http://127.0.0.1:8000/api/quiz-result/",
            headers={"Authorization": f"Token {token}"},
            json={"discord_id": discord_id, "username": username},
        )
        if res.status_code == 200:
            break
    return res


def quiz_result_plus_request(token, discord_id, username):
    for _ in range(3):
        res = requests.post(
            f"http://127.0.0.1:8000/api/quiz-result/plus/",
            headers={"Authorization": f"Token {token}"},
            json={"discord_id": discord_id, "username": username},
        )
        if res.status_code == 200:
            break
    return res


def quiz_result_minus_request(token, discord_id, username):
    for _ in range(3):
        res = requests.post(
            f"http://127.0.0.1:8000/api/quiz-result/minus/",
            headers={"Authorization": f"Token {token}"},
            json={"discord_id": discord_id, "username": username},
        )
        if res.status_code == 200:
            break
    return res


def overslept_result_list_request(token, guild_id, guild_name):
    for _ in range(3):
        res = requests.get(
            f"http://127.0.0.1:8000/api/overslept-results/",
            headers={"Authorization": f"Token {token}"},
            json={"guild_id": guild_id, "guild_name": guild_name},
        )
        if res.status_code == 200:
            break
    return res


def overslept_result_retrieve_request(token, discord_id, username):
    for _ in range(3):
        res = requests.get(
            f"http://127.0.0.1:8000/api/overslept-result/",
            headers={"Authorization": f"Token {token}"},
            json={"discord_id": discord_id, "username": username},
        )
        if res.status_code == 200:
            break
    return res


def overslept_result_plus_request(token, discord_id, username):
    for _ in range(3):
        res = requests.post(
            f"http://127.0.0.1:8000/api/overslept-result/plus/",
            headers={"Authorization": f"Token {token}"},
            json={"discord_id": discord_id, "username": username},
        )
        if res.status_code == 200:
            break
    return res


def prediction_result_list_request(token, guild_id, guild_name):
    for _ in range(3):
        res = requests.get(
            f"http://127.0.0.1:8000/api/prediction-results/",
            headers={"Authorization": f"Token {token}"},
            json={"guild_id": guild_id, "guild_name": guild_name},
        )
        if res.status_code == 200:
            break
    return res


def prediction_result_retrieve_request(token, discord_id, username):
    for _ in range(3):
        res = requests.get(
            f"http://127.0.0.1:8000/api/prediction-result/",
            headers={"Authorization": f"Token {token}"},
            json={"discord_id": discord_id, "username": username},
        )
        if res.status_code == 200:
            break
    return res


def prediction_result_plus_request(token, discord_id, username):
    for _ in range(3):
        res = requests.post(
            f"http://127.0.0.1:8000/api/prediction-result/plus/",
            headers={"Authorization": f"Token {token}"},
            json={"discord_id": discord_id, "username": username},
        )
        if res.status_code == 200:
            break
    return res


def prediction_result_minus_request(token, discord_id, username):
    for _ in range(3):
        res = requests.post(
            f"http://127.0.0.1:8000/api/prediction-result/minus/",
            headers={"Authorization": f"Token {token}"},
            json={"discord_id": discord_id, "username": username},
        )
        if res.status_code == 200:
            break
    return res
