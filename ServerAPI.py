import requests
import time

class ServerAPI:
    def __init__(self):
        self.base_url = "https://caps-project-3fyz2v9aw-georgplotnikov03-8623s-projects.vercel.app"

    def login(self, email, password):
        url = f"{self.base_url}/api/login"

        for attempt in range(2):  # 2 попытки достаточно
            try:
                response = requests.post(
                    url,
                    json={
                        "email": email,
                        "password": password,
                        "client_type": "telegram"
                    },
                    timeout=3
                )

                print(f"LOGIN ATTEMPT {attempt + 1} STATUS:", response.status_code)
                print("RESPONSE:", response.text)

                if response.status_code == 200:
                    return response.json()

            except requests.exceptions.RequestException as e:
                print(f"LOGIN ATTEMPT {attempt + 1} ERROR:", e)
                time.sleep(1)

        return {"error": "connection_error"}
        '''if response.status_code == 200:
                return response.json()
            else:
                return {"error": "connection_error"}
        except requests.exceptions.RequestException:
            return {"error": "connection_error"}'''

    def register(self, email, password, telegram_id):
        url = f"{self.base_url}/api/register"

        for attempt in range(2):
            try:
                response = requests.post(
                    url,
                    json={
                        "email": email,
                        "password": password,
                        "client_type": "telegram"
                    },
                    timeout=3
                )

                print(f"REGISTER ATTEMPT {attempt + 1} STATUS:", response.status_code)
                print("RESPONSE:", response.text)

                if response.status_code in (200, 201):
                    return response.json()

                elif response.status_code == 400:
                    return {"error": "user_exists_or_invalid_data"}

            except requests.exceptions.RequestException as e:
                print(f"REGISTER ATTEMPT {attempt + 1} ERROR:", e)
                time.sleep(1)

        return {"error": "connection_error"}

    def add_to_queue(self, token, machine_code):
        url = f"{self.base_url}/api/add-to-queue/{machine_code}"

        for attempt in range(2):
            try:
                response = requests.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                    timeout=3
                )

                print(f"QUEUE ATTEMPT {attempt + 1} STATUS:", response.status_code)
                print("RESPONSE:", response.text)

                try:
                    return response.json()
                except:
                    return {"error": f"server_error{response.status_code}"}

            except requests.exceptions.RequestException as e:
                print(f"QUEUE ATTEMPT {attempt + 1} ERROR:", e)
                time.sleep(1)

        return {"error": "connection_error"}

    def get_last_deposits(self, token):
        url = f"{self.base_url}/api/get-last-deposits"

        for attempt in range(2):
            try:
                response = requests.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                    timeout=3
                )

                print(f"DEPOSITS ATTEMPT {attempt + 1} STATUS:", response.status_code)
                print("RESPONSE:", response.text)

                return response.json()

            except requests.exceptions.RequestException as e:
                print(f"DEPOSITS ATTEMPT {attempt + 1} ERROR:", e)
                time.sleep(1)

        return {"error": "connection_error"}

    def get_current_user(self, token):
        url = f"{self.base_url}/api/current-user"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        for attempt in range(2):
            try:
                response = requests.get(url, headers=headers, timeout=3)

                print(f"USER ATTEMPT {attempt + 1} STATUS:", response.status_code)
                print("RESPONSE:", response.text)

                if response.status_code == 200:
                    return response.json()

            except requests.exceptions.RequestException as e:
                print(f"USER ATTEMPT {attempt + 1} ERROR:", e)
                time.sleep(1)

        return {"error": "connection_error"}