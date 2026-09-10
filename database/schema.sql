-- ====================================================================
-- QueryRunner AI - Database Schema (SQLite)
-- Metodologia: Spec-Driven Development (conforme Seção 2 do SPEC.md)
-- ====================================================================

-- 1. Habilita a validação estrita de integridade referencial no SQLite
PRAGMA foreign_keys = ON;

-- --------------------------------------------------------------------
-- ETAPA 1: Tabela Independente (Pai) - Entregadores Parceiros
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS entregadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    modal TEXT NOT NULL CHECK (modal IN ('MOTO', 'BIKE', 'CARRO')),
    regiao_atuacao TEXT NOT NULL,
    avaliacao REAL CHECK (avaliacao BETWEEN 1.0 AND 5.0),
    status TEXT NOT NULL CHECK (status IN ('DISPONIVEL', 'EM_ROTA', 'OFFLINE'))
);

-- --------------------------------------------------------------------
-- ETAPA 2: Tabela Dependente de Nível 1 - Pedidos / Corridas
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_nome TEXT NOT NULL,
    entregador_id INTEGER,
    origem TEXT NOT NULL,
    destino TEXT NOT NULL,
    valor_total REAL NOT NULL,
    taxa_entrega REAL NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('CRIADO', 'COLETA', 'EM_ROTA', 'ENTREGUE', 'ATRASADO', 'CANCELADO')),
    tempo_estimado_min INTEGER NOT NULL,
    tempo_decorrido_min INTEGER NOT NULL DEFAULT 0,
    criado_em TEXT NOT NULL,
    FOREIGN KEY (entregador_id) REFERENCES entregadores(id)
);

-- --------------------------------------------------------------------
-- ETAPA 3: Tabela Dependente de Nível 2 - Incidentes em Rota
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS incidentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('ATRASO_TRANSITO', 'PNEU_FURADO', 'CHUVAS_FORTES', 'CLIENTE_AUSENTE', 'EXTRAVIO')),
    descricao TEXT NOT NULL,
    gravidade TEXT NOT NULL CHECK (gravidade IN ('BAIXA', 'MEDIA', 'ALTA')),
    registrado_em TEXT NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
);

-- --------------------------------------------------------------------
-- ETAPA 4: Tabela Dependente de Nível 2 - Vouchers de Compensação
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vouchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    cliente_nome TEXT NOT NULL,
    valor REAL NOT NULL CHECK (valor > 0),
    codigo TEXT NOT NULL UNIQUE,
    motivo TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ATIVO', 'UTILIZADO', 'CANCELADO')),
    emitido_em TEXT NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
);

-- --------------------------------------------------------------------
-- ETAPA 5: Views Analíticas de Suporte (Somente-Leitura)
-- --------------------------------------------------------------------

-- View 1: Pedidos em Atraso Crítico
-- Cruza o pedido com o entregador e calcula o tempo de atraso em minutos.
CREATE VIEW IF NOT EXISTS vw_pedidos_atrasados AS
SELECT 
    p.id AS pedido_id,
    p.cliente_nome,
    p.status AS status_pedido,
    p.origem,
    p.destino,
    p.tempo_estimado_min,
    p.tempo_decorrido_min,
    (p.tempo_decorrido_min - p.tempo_estimado_min) AS minutos_atraso,
    e.id AS entregador_id,
    e.nome AS entregador_nome,
    e.modal AS entregador_modal,
    e.regiao_atuacao AS entregador_regiao
FROM pedidos p
LEFT JOIN entregadores e ON p.entregador_id = e.id
WHERE p.status = 'ATRASADO' 
   OR (p.tempo_decorrido_min > p.tempo_estimado_min AND p.status NOT IN ('ENTREGUE', 'CANCELADO'));

-- View 2: KPI Geral da Operação Diária
-- Totaliza o desempenho operacional e o impacto financeiro de vouchers.
CREATE VIEW IF NOT EXISTS vw_kpi_operacao AS
SELECT 
    COUNT(p.id) AS total_pedidos,
    SUM(CASE WHEN p.status = 'ENTREGUE' THEN 1 ELSE 0 END) AS total_entregues,
    SUM(CASE WHEN p.status = 'ATRASADO' OR (p.tempo_decorrido_min > p.tempo_estimado_min AND p.status != 'ENTREGUE') THEN 1 ELSE 0 END) AS total_atrasados,
    SUM(CASE WHEN p.status = 'CANCELADO' THEN 1 ELSE 0 END) AS total_cancelados,
    ROUND(
        (CAST(SUM(CASE WHEN p.status = 'ENTREGUE' THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(p.id), 0)) * 100, 
        1
    ) AS taxa_sucesso_pct,
    COALESCE((SELECT SUM(valor) FROM vouchers WHERE status = 'ATIVO'), 0.0) AS total_vouchers_brl
FROM pedidos p;
