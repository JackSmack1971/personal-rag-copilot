from src.ui.settings import update_field
from src.config.runtime_config import config_manager


def test_toggle_hybrid_mode() -> None:
    original = config_manager.as_dict()
    settings = original
    settings, _ = update_field("retrieval_mode", "lexical", settings)
    assert config_manager.get("retrieval_mode") == "lexical"
    settings, _ = update_field("retrieval_mode", "hybrid", settings)
    assert config_manager.get("retrieval_mode") == "hybrid"
    config_manager.set_runtime_overrides({})
