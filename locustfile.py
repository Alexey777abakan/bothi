from locust import HttpUser, task, between

class TelegramUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def start(self):
        self.client.get("/start")  # Симулируйте запросы к вашему боту

    @task(3)
    def generate(self):
        self.client.get("/generate?theme=3#travel")  # Симулируйте генерацию постов