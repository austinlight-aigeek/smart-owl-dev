import json

from deprecated import deprecated
from langchain.schema import messages_to_dict

from app.apis.services.gpt_manager import GPTManager, GPTManagerError
from app.apis.services.owl_manager import OwlChatbotAcademy, OwlChatbotPDF
from app.apis.services.public_llms.chain_manager import ChainManagerError
from app.apis.services.public_llms.chatbot_gatekeeper import ChatBotGateKeeper
from app.db.repository.log import log_prompt


async def _retrieve_chat_messages(chat_id, cache_db):
    chat_message_history = None
    if await cache_db.exists(chat_id):
        chat_message_history: str = await cache_db.get_conversation(chat_id)

    return chat_message_history


async def _save_extracted_messages(chat_id, cache_db, extracted_messages):
    ingest_to_cache: str = json.dumps(messages_to_dict(extracted_messages))
    await cache_db.save_conversation(chat_id, ingest_to_cache)


@deprecated(
    version="0.0.1",
    reason="The gpt_handler() function is deprecated and will be removed in a future version.",
)
async def gpt_handler(log_db, current_user, request_data):
    try:
        gptManager = GPTManager(model=request_data.model)
        prompt = request_data.prompt
        # cleaned_prompt = clean_prompt(prompt=prompt, http_err=sensitive_material_exception)
        cleaned_prompt = prompt
        response = await gptManager.complete(cleaned_prompt)
    except GPTManagerError as gpt_error:
        raise gpt_error

    log_prompt(
        db=log_db,
        user=current_user,
        model=request_data.model,
        prompt=prompt,
        cleaned_prompt=cleaned_prompt,
        response=response,
    )

    return response.choices[0].message.content


async def public_chat_handler(log_db, current_user, request_data, cache_db):
    chat_id = current_user.email + "+" + request_data.model
    chat_message_history = await _retrieve_chat_messages(chat_id, cache_db)

    try:
        chatbot_gatekeeper = ChatBotGateKeeper(
            model_type=request_data.model, chat_message_history=chat_message_history
        )

        prompt = request_data.prompt
        # cleaned_prompt = clean_prompt(prompt=prompt, http_err=sensitive_material_exception)
        cleaned_prompt = prompt
        response = await chatbot_gatekeeper(cleaned_prompt, output_dict=True)
    except ChainManagerError as gpt_chat_error:
        raise gpt_chat_error

    log_prompt(
        db=log_db,
        user=current_user,
        model=request_data.model,
        prompt=prompt,
        cleaned_prompt=cleaned_prompt,
        response=response,
    )

    extracted_messages = chatbot_gatekeeper.get_message_chat_history()
    await _save_extracted_messages(chat_id, cache_db, extracted_messages)

    return response.choices[-1].message.content


async def owl_handler(request_data, cache_db, current_user):
    chat_id = current_user.email + "+" + request_data.model
    chat_message_history = await _retrieve_chat_messages(chat_id, cache_db)

    prompt = request_data.prompt
    # cleaned_prompt = clean_prompt(prompt=prompt, http_err=sensitive_material_exception)
    cleaned_prompt = prompt

    if request_data.model in {
        "Owl_WGU_Program_Advisor_BA",
        "Owl_MTC_Enrollment_Counselor",
        "Owl_WGU_Smart_Statistics_TA",
        "Owl_WGU_Smart_History_TA",
        "Owl_ChatLR",
    }:
        smart_owl = OwlChatbotPDF(
            request_data.model, chat_message_history=chat_message_history
        )
    elif request_data.model == "Owl_WGU_Smart_English_TA":
        smart_owl = OwlChatbotAcademy(
            request_data.model, chat_message_history=chat_message_history
        )
    else:
        return "Oops, something went wrong. You should not be here :)"

    response = await smart_owl.execute(cleaned_prompt)

    # TODO: log_prompt

    extracted_messages = smart_owl.get_message_chat_history()
    await _save_extracted_messages(chat_id, cache_db, extracted_messages)

    return response


def llm_handler(log_db, current_user, request_data, cache_db):
    print(request_data)

    if request_data.model.lower().startswith("owl"):
        return owl_handler(request_data, cache_db, current_user)
    else:
        return public_chat_handler(log_db, current_user, request_data, cache_db)
