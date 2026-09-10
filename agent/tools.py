"""
QueryRunner AI - Agent Tools
Metodologia: Spec-Driven Development (conforme Seção 3 do SPEC.md)
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

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
            
            

    
