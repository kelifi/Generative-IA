import os
from typing import List

import requests
import torch
from langchain import LlamaCpp, HuggingFacePipeline
from langchain.callbacks.base import BaseCallbackHandler
from loguru import logger
from transformers import AutoModelForCausalLM, pipeline, AutoTokenizer

from configuration.config import AppConfig, app_config
from source.exceptions.service_exceptions import UnknownModelType
from source.helpers.model_wrappers.fake_llm_wrapper import FakeListLLM
from source.helpers.model_wrappers.gpt4all_wrapper import GPT4All
from source.helpers.model_wrappers.huggingface_wrapper import HuggingFacePipeline
from source.helpers.streaming_handlers import streaming_callbacks
from source.schemas.llm_schema import SupportedLLModels


class LLMFactory:
    def __init__(self, config: AppConfig, callbacks: List[BaseCallbackHandler]):
        self.config = config
        self.streaming_callbacks = callbacks

    def __call__(self, model_type: str):
        config = self.config
        match model_type:  # match requires probably python 3.10 or more
            case SupportedLLModels.llama_cpp:
                return LlamaCpp(model_path=config.model_path, n_ctx=config.model_n_ctx,
                                callbacks=None, streaming=True,
                                verbose=False)
            case SupportedLLModels.gpt4all:
                return GPT4All(model=config.model_path,
                               n_ctx=config.model_n_ctx,
                               backend='gptj',
                               callbacks=self.streaming_callbacks,
                               verbose=False)
            case SupportedLLModels.gpt2:
                tokenizer = AutoTokenizer.from_pretrained("gpt2")
                model = AutoModelForCausalLM.from_pretrained(config.model_path)
                pipe = pipeline(
                    "text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200
                )
                return HuggingFacePipeline(pipeline=pipe, callbacks=self.streaming_callbacks)

            case SupportedLLModels.falcon:
                model_name = config.FALCON_MODEL_PATH
                model_directory = config.LOCAL_FALCON_MODEL_PATH
                # Check if the model files already exist
                if not os.path.exists(os.path.join(model_directory, "config.json")):
                    model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", trust_remote_code=True)
                    model.save_pretrained(model_directory)
                else:
                    model = AutoModelForCausalLM.from_pretrained(model_directory, device_map="auto",
                                                                 trust_remote_code=True)
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    torch_dtype=torch.int8,
                    trust_remote_code=True,
                    max_length=2000,
                    eos_token_id=tokenizer.eos_token_id,
                    device_map="auto"
                )
                logger.info("Model loaded")
                return HuggingFacePipeline(pipeline=pipe, callbacks=self.streaming_callbacks)

            case SupportedLLModels.fake:
                with open("static/mock_llm_response.txt", 'r') as f:
                    responses = [
                        str(f.read()),
                    ]
                    return FakeListLLM(responses=responses, callbacks=self.streaming_callbacks)

            case _default:
                logger.error(f"Model {model_type} not supported!")
                raise UnknownModelType(detail=f"Unknown Model Type: {model_type}")

    @staticmethod
    def download_model(model_url, model_path):
        logger.info("Downloading Model Files ... Please wait")
        if os.path.exists(model_path):
            logger.info("Model already exists .. Skipping download!")
        else:
            response = requests.get(model_url)
            response.raise_for_status()

            with open(model_path, 'wb') as model_file:
                model_file.write(response.content)
            logger.success("Model Files Downloaded!")


llm_factory = LLMFactory(config=app_config, callbacks=streaming_callbacks)
