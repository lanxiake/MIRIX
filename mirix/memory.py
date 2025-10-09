from typing import Callable, Dict, List, Optional
import logging

from mirix.constants import MESSAGE_SUMMARY_REQUEST_ACK
from mirix.llm_api.llm_client import LLMClient
from mirix.prompts.gpt_summarize import SYSTEM as SUMMARY_PROMPT_SYSTEM
from mirix.schemas.agent import AgentState
from mirix.schemas.enums import MessageRole
from mirix.schemas.memory import Memory
from mirix.schemas.message import Message
from mirix.schemas.mirix_message_content import TextContent
from mirix.settings import summarizer_settings
from mirix.utils import count_tokens, printd

logger = logging.getLogger(__name__)


def get_memory_functions(cls: Memory) -> Dict[str, Callable]:
    """Get memory functions for a memory class"""
    functions = {}

    # collect base memory functions (should not be included)
    base_functions = []
    for func_name in dir(Memory):
        funct = getattr(Memory, func_name)
        if callable(funct):
            base_functions.append(func_name)

    for func_name in dir(cls):
        if func_name.startswith("_") or func_name in [
            "load",
            "to_dict",
        ]:  # skip base functions
            continue
        if func_name in base_functions:  # dont use BaseMemory functions
            continue
        func = getattr(cls, func_name)
        if not callable(func):  # not a function
            continue
        functions[func_name] = func
    return functions


def _format_summary_history(message_history: List[Message]):
    # TODO use existing prompt formatters for this (eg ChatML)
    def format_message(m: Message):
        content_str = ""
        for content in m.content:
            if content.type == "text":
                content_str += content.text + "\n"
            elif content.type == "image_url":
                content_str += f"[Image: {content.image_id}]" + "\n"
            elif content.type == "file_uri":
                content_str += f"[File: {content.file_id}]" + "\n"
            elif content.type == "google_cloud_file_uri":
                content_str += f"[Cloud File: {content.cloud_file_uri}]" + "\n"
            else:
                content_str += f"[Unknown content type: {content.type}]" + "\n"
        return content_str.strip()

    return "\n\n".join([f"{m.role}: {format_message(m)}" for m in message_history])


def summarize_messages(
    agent_state: AgentState,
    message_sequence_to_summarize: List[Message],
    existing_file_uris: Optional[List[str]] = None,
):
    """Summarize a message sequence using GPT"""
    # we need the context_window
    context_window = agent_state.llm_config.context_window

    summary_prompt = SUMMARY_PROMPT_SYSTEM
    summary_input = _format_summary_history(message_sequence_to_summarize)
    summary_input_tkns = count_tokens(summary_input)

    # Check if the input is too large for summarization
    max_summary_tokens = int(summarizer_settings.memory_warning_threshold * context_window)

    if summary_input_tkns > max_summary_tokens:
        # Need to split into batches and summarize recursively
        logger.info(f"Summary input ({summary_input_tkns} tokens) exceeds threshold ({max_summary_tokens} tokens)")

        # Calculate how many batches we need
        # Use 0.5 (50%) of max to be more conservative and leave room for the prompt
        target_tokens_per_batch = int(max_summary_tokens * 0.5)
        num_batches = max(2, int(summary_input_tkns / target_tokens_per_batch) + 1)
        batch_size = len(message_sequence_to_summarize) // num_batches

        if batch_size < 1:
            batch_size = 1

        logger.info(f"Splitting into {num_batches} batches of ~{batch_size} messages each")

        # Summarize each batch
        summaries = []
        for i in range(0, len(message_sequence_to_summarize), batch_size):
            batch = message_sequence_to_summarize[i:i+batch_size]
            if len(batch) == 0:
                continue
            logger.info(f"Summarizing batch {i//batch_size + 1}/{num_batches} ({len(batch)} messages)")
            batch_summary = summarize_messages(
                agent_state,
                message_sequence_to_summarize=batch,
                existing_file_uris=existing_file_uris,
            )
            summaries.append(batch_summary)

        # Combine all summaries into one
        if len(summaries) == 1:
            return summaries[0]
        else:
            combined = " | ".join(summaries)
            # If combined is still too long, summarize the summaries
            combined_tokens = count_tokens(combined)
            if combined_tokens > max_summary_tokens:
                logger.info(f"Combined summaries still too long ({combined_tokens} tokens), re-summarizing")
                # Create a simple message to summarize the summaries
                summary_messages = [
                    Message(
                        agent_id=agent_state.id,
                        role=MessageRole.user,
                        content=[TextContent(text=s)]
                    ) for s in summaries
                ]
                return summarize_messages(
                    agent_state,
                    message_sequence_to_summarize=summary_messages,
                    existing_file_uris=existing_file_uris,
                )
            return combined

    dummy_agent_id = agent_state.id
    message_sequence = [
        Message(
            agent_id=dummy_agent_id,
            role=MessageRole.system,
            content=[TextContent(text=summary_prompt)],
        ),
        Message(
            agent_id=dummy_agent_id,
            role=MessageRole.assistant,
            content=[TextContent(text=MESSAGE_SUMMARY_REQUEST_ACK)],
        ),
        Message(
            agent_id=dummy_agent_id,
            role=MessageRole.user,
            content=[TextContent(text=summary_input)],
        ),
    ]

    # TODO: We need to eventually have a separate LLM config for the summarizer LLM
    llm_config_no_inner_thoughts = agent_state.llm_config.model_copy(deep=True)
    llm_config_no_inner_thoughts.put_inner_thoughts_in_kwargs = False
    # response = create(
    #     llm_config=llm_config_no_inner_thoughts,
    #     messages=message_sequence,
    #     stream=False,
    #     summarizing=True
    # )
    llm_client = LLMClient.create(
        llm_config=llm_config_no_inner_thoughts,
    )
    response = llm_client.send_llm_request(
        messages=message_sequence,
        existing_file_uris=existing_file_uris,
    )

    printd(f"summarize_messages gpt reply: {response.choices[0]}")
    reply = response.choices[0].message.content
    return reply
