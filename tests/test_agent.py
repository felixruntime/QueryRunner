"""
QueryRunner AI - Unit Tests for Agent Orchestrator
Valida o loop ReAct, despacho de ferramentas, limite de iterações e tratamento de erros.
"""

import json
from unittest.mock import MagicMock
import pytest

from agent.agent import QueryRunnerAgent, run_agent, AVAILABLE_TOOLS


def _create_mock_completion(content=None, tool_calls=None):
    """Auxiliar para simular respostas do cliente OpenAI."""
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    return response


def _create_mock_tool_call(name: str, arguments: dict, call_id: str = "call_123"):
    """Auxiliar para simular um objeto ToolCall retornado pelo modelo."""
    function = MagicMock()
    function.name = name
    function.arguments = json.dumps(arguments)

    tool_call = MagicMock()
    tool_call.id = call_id
    tool_call.function = function
    return tool_call


def test_agent_resposta_direta_sem_tools():
    """Valida fluxo quando o LLM responde diretamente sem chamar ferramentas."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _create_mock_completion(
        content="BLUF: Operação em andamento normalmente."
    )

    agent = QueryRunnerAgent(client=mock_client, model="mock-model")
    result = agent.run("Qual a situação?")

    assert result["status"] == "success"
    assert "Operação em andamento" in result["response"]
    assert result["iterations"] == 1
    assert len(result["tool_calls_executed"]) == 0


def test_agent_executa_tool_calling_com_sucesso():
    """Valida ciclo completo: LLM solicita ferramenta -> agente executa -> LLM sintetiza resposta."""
    mock_client = MagicMock()

    # Turno 1: LLM pede tool_sql_query
    tool_call = _create_mock_tool_call(
        name="tool_sql_query",
        arguments={"query": "SELECT COUNT(*) AS total FROM pedidos;"},
        call_id="call_sql_1",
    )
    res_turno_1 = _create_mock_completion(content=None, tool_calls=[tool_call])

    # Turno 2: LLM recebe o resultado e sintetiza o BLUF final
    res_turno_2 = _create_mock_completion(
        content="BLUF: Existem 8 pedidos cadastrados no banco de dados.",
        tool_calls=None,
    )

    mock_client.chat.completions.create.side_effect = [res_turno_1, res_turno_2]

    agent = QueryRunnerAgent(client=mock_client, model="mock-model")
    result = agent.run("Quantos pedidos temos?")

    assert result["status"] == "success"
    assert "Existem 8 pedidos" in result["response"]
    assert result["iterations"] == 2
    assert len(result["tool_calls_executed"]) == 1
    assert result["tool_calls_executed"][0]["tool"] == "tool_sql_query"
    assert result["tool_calls_executed"][0]["result"]["status"] == "success"


def test_agent_trata_ferramenta_desconhecida():
    """Valida comportamento defensivo caso o modelo alucine o nome de uma ferramenta."""
    mock_client = MagicMock()

    tool_call = _create_mock_tool_call(
        name="ferramenta_inexistente",
        arguments={},
        call_id="call_unknown_1",
    )
    res_turno_1 = _create_mock_completion(content=None, tool_calls=[tool_call])
    res_turno_2 = _create_mock_completion(
        content="BLUF: Houve um erro de ferramenta desconhecida.",
        tool_calls=None,
    )

    mock_client.chat.completions.create.side_effect = [res_turno_1, res_turno_2]

    agent = QueryRunnerAgent(client=mock_client, model="mock-model")
    result = agent.run("Execute algo desconhecido")

    assert result["status"] == "success"
    assert len(result["tool_calls_executed"]) == 1
    assert result["tool_calls_executed"][0]["result"]["status"] == "error"
    assert "não reconhecida" in result["tool_calls_executed"][0]["result"]["message"]


def test_agent_limite_max_iterations():
    """Valida que o agente aborta quando excede o número máximo de iterações configuradas."""
    mock_client = MagicMock()

    # Cria loop infinito onde o modelo sempre pede nova ferramenta
    tool_call = _create_mock_tool_call(
        name="tool_resumo_operacional",
        arguments={},
        call_id="call_loop",
    )
    mock_client.chat.completions.create.return_value = _create_mock_completion(
        content=None,
        tool_calls=[tool_call],
    )

    agent = QueryRunnerAgent(client=mock_client, model="mock-model", max_iterations=3)
    result = agent.run("Teste de loop infinito")

    assert result["status"] == "max_iterations_reached"
    assert result["iterations"] == 3
    assert "Limite máximo de iterações" in result["response"]
