"""
QueryRunner AI - Agent Tools
Metodologia: Spec-Driven Development (conforme Seção 3 do SPEC.md)
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid


# Caminho padrão do banco de dadosSQLite
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "database" / "delivery.db"

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Obtém conexão com o banco de dados SQLite retornando linhas como dicionarios"""

    target_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def tool_sql_query(query: str, db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Executa consultas SQL de leitura (SELECT) no banco de dados SQLite ativo.
    
    Restrições de Segurança (Guardrails da Seção 4 do SPEC.md):
    - Apenas consultas de leitura (SELECT, WITH, EXPLAIN) são permitidas.
    - Bloqueia comandos destrutivos: DROP, DELETE, INSERT, UPDATE, ALTER, etc.
    """
    
    clean_query = query.strip()
    
    # 1. Guardrail de Segurança: Bloqueia comandos destrutivos ou de modificação
    blocked_patterns = [
        r"\bDROP\b",
        r"\bDELETE\b",
        r"\bINSERT\b",
        r"\bUPDATE\b", 
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b"
    ]
    for pattern in blocked_patterns:
        if re.search(pattern, clean_query, re.IGNORECASE):
            return {
                "status": "error",
                "message": f"Comando bloqueado por política de segurança: {pattern} não é permitido.",
                "query": clean_query
            }

    
    # 2. Garante que a query inicia com comandos de leitura válidos
    if not re.match(r"^(SELECT|WITH|EXPLAIN|PRAGMA)", clean_query, re.IGNORECASE):
        return {
            "status": "error",
            "message": "Comando inválido: apenas consultas SELECT, WITH, EXPLAIN e PRAGMA são permitidas.",
            "query": clean_query
        }
    
    # 3. Execução segura da query
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(clean_query)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]

            return {
                "status": "success",
                "query": clean_query,
                "rows_found": len(results),
                "rows": results
            }
    except sqlite3.Error as e:
        return {
            "status": "error",
            "message": f"Erro de sintaxe ou de execução SQL: {str(e)}",
            "query": clean_query
        }
            
def tool_analise_risco(pedido_id: int, db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Avalia a severidade operacional de um pedido com base em atraso
    e incidentes registrados, sugerindo a ação cabível.
    
    Conforme especificado na Seção 3.2 do SPEC.md:
    Retorna: score_risco, classificacao (BAIXO|MEDIO|CRITICO), fatores e acao_sugerida. 
    """

    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()

            # 1. Busca dados do pedido
            cursor.execute("""
                SELECT id, cliente_nome, status, tempo_estimado_min, tempo_decorrido_min
                FROM pedidos
                WHERE id = ?
                """, (pedido_id,))
            pedido = cursor.fetchone()

            if not pedido:
                return {"status": "error",
                "message": f"Pedido #{pedido_id} não encontrado na base de dados.",
                "pedido_id": pedido_id
                }
            
            # 2. Se foi finalizado ou cancelado, risco nulo
            if pedido['status'] in ('ENTREGUE', 'CANCELADO'):
                is_entregue = (pedido['status'] == 'ENTREGUE')
                return {
                    "status": "success",
                    "pedido_id": pedido_id,
                    "cliente": pedido["cliente_nome"],
                    "score_risco": 0.0,
                    "classificacao": "BAIXO",
                    "fatores": [f"Pedido #{pedido_id} entregue com sucesso." if is_entregue else f"Pedido #{pedido_id} cancelado."],
                    "acao_sugerida": "Nenhuma ação necessária." if is_entregue else "Verificar se estorno financeiro foi processado."
                }
            
            # 3. Busca Incidentes vinculados ao pedido
            cursor.execute("""
                SELECT tipo, descricao, gravidade
                FROM incidentes
                WHERE pedido_id = ?
                """, (pedido_id,))
            incidentes = cursor.fetchall()

            # 4. Calcula o score de risco
            score = 0.0
            fatores: List[str] = []

            # Avalia atraso
            atraso_min = pedido['tempo_decorrido_min'] - pedido['tempo_estimado_min']
            if atraso_min > 20:
                score += 45.0
                fatores.append(f"Alto atraso operacional: {atraso_min} minutos acima do estimado.")
            elif atraso_min > 0:
                score += 25.0
                fatores.append(f"Atraso moderado: {atraso_min} minutos acima do estimado.")
            
            # Avalia incidentes
            for inc in incidentes:
                if inc["gravidade"] == "ALTA":
                    score += 35.0
                    fatores.append(f"Incidente Grave ({inc['tipo']}): {inc['descricao']}")
                elif inc["gravidade"] == "MEDIA":
                    score += 20.0
                    fatores.append(f"Incidente Médio ({inc['tipo']}): {inc['descricao']}")
                else:
                    score += 10.0
                    fatores.append(f"Incidente Leve ({inc['tipo']}): {inc['descricao']}")
            score_final = min(score, 100.0)
            
            # 5. Classificação e Ação Sugerida
            if score_final >= 60.0:
                classificacao = "CRITICO"
                acao_sugerida = "Prioridade máxima: acionar suporte ao cliente e emitir voucher compensatório (sugestão R$ 15 a R$ 25)."
            elif score_final >= 30.0:
                classificacao = "MEDIO"
                acao_sugerida = "Monitorar rota e notificar entregador via chat para posicionamento."
            else:
                classificacao = "BAIXO"
                acao_sugerida = "Operação dentro dos parâmetros toleráveis. Manter fluxo normal."
            return {
                "status": "success",
                "pedido_id": pedido_id,
                "cliente": pedido["cliente_nome"],
                "score_risco": score_final,
                "classificacao": classificacao,
                "fatores": fatores if fatores else ["Nenhum fator anômalo registrado."],
                "acao_sugerida": acao_sugerida
            }
    except sqlite3.Error as e:
        return {
            "status": "error",
            "message": f"Erro de banco de dados na análise de risco: {str(e)}",
            "pedido_id": pedido_id
        }

def tool_gerar_voucher(
    pedido_id: int, 
    valor: float, 
    motivo: str, 
    db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Emite uma compensação financeira vinculada a um pedido prejudicado,
    inserindo um registro auditável na tabela 'vouchers'.
    
    Restrições de Segurança (Seções 3.3 e 4 do SPEC.md):
    - Alçada máxima de emissão autônoma: R$ 100,00.
    - Valores acima de R$ 100,00 exigem confirmação explícita do operador humano.
    """
    # 1. Validação de valor positivo
    if valor <= 0:
        return {
            "status": "error",
            "message": "O valor do voucher deve ser maior que zero (R$ > 0.00).",
            "pedido_id": pedido_id,
            "valor": valor
        }

    # 2. Guardrail de Alçada Financeira (Ask First do SPEC.md)
    if valor > 100.0:
        return {
            "status": "requires_approval",
            "message": f"Alçada excedida: a emissão de voucher no valor de R$ {valor:.2f} requer aprovação humana prévia do operador (limite autônomo é de R$ 100,00).",
            "pedido_id": pedido_id,
            "valor": valor,
            "motivo": motivo
        }

    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()

            # 3. Verifica se o pedido existe e obtém o nome do cliente
            cursor.execute("SELECT id, cliente_nome FROM pedidos WHERE id = ?;", (pedido_id,))
            pedido = cursor.fetchone()

            if not pedido:
                return {
                    "status": "error",
                    "message": f"Pedido #{pedido_id} não encontrado para vinculação de voucher.",
                    "pedido_id": pedido_id
                }

            cliente_nome = pedido["cliente_nome"]

            # 4. Gera código único e timestamp ISO-8601
            # Exemplo de código: COMP-105-X9F2
            codigo_hash = uuid.uuid4().hex[:4].upper()
            codigo = f"COMP-{pedido_id}-{codigo_hash}"
            emitido_em = datetime.now().isoformat()

            # 5. Insere o voucher de forma auditável no banco
            cursor.execute("""
                INSERT INTO vouchers (pedido_id, cliente_nome, valor, codigo, motivo, status, emitido_em)
                VALUES (?, ?, ?, ?, ?, 'ATIVO', ?);
            """, (pedido_id, cliente_nome, valor, codigo, motivo, emitido_em))
            
            conn.commit()  # Persiste a transação no SQLite

            return {
                "status": "success",
                "codigo": codigo,
                "pedido_id": pedido_id,
                "cliente": cliente_nome,
                "valor": valor,
                "motivo": motivo,
                "emitido_em": emitido_em,
                "message": f"Voucher {codigo} de R$ {valor:.2f} emitido com sucesso para {cliente_nome}."
            }

    except sqlite3.Error as e:
        return {
            "status": "error",
            "message": f"Erro de banco de dados ao emitir voucher: {str(e)}",
            "pedido_id": pedido_id
        }

def tool_resumo_operacional(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Retorna os principais indicadores consolidados de saúde da operação.
    Consulta diretamente a view analítica 'vw_kpi_operacao'.
    
    Conforme especificado na Seção 3.4 do SPEC.md:
    Retorna: total_pedidos, entregues, atrasados, cancelados, taxa_sucesso_pct e total_vouchers_brl.
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vw_kpi_operacao;")
            row = cursor.fetchone()

            if not row:
                return {
                    "status": "error",
                    "message": "Nenhum dado consolidado retornado pela view de KPIs operacionais."
                }

            kpis = dict(row)
            return {
                "status": "success",
                "kpis": kpis,
                "message": (
                    f"Operação com {kpis['total_pedidos']} pedidos: "
                    f"{kpis['total_entregues']} entregues ({kpis['taxa_sucesso_pct']}%), "
                    f"{kpis['total_atrasados']} atrasados e {kpis['total_cancelados']} cancelados. "
                    f"Total de vouchers ativos: R$ {kpis['total_vouchers_brl']:.2f}."
                )
            }
    except sqlite3.Error as e:
        return {
            "status": "error",
            "message": f"Erro de banco de dados ao obter resumo operacional: {str(e)}"
        }


            
            
    
            

                
    
