import logging
import os
import time
from typing import Type

import torch
from pydantic import ValidationError
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from configuration.config import offline_service_config, app_config, OfflineServiceConfig
from source.exceptions.model_exception_handler import ResultParsingPredictionError, ModelLoadError, \
    ModelCallPredictionError, PromptError, MetadataParsingError
from source.schemas.model_answer_schema import ModelAnswer, ModelMetadata
from source.services.abstract_model_services import LLMFactory

logger = logging.getLogger(__name__)


class LLMFactoryHuggingFace(LLMFactory):
    def __init__(self, model_name: str, model_directory: str,
                 config: OfflineServiceConfig,
                 model_class: Type[AutoModelForCausalLM] = AutoModelForCausalLM,
                 tokenizer_class: Type[AutoTokenizer] = AutoTokenizer):
        super().__init__()
        self.config = config
        self.model_name = model_name
        self.model_class = model_class
        self.model_directory = os.path.join(model_directory, model_name.split("/")[-1])
        self.tokenizer = tokenizer_class.from_pretrained(self.model_name)
        self.model = None
        self.inference_pipeline = None

        # we need to keep space for new tokens to be generated! TEHE!
        self.allowed_prompt_length = self.tokenizer.model_max_length - self.config.MAX_NEW_TOKENS

    def load(self) -> AutoModelForCausalLM:
        """
        Wrapper for the HuggingFace model loading and downloading function.
        :return: the loaded model.
        """
        if self.config.FOUR_BIT_LLM_QUANTIZATION:
            return self.model_class.from_pretrained(
                self.model_name,
                cache_dir=self.model_directory,
                trust_remote_code=True,
                device_map=offline_service_config.DEVICE_MAP,
                load_in_8bit=offline_service_config.EIGHT_BIT_LLM_QUANTIZATION,
                load_in_4bit=offline_service_config.FOUR_BIT_LLM_QUANTIZATION,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
        return self.model_class.from_pretrained(
            self.model_name,
            cache_dir=self.model_directory,
            trust_remote_code=True,
            device_map=offline_service_config.DEVICE_MAP,
            load_in_8bit=offline_service_config.EIGHT_BIT_LLM_QUANTIZATION,
            load_in_4bit=offline_service_config.FOUR_BIT_LLM_QUANTIZATION,
        )

    def create_pipeline(self) -> pipeline:
        """
        Creates a HuggingFace pipeline for text generation using the selected model.
        :return: the created pipeline 
        """
        try:
            inference_pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                torch_dtype=torch.int8,
                trust_remote_code=True,
                eos_token_id=self.tokenizer.eos_token_id,
                device_map=offline_service_config.DEVICE_MAP,
                repetition_penalty=offline_service_config.REPETITION_PENALTY,
                no_repeat_ngram_size=offline_service_config.NO_REPEAT_NGRAM_SIZE
            )
        except TypeError as model_loading_error:
            raise ModelLoadError(
                detail=f"Unable to load the offline model {self.model_name}: {model_loading_error}"
            )

        logger.info("Pipeline created.")
        return inference_pipeline

    def predict(self, prompt: str, **kwargs) -> str:
        """
        Generates a response for the given prompt.
        :param prompt: the input prompt
        :return: model response
        """
        logger.warning("This function will be replaced by `generate_answer()` in a future version.")
        prompt_length = len(self.tokenizer.encode(prompt))
        if prompt_length > offline_service_config.MAX_PROMPT_TOKEN_LENGTH:
            raise PromptError(
                detail=f"The received prompt length ({prompt_length}) exceeds the "
                       f"limit of {offline_service_config.MAX_PROMPT_TOKEN_LENGTH}",
            )

        try:
            results = self.inference_pipeline(
                prompt,
                return_full_text=False,
                max_new_tokens=offline_service_config.MAX_NEW_TOKENS,
            )

        except RuntimeError as runtime_error:
            raise ModelCallPredictionError(
                detail=f"Could not generate answer for prompt: {prompt}. Error: {runtime_error}")

        except TypeError as model_loading_error:
            raise ModelLoadError(
                detail=f"Offline model {self.model_name} not loaded: {model_loading_error}"
            )
        torch.cuda.empty_cache()
        try:
            return results[0].get("generated_text")
        except (KeyError, ValueError) as parsing_error:
            raise ResultParsingPredictionError(
                detail=f"Unable to parse model answer: {parsing_error}"
            )

    def get_metadata(self) -> dict:
        """
        Get the model hyperparameters and related configuration.
        Returns: 
            dict: A dictionary containing the model metadata:
        """
        metadata = {"load_in_8bit": offline_service_config.EIGHT_BIT_LLM_QUANTIZATION}
        metadata["load_in_4bit"] = offline_service_config.NO_REPEAT_NGRAM_SIZE
        metadata["max_new_tokens"] = offline_service_config.MAX_NEW_TOKENS
        metadata["no_repeat_ngram_size"] = offline_service_config.NO_REPEAT_NGRAM_SIZE
        metadata["repetition_penalty"] = offline_service_config.REPETITION_PENALTY
        return metadata

    def generate_answer(self, prompt: str) -> ModelAnswer:
        """
        Generates an answer from the LLM given a prompt.
        Args:
            prompt: A text prompt upon which to generate an answer.

        Returns:
            ModelAnswer: the actual answer of the LLM and the inference time.
        """

        prompt_length = len(self.tokenizer.encode(prompt))
        if prompt_length > self.allowed_prompt_length:
            message = (
                f"The received prompt length ({prompt_length}) exceeds the limit of "
                f"{self.allowed_prompt_length} tokens, with max new tokens set to "
                f"{self.config.MAX_NEW_TOKENS}, the model total capacity is {self.tokenizer.model_max_length}!"
            )

            logger.error(message)
            raise PromptError(
                detail=message
            )

        model_answer = {"prompt_length": prompt_length}

        start_time = time.time()
        try:
            results = self.inference_pipeline(
                prompt,
                return_full_text=False,
                max_new_tokens=offline_service_config.MAX_NEW_TOKENS,
            )
        except TypeError as model_loading_error:
            raise ModelLoadError(
                detail=f"Offline model {self.model_name} not loaded: {model_loading_error}"
            )

        torch.cuda.empty_cache()
        model_answer["inference_time"] = time.time() - start_time
        try:
            model_answer["model_name"] = app_config.MODEL_NAME.split("/")[-1]
        except IndexError as index_error:
            raise MetadataParsingError(
                detail=f"Unable to validate metadata format: {index_error}",
            )
        try:
            model_answer["metadata"] = ModelMetadata(**self.get_metadata())
        except ValidationError as validation_error:
            raise MetadataParsingError(
                detail=f"Unable to validate metadata format: {validation_error}",
            )
        logger.info(
            f"Prompt length: {model_answer['prompt_length']} |  "
            f"Inference time: {model_answer['inference_time']} seconds."
        )
        try:
            model_answer["response"] = results[0].get("generated_text")
        except KeyError as key_error:
            raise ResultParsingPredictionError(
                detail=f"Unable to parse response from model: {key_error}",
            )
        try:
            return ModelAnswer(**model_answer)
        except ValidationError as validation_error:
            raise ResultParsingPredictionError(
                detail=f"Unable to validate model response format: {validation_error}",
            )

    def is_loaded_correctly(self) -> bool:
        """
        Checks if the  LLM is loaded as expected.
        If local LLM loading is enabled, the model should not be None.
        Returns: bool
        """

        return self.model is not None if app_config.LOAD_LOCAL_MODEL else True
