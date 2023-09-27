import uuid

from locust import HttpUser, task, between


class ConversationUser(HttpUser):
    headers = {"user-id": "154521b8-94ce-4229-a25e-af856ff4c070"}  # Replace with the appropriate user-id value
    wait_time = between(1, 5)  # You can adjust this as needed

    @task
    def get_conversations(self):
        self.client.get("/conversations", headers=self.headers)

    @task
    def create_conversation(self):
        headers = {
            "user-id": "154521b8-94ce-4229-a25e-af856ff4c070",  # Replace with the appropriate user ID header value
        }
        request_body = {
            "title": "Test Conversation",
        }
        self.client.post("/conversations", headers=headers, json=request_body)

    @task
    def get_latest_versioned_answer(self):

        answer_id = "f881182b-df14-4182-98c1-25310fd86c8f"

        headers = {
            "user-id": "154521b8-94ce-4229-a25e-af856ff4c070",
        }
        self.client.get(f"/chat/answer/{answer_id}/history/latest", headers=headers)

    @task
    def create_sources(self):
        question_id = str(uuid.uuid4())
        body = {
            "similar_docs": [
                {
                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "content": "string",
                    "link": "string",
                    "fileName": "EL_GEN.pdf",
                    "creationTime": "2023-09-08T13:54:22.046Z",
                    "documentType": "string",
                    "fileId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "downloadLink": "string"
                }
            ]
        }

        self.client.post(
            f"/conversations/sources",
            json=body,  # Send the data as JSON
            params={"question_id": question_id}
        )

    @task
    def web_source(self):
        question_id = str(uuid.uuid4())
        body = {
            "web_sources": [
                {
                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "url": "string",
                    "description": "web_source",
                    "title": "EL_GEN",
                    "paragraphs": "string"
                }
            ]
        }
        self.client.post(f"/conversations/web-sources", json=body,

                         params={"question_id": question_id}
                         )


