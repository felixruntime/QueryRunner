"""
QueryRunner AI - LLM Client & Tool Calling Schemas
Metodologia: Spec-Driven Development (conforme Seção 3 e 4 do SPEC.md)
"""

from typing import Dict, Any, List, Optional
from openai import OpenAI
from .config import settings

def get_llm_client() -> OpenAI:
    """
    Inicializa e retorna uma instância autenticada do cliente OpenAI
    apontando para o endpoint configurado (Google Gemini por padrão).
    """
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "Chave de API não configurada!\n"
            "Defina 'GEMINI_API_KEY' no seu arquivo .env ou como variável de ambiente.\n"
            "Obtenha sua chave gratuita em: https://aistudio.google.com/apikey"
        )
    return OpenAI(api_key=settings.GEMINI_API_KEY, base_url=settings.LLM_BASE_URL)


def get_model_name() -> str:
    """Retorna o nome do modelo configurado no settings."""
    return settings.LLM_MODEL



# ====================================================================
# DEFINIÇÃO FORMAL DOS SCHEMAS DAS FERRAMENTAS (OpenAI Function Calling)
# ====================================================================

TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "tool_sql_query",
            "description": (
                "Executa consultas SELECT de somente-leitura no banco de dados SQLite local da operação. "
                "Use para consultar pedidos, entregadores, incidentes, vouchers ou views analíticas. "
                "Comandos de escrita ou destrutivos são bloqueados por guardrails."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Instrução SQL SELECT válida para SQLite "
                            "(ex.: \"SELECT * FROM entregadores WHERE modal = 'MOTO' AND status = 'DISPONIVEL'\")"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_analise_risco",
            "description": (
                "Calcula a heurística de risco operacional de um pedido atrasado ou em rota. "
                "Retorna o score de risco (0 a 100), classificação (BAIXO, MEDIO, CRITICO) "
                "e a lista detalhada de fatores agravantes (SLA estourado, chuva, pneu furado, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_id": {
                        "type": "integer",
                        "description": "ID numérico identificador do pedido a ser avaliado.",
                    }
                },
                "required": ["pedido_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_gerar_voucher",
            "description": (
                "Emite um voucher de compensação financeira para o cliente lesado por atraso ou incidente. "
                "Atenção à alçada: valores acima de R$ 100,00 não podem ser emitidos de forma autônoma "
                "sem autorização explícita do operador."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_id": {
                        "type": "integer",
                        "description": "ID numérico do pedido relacionado ao voucher.",
                    },
                    "valor": {
                        "type": "number",
                        "description": "Valor monetário do voucher em reais (ex.: 15.0 para R$ 15,00).",
                    },
                    "motivo": {
                        "type": "string",
                        "description": "Justificativa operacional da compensação (ex.: 'Atraso decorrente de pneu furado').",
                    },
                },
                "required": ["pedido_id", "valor", "motivo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_resumo_operacional",
            "description": (
                "Consulta a view analítica vw_kpi_operacao e retorna o consolidado diário dos KPIs da operação: "
                "total de pedidos, entregues no prazo, atrasados, cancelados, taxa de sucesso percentual "
                "e montante total emitido em vouchers de compensação."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

__all__ = [
    "get_llm_client",
    "get_model_name",
    "TOOLS_SCHEMA",
]

