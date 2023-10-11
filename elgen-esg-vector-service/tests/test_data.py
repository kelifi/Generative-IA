class MocksConstants:
    dummy_similar_docs = {"data": [{
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "content": "string",
        "link": "string",
        "fileId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "fileName": "string",
        "creationDate": None,
        "documentType": "string",
        "downloadLink": "/sources/v1/download/3fa85f64-5717-4562-b3fc-2c963f66afa6"
    }], "detail": "test"}

    dummy_similar_docs_request = {"query": "This for testing",
                                  "n_results": 3,
                                  "workspace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"}
    dummy_nb_documents = {"count": 10}
    workspace_id = '3fa85f64-5717-4562-b3fc-2c963f66afa6'
    dummy_chunks = {"data": [
        {
            "document": "The sky was painted with vibrant hues of orange and pink as the sun began to set.",
            "metadata": {
                "file_name": "nature_article.pdf",
                "file_id": "1001",
                "workspace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "es_id": "es_001"
            }
        }]}
