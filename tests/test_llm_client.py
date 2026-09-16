import pytest
from agent.config import Settings
from agent.llm_client import get_llm_client, get_model_name, TOOLS_SCHEMA

def test_config_carrega_defaults():
    """Valida se valores padrão funcionam quando não há variáveis customizadas."""
    s = Settings()
    assert "googleapis.com" in s.LLM_BASE_URL
    assert "gemini" in s.LLM_MODEL

def test_llm_client_lanca_erro_sem_api_key(monkeypatch):
    """Garante que sem chave de API uma exceção amigável seja levantada."""
    from agent import config
    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "")
    
    with pytest.raises(RuntimeError) as exc_info:
        get_llm_client()
    
    assert "Chave de API não configurada" in str(exc_info.value)

def test_tools_schema_tem_4_ferramentas():
    """Garante que o TOOLS_SCHEMA declare exatamente as 4 ferramentas do SPEC."""
    assert len(TOOLS_SCHEMA) == 4
    nomes_tools = [t["function"]["name"] for t in TOOLS_SCHEMA]
    assert "tool_sql_query" in nomes_tools
    assert "tool_analise_risco" in nomes_tools
    assert "tool_gerar_voucher" in nomes_tools
    assert "tool_resumo_operacional" in nomes_tools
