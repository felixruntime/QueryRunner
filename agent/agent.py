"""
QueryRunner AI - Agent Orchestrator (Core Loop)
Metodologia: Spec-Driven Development (conforme Seções 3, 4 e 5 do SPEC.md)
"""

import json
import logging
import re
import time
from typing import Dict, Any, List, Optional
from openai import OpenAI

from .config import settings
from .llm_client import get_llm_client, get_model_name, TOOLS_SCHEMA
from .prompts import SYSTEM_PROMPT
from .tools import (
    tool_sql_query,
    tool_analise_risco,
    tool_gerar_voucher,
    tool_resumo_operacional,
)

logger = logging.getLogger(__name__)

# Mapeamento oficial de despacho de ferramentas
AVAILABLE_TOOLS = {
    "tool_sql_query": tool_sql_query,
    "tool_analise_risco": tool_analise_risco,
    "tool_gerar_voucher": tool_gerar_voucher,
    "tool_resumo_operacional": tool_resumo_operacional,
}


class QueryRunnerAgent:
    """
    Agente de despacho e inteligência operacional para logística urbana.
    Executa o loop de Function Calling governado com o Google Gemini / OpenAI.
    """

    def __init__(
        self,
        client: Optional[OpenAI] = None,
        model: Optional[str] = None,
        system_prompt: str = SYSTEM_PROMPT,
        max_iterations: int = 5,
    ):
        self.client = client or get_llm_client()
        self.model = model or get_model_name()
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations

    def run(
        self,
        user_prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Executa uma solicitação do operador através do loop de raciocínio e ferramentas.

        Retorna um dicionário estruturado:
        - `response`: Resposta textual final formatada no protocolo BLUF
        - `tool_calls_executed`: Lista de ferramentas executadas com argumentos e retornos
        - `iterations`: Número de iterações realizadas no loop
        - `status`: 'success', 'error' ou 'max_iterations_reached'
        - `messages`: Histórico completo da conversa gerada nesta execução
        """
        # Inicializa o contexto da conversa com o prompt de governança do sistema
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Adiciona histórico anterior, se houver
        if chat_history:
            messages.extend(chat_history)

        # Adiciona o novo prompt do operador
        messages.append({"role": "user", "content": user_prompt})

        tool_calls_executed: List[Dict[str, Any]] = []
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1

            # Chamada resiliente ao modelo com retry para erros transitórios (ex.: 503, 429)
            response = None
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=TOOLS_SCHEMA,
                        tool_choice="auto",
                        temperature=0.1,  # Baixa temperatura para determinismo e conformidade operacional
                    )
                    break
                except Exception as e:
                    err_msg = str(e)
                    is_transient = any(code in err_msg for code in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "high demand", "Quota exceeded"])
                    if is_transient and attempt < max_retries:
                        # Extrai o tempo de espera informado pelo Google (ex: "retry in 19.6s")
                        delay_match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_msg, re.IGNORECASE)
                        if delay_match:
                            sleep_time = float(delay_match.group(1)) + 1.5
                        elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                            sleep_time = 15.0 * attempt
                        else:
                            sleep_time = 2.0 * attempt

                        logger.warning(
                            f"Instabilidade transitória na API ({err_msg}). "
                            f"Aguardando {sleep_time:.1f}s antes da tentativa {attempt + 1}/{max_retries}..."
                        )
                        time.sleep(sleep_time)
                        continue
                    logger.error(f"Erro definitivo na comunicação com a API do LLM: {e}")
                    return {
                        "response": f"Erro de comunicação com o provedor de IA: {str(e)}",
                        "tool_calls_executed": tool_calls_executed,
                        "iterations": iteration,
                        "status": "error",
                        "messages": messages,
                    }

            choice = response.choices[0]
            message = choice.message

            # Se o modelo não requisitou ferramentas, temos a resposta final
            if not message.tool_calls:
                final_content = message.content or ""
                messages.append({"role": "assistant", "content": final_content})
                return {
                    "response": final_content,
                    "tool_calls_executed": tool_calls_executed,
                    "iterations": iteration,
                    "status": "success",
                    "messages": messages,
                }

            # Registra a mensagem de solicitação de tool_calls do assistente
            messages.append(message)

            # Executa cada ferramenta solicitada pelo modelo
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                raw_args = tool_call.function.arguments or "{}"

                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}

                tool_func = AVAILABLE_TOOLS.get(func_name)

                if not tool_func:
                    result = {
                        "status": "error",
                        "message": f"Ferramenta '{func_name}' não reconhecida ou não permitida.",
                    }
                else:
                    try:
                        result = tool_func(**args)
                    except Exception as e:
                        logger.exception(f"Exceção inesperada ao executar {func_name}: {e}")
                        result = {
                            "status": "error",
                            "message": f"Erro na execução da ferramenta {func_name}: {str(e)}",
                        }

                # Registra na telemetria de auditoria
                tool_calls_executed.append({
                    "tool": func_name,
                    "arguments": args,
                    "result": result,
                })

                # Devolve o resultado da ferramenta para o contexto do LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        # Caso exceda o limite máximo de iterações
        return {
            "response": (
                "Atenção: Limite máximo de iterações operacionais atingido sem convergência final. "
                "Por favor, refine sua instrução ou consulte o suporte da Control Tower."
            ),
            "tool_calls_executed": tool_calls_executed,
            "iterations": iteration,
            "status": "max_iterations_reached",
            "messages": messages,
        }


def run_agent(
    user_prompt: str,
    chat_history: Optional[List[Dict[str, Any]]] = None,
    max_iterations: int = 5,
) -> Dict[str, Any]:
    """
    Função helper de alto nível para executar uma solicitação no QueryRunner AI.
    """
    agent = QueryRunnerAgent(max_iterations=max_iterations)
    return agent.run(user_prompt=user_prompt, chat_history=chat_history)


__all__ = ["QueryRunnerAgent", "run_agent", "AVAILABLE_TOOLS"]
