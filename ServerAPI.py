import requests

class ServerAPI:
    def __init__(self):
        self.base_url = "https://caps-project-8y8ucy8z0-georgplotnikov03-8623s-projects.vercel.app"

    def login(self, email, password):
        url = f"{self.base_url}/api/login"

        try:
            response = (requests.post
                (url,
                json={"email": email, "password": password, "client_type": "telegram"},
                timeout = 5
            ))
            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text)

            return response.json()

        except Exception as e:
            print("ERROR:", e)  # 👈 КЛЮЧЕВОЕ
            return {"error": "connection_error"}
            '''if response.status_code == 200:
                return response.json()
            else:
                return {"error": "connection_error"}
        except requests.exceptions.RequestException:
            return {"error": "connection_error"}'''

    def register(self, email, password, telegram_id):
        url = f"{self.base_url}/api/register"

        try:
            response = (requests.post(
                url,
                json={"email": email, "password": password, "cient_type": "telegram"},
                timeout = 5
            ))
            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text)

            if response.status_code in (200, 201):
                return response.json()

            elif response.status_code == 400:
                return {"error": "user_exists_or_invalid_data"}

            else:
                return {"error": f"server_error{response.status_code}"}
        except requests.exceptions.RequestException:
            return {"error": "connection_error"}

    def get_current_user(self, token):
        url = f"{self.base_url}/api/current-user"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:
            response = requests.get(url, headers=headers)

            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text)

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"server_error{response.status_code}"}

        except requests.exceptions.RequestException as e:
            print("REQUEST ERROR:", e)
            return {"error": "connection_error"}

    def add_to_queue(self, token, machine_code):
        url = f"{self.base_url}/api/add-to-queue/{machine_code}"

        print("👉 ADD_TO_QUEUE CALLED")
        print("URL:", url)
        print("TOKEN:", token[:20], "...")
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=10
            )

            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text)

            try:
                data = response.json()
            except:
                return {"error": f"server_error{response.status_code}"}

            return data

        except requests.exceptions.RequestException:
            return {"error": "connection_error"}

    def get_last_deposits(self, token):
        url = f"{self.base_url}/api/get-last-deposits"

        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=10
            )

            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text)

            try:
                return response.json()
            except:
                return {"error": f"server_error{response.status_code}"}

        except requests.exceptions.RequestException:
            return {"error": "connection_error"}