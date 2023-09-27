import torch

from tests.test_data import mock_pipeline_response, device_map


class MockPipeline:
    def __init__(self,
                 task: str,
                 model: any,
                 tokenizer: any,
                 torch_dtype: torch.dtype,
                 trust_remote_code: bool,
                 eos_token_id: int,
                 device_map: str,
                 *args,
                 **kwargs
                 ):
        self.task = task,
        self.model = model,
        self.tokenizer = tokenizer,
        self.torch_dtype = torch_dtype,
        self.trust_remote_code = trust_remote_code,
        self.eos_token_id = eos_token_id,
        self.device_map = device_map

    def __call__(self, prompt: str, return_full_text: bool, max_new_tokens: int) -> list[dict]:
        return mock_pipeline_response


def mock_pipeline_call(*args, **kwargs):
    return MockPipeline(
        "text-generation",
        model=None,
        tokenizer=None,
        torch_dtype=torch.int8,
        trust_remote_code=True,
        eos_token_id=0,
        device_map=device_map,
    ).__call__(*args, **kwargs)


class MockTokenizer:
    def __init__(self, *args, **kwargs):
        """
        Mock Init
        :param args:
        :param kwargs:
        """
        self.model_max_length = 2048  # assuming it is falcon-instruct

    def __call__(self, *args, **kwargs):
        """
        Mock call to model
        :param args:
        :param kwargs:
        :return:
        """
        return {'attention_mask': torch.tensor([[1, 1, 1, 1, 1, 1, 1, 1]]),
                'input_ids': torch.tensor([[0, 42891, 475, 338, 181, 967, 46035, 2]])
                }

    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        """
        Mock from_pretrained
        :param args:
        :param kwargs:
        :return:
        """
        return cls(*args, **kwargs)

    def encode(cls, *args, **kwargs):
        """
        Mock from_pretrained
        :param args:
        :param kwargs:
        :return:
        """
        return [210]


def mock_tokenizer_call(*args, **kwargs):
    return MockTokenizer().__call__(*args, **kwargs)


class MockAutoModel:
    def __init__(self, *args, **kwargs):
        """
        Mock Init
        :param args:
        :param kwargs:
        """

    @classmethod
    def from_pretrained(cls, model_name, cache_dir, trust_remote_code, device_map,
                                                   load_in_8bit, load_in_4bit, bnb_4bit_compute_dtype=None,
                                                   bnb_4bit_quant_type=None, bnb_4bit_use_double_quant=None):
        """
        Mock from_pretrained
        :param args:
        :param kwargs:
        :return:
        """
        return cls(model_name, cache_dir, trust_remote_code, device_map, load_in_8bit, load_in_4bit,
                   bnb_4bit_compute_dtype, bnb_4bit_quant_type, bnb_4bit_use_double_quant)
