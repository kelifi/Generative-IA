from abc import ABC, abstractmethod


class LLMChain(ABC):
    """
    An abstract class used to define a common interface for manipulating LLM stacks
    """

    @abstractmethod
    def prepare_prompt_arguments(self, *args, **kwargs):
        """
        Define a method that fetchs all necessary data for the construction of the prompt
        """
        pass

    @abstractmethod
    def construct_prompt(self, *args, **kwargs):
        """
        Define a method that constructs the prompts
        """
        pass

    @abstractmethod
    def generate_answer(self, *args, **kwargs):
        """
        Define a method that generates the answer, usually will need to fetch the model_code
        and make a HTTP request to said service
        """
        pass
