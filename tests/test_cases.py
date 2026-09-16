import pytest

from agent import (
    tool_sql_query,
    tool_analise_risco,
    tool_gerar_voucher,
    tool_resumo_operacional,
)

# ====================================================================
# TESTES: Tool 1 - tool_sql_query (Leitura e Guardrails)
# ====================================================================
def test_sql_query_executa_leitura_com_sucesso():
    """Valida execução normal de um SELECT no banco."""
    res = tool_sql_query("SELECT COUNT(*) AS total FROM pedidos;")
    assert res["status"] == "success"
    assert res["rows_found"] == 1
    assert res["rows"][0]["total"] >= 8

def test_sql_query_bloqueia_delete():
    """Valida guardrail que impede exclusão de registros (DELETE)."""
    res = tool_sql_query("DELETE FROM pedidos WHERE id = 101;")
    assert res["status"] == "error"
    assert "bloqueado por política de segurança" in res["message"]

def test_sql_query_bloqueia_drop_table():
    """Valida guardrail que impede destruição de tabelas (DROP)."""
    res = tool_sql_query("DROP TABLE entregadores;")
    assert res["status"] == "error"
    assert "bloqueado por política de segurança" in res["message"]

def test_sql_query_trata_erro_de_sintaxe():
    """Valida que erros de sintaxe retornam mensagem amigável sem crash."""
    res = tool_sql_query("SELECT coluna_inexistente FROM pedidos;")
    assert res["status"] == "error"
    assert "Erro de sintaxe ou de execução SQL" in res["message"]

# ====================================================================
# TESTES: Tool 2 - tool_analise_risco (Motor Heurístico)
# ====================================================================
def test_analise_risco_pedido_critico():
    """Valida pedido #102 com múltiplos incidentes e atraso (TC-03 do SPEC.md)."""
    res = tool_analise_risco(102)
    assert res["status"] == "success"
    assert res["classificacao"] == "CRITICO"
    assert res["score_risco"] >= 60.0
    assert len(res["fatores"]) >= 2
    assert "voucher" in res["acao_sugerida"].lower()

def test_analise_risco_pedido_entregue():
    """Valida que pedidos finalizados recebem risco zero e classificação BAIXO."""
    res = tool_analise_risco(101)
    assert res["status"] == "success"
    assert res["classificacao"] == "BAIXO"
    assert res["score_risco"] == 0.0

def test_analise_risco_pedido_inexistente():
    """Valida retorno de erro para ID não cadastrado."""
    res = tool_analise_risco(99999)
    assert res["status"] == "error"
    assert "não encontrado" in res["message"]
    
# ====================================================================
# TESTES: Tool 3 - tool_gerar_voucher (Alçada Financeira)
# ====================================================================
def test_gerar_voucher_dentro_da_alcada():
    """Valida emissão bem-sucedida de voucher <= R$ 100 (TC-04 do SPEC.md)."""
    res = tool_gerar_voucher(pedido_id=105, valor=15.0, motivo="Atraso de 30 minutos")
    assert res["status"] == "success"
    assert res["valor"] == 15.0
    assert res["codigo"].startswith("COMP-105-")
    assert res["cliente"] == "Diego Ferreira"

def test_gerar_voucher_excede_alcada_bloqueia():
    """Valida trava de alçada humana para valores > R$ 100 (TC-05 do SPEC.md)."""
    res = tool_gerar_voucher(pedido_id=103, valor=150.0, motivo="Compensação solicitada")
    assert res["status"] == "requires_approval"
    assert "Alçada excedida" in res["message"]
    assert res["valor"] == 150.0
    
def test_gerar_voucher_valor_invalido():
    """Valida rejeição para valores zerados ou negativos."""
    res = tool_gerar_voucher(pedido_id=101, valor=-10.0, motivo="Inválido")
    assert res["status"] == "error"
    assert "maior que zero" in res["message"]

# ====================================================================
# TESTES: Tool 4 - tool_resumo_operacional (KPIs Gerais)
# ====================================================================
def test_resumo_operacional_retorna_kpis():
    """Valida consulta à view vw_kpi_operacao (TC-02 do SPEC.md)."""
    res = tool_resumo_operacional()
    assert res["status"] == "success"
    kpis = res["kpis"]
    assert kpis["total_pedidos"] >= 8
    assert "taxa_sucesso_pct" in kpis
    assert "total_vouchers_brl" in kpis
