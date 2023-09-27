from uuid import UUID

from fastapi import APIRouter, Body, Header

from source.helpers.context_helpers import user_id_var
from source.schemas.common_schema import LLMResponse
from source.services.inference_services import llm_service

inference_router = APIRouter(prefix="/inference")


@inference_router.post("/")
async def chat_with_private_gpt_stateless(query: str = Body(...),
                                          user_id: UUID = Header(...)
                                          ) -> LLMResponse:
    '''
    use this endpoint to test purely the response of deployed llm model,
    without calling for database and stuff
    :param query:
    :return:
    '''

    user_id_var.set(str(user_id))

    return await llm_service.get_response_from_query(query)
