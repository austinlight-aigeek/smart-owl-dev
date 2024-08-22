from pathlib import Path
from typing import Any, Dict

from yaml import safe_load

PACKAGE_ROOT = Path(__file__).parent
CONFIG_MODELS_PATH = PACKAGE_ROOT / "models.yaml"
CONFIG_PROMPS_PATH = PACKAGE_ROOT / "prompts.yaml"
CONFIG_MEMORIES_PATH = PACKAGE_ROOT / "memories.yaml"


def fetch_config_file(cfg_path: Path) -> Dict[Any, Any]:
    """Parse YAML containing the package configuration."""
    if cfg_path:
        with open(cfg_path, "r", encoding="utf-8") as conf_file:
            parsed_config = safe_load(conf_file)
            return parsed_config
    raise OSError(f"Did not find config file at path: {cfg_path}")


config_models = fetch_config_file(CONFIG_MODELS_PATH)
config_prompts = fetch_config_file(CONFIG_PROMPS_PATH)
config_memories = fetch_config_file(CONFIG_MEMORIES_PATH)

available_models = {
    provider: config_models["providers"][provider]["models"]
    for provider in set({provider for provider in config_models["providers"]})
}
available_memories = [memory for memory in config_memories["type_memories"]]
default_memory_type = {
    "memory_type": "ConversationBufferMemory",
    "parameters": {"memory_key": "messages", "return_messages": True},
}
default_model_type = {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "parameters": {
        "temperature": 0,
        "model_kwargs": {
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
        },
    },
}
default_prompt_template_type = {
    "human_message_prompt_template": {"variable_name": "content", "content": "{content}"},
    "system_message_prompt_template": {"variable_name": None, "content": None},
}
