import requests
import time

class ServerAPI:
    def __init__(self):
        self.base_url = "https://caps-project-3fyz2v9aw-georgplotnikov03-8623s-projects.vercel.app"

    def _request_with_retry(self, method, url, **kwargs):
        for attempt in range(3):
            try:
                response = requests.request(
                    method,
                    url,
                    timeout=10,
                    **kwargs
                )

                print(f"TRY {attempt + 1} STATUS:", response.status_code)
                print("RESPONSE:", response.text)

                try:
                    return response.json()
                except:
                    return {"error": f"server_error{response.status_code}"}

            except requests.exceptions.ReadTimeout:
                print(f"⏳ Timeout, attempt {attempt + 1}")
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print("❌ Request error:", e)
                return {"error": "connection_error"}

        return {"error": "timeout"}

    # AUTH

    def login(self, email, password):
        url = f"{self.base_url}/api/login"

        return self._request_with_retry(
            "POST",
            url,
            json={
                "email": email,
                "password": password,
                "client_type": "telegram"
            }
        )

    def register(self, email, password, telegram_id):
        url = f"{self.base_url}/api/register"

        data = self._request_with_retry(
            "POST",
            url,
            json={
                "email": email,
                "password": password,
                "client_type": "telegram"
            }
        )

        # обработка бизнес-ошибок
        if isinstance(data, dict):
            if data.get("status") == "Failed":
                return data

        return data

    # USER

    def get_current_user(self, token):
        url = f"{self.base_url}/api/current-user"

        return self._request_with_retry(
            "GET",
            url,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

    # QUEUE

    def add_to_queue(self, token, machine_code):
        url = f"{self.base_url}/api/add-to-queue/{machine_code}"

        return self._request_with_retry(
            "POST",
            url,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

    # DEPOSITS

    def get_last_deposits(self, token):
        url = f"{self.base_url}/api/get-last-deposits"

        return self._request_with_retry(
            "GET",
            url,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )