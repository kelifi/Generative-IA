from typing import Union

from fastapi import APIRouter

from tests.contract_test.configuration.configuration import ProviderState
from tests.contract_test.configuration.provider_states_setup import pact_states

pact_router = APIRouter()


@pact_router.post("/_pact/provider_states")
def provider_states(provider_state: ProviderState) -> Union[dict, None]:
    """
    Define provider states for the Pact contract testing.

    Args:
        provider_state (ProviderState): The provider state specified in the Pact request.

    Returns:
        dict: The result of the provider state setup, if applicable.
    """
    pact_states.get_pact_states_data()
    pact_states.container.db_helpers().init_database()
    provider_states_mapping = {
        "Conversation list found": pact_states.setup_user_exist_and_conversation_data_exist,
        "Conversation exist": pact_states.setup_conversation_exist,
    }
    if provider_state.state in provider_states_mapping:
        state_result = provider_states_mapping[provider_state.state]()
        return {"result": state_result}
    return None
