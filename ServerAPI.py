import requests
from telebot import types

class ServerAPI:
    def __init__(self):
        self.base_url = "https://caps-project-gr22b8aqm-georgplotnikov03-8623s-projects.vercel.app/"

    def login(self, email, password, telegram_id):
        url = f"{self.base_url}/login"

        try:
            response = (requests.post
                (url,
                json={"email": email, "password": password, "telegram_id": telegram_id},
                timeout = 5
            ))

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "connection_error"}
        except requests.exceptions.RequestException:
            return {"error": "connection_error"}

    def register(self, email, password, telegram_id):
        url = f"{self.base_url}/register"

        try:
            response = (requests.post(
                url,
                json={"email": email, "password": password, "telegram_id": telegram_id},
                timeout = 5
            ))
            if response.status_code in (200, 201):
                return response.json()

            elif response.status_code == 400:
                return {"error": "user_exists_or_invalid_data"}

            else:
                return {"error": f"server_error{response.status_code}"}
        except requests.exceptions.RequestException:
            return {"error": "connection_error"}
