# ELGEN PrivateGPT POC

This documentation is outdated, since this code is not mere prototype but backend logic
for more information: 

https://github.com/imartinez/privateGPT

# env file:

Use the example.env as a starting point. Check the link of privateGPT repo for more information.

```
PERSIST_DIRECTORY=db
MODEL_TYPE=GPT4All
MODEL_PATH=models/ggml-gpt4all-j-v1.3-groovy.bin
EMBEDDINGS_MODEL_NAME=all-MiniLM-L6-v2
MODEL_N_CTX=1000
SOURCE_DIRECTORY=source_documents/
APP_ENV=dev # to show logs/print in dev env
```

# steps to run privateGPT:

* properly configure your .env file
* download the model `ggml-gpt4all-j-v1.3-groovy.bin` and put it in models directory, check https://huggingface.co/orel12/ggml-gpt4all-j-v1.3-groovy
* make sure that SOURCE_DIRECTORY, MODEL_PATH are correct
* run `python ingest.py`
* run `python privateGPT.py` and query your model!
