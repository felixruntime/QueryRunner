-- ====================================================================
-- QueryRunner AI - Seed Data (Massa de Testes Controlada)
-- Alinhado aos Critérios de Aceite da Seção 5 do SPEC.md
-- ====================================================================

-- 1. Inserção de Entregadores Parceiros em São Paulo
INSERT INTO entregadores (id, nome, modal, regiao_atuacao, avaliacao, status) VALUES
(1, 'Carlos Silva', 'MOTO', 'Centro', 4.9, 'DISPONIVEL'),
(2, 'Mariana Costa', 'MOTO', 'Centro', 4.8, 'DISPONIVEL'),
(3, 'Lucas Oliveira', 'BIKE', 'Pinheiros', 4.7, 'EM_ROTA'),
(4, 'Rafael Souza', 'CARRO', 'Zona Sul', 4.9, 'DISPONIVEL'),
(5, 'Juliana Mendes', 'MOTO', 'Zona Leste', 4.6, 'OFFLINE');

-- 2. Inserção de Pedidos (IDs explícitos para bater com os testes do SPEC.md)
INSERT INTO pedidos (id, cliente_nome, entregador_id, origem, destino, valor_total, taxa_entrega, status, tempo_estimado_min, tempo_decorrido_min, criado_em) VALUES
-- Pedidos Entregues com Sucesso (Padrão)
(101, 'Ana Paula Santos', 1, 'Bela Vista', 'Consolação', 65.00, 8.50, 'ENTREGUE', 25, 22, '2026-09-10T11:00:00Z'),
(104, 'Marcos Vinicius', 4, 'Moema', 'Vila Mariana', 120.00, 14.00, 'ENTREGUE', 35, 30, '2026-09-10T11:15:00Z'),
(106, 'Fernanda Lima', 1, 'República', 'Higienópolis', 45.00, 7.00, 'ENTREGUE', 20, 18, '2026-09-10T11:30:00Z'),

-- Pedidos Críticos / Atrasados (Para os Casos de Teste TC-01, TC-03 e TC-04)
(102, 'Bruno Alcantara', 3, 'Pinheiros', 'Jardins', 89.90, 10.00, 'ATRASADO', 30, 55, '2026-09-10T11:40:00Z'),
(103, 'Carla Prado', 2, 'Sé', 'Liberdade', 190.00, 15.00, 'ATRASADO', 25, 45, '2026-09-10T11:45:00Z'),
(105, 'Diego Ferreira', 3, 'Vila Madalena', 'Perdizes', 52.00, 9.00, 'ATRASADO', 30, 60, '2026-09-10T11:50:00Z'),

-- Pedido em Rota Normal
(107, 'Patricia Gomes', 2, 'Santa Cecília', 'Bom Retiro', 38.00, 6.50, 'EM_ROTA', 25, 10, '2026-09-10T12:00:00Z'),

-- Pedido Cancelado
(108, 'Roberto Dias', NULL, 'Ipiranga', 'Aclimação', 75.00, 11.00, 'CANCELADO', 30, 5, '2026-09-10T10:30:00Z');

-- 3. Inserção de Incidentes em Rota
-- Pedido 102 possui incidentes combinados (Pneu Furado + Chuva) para o caso TC-03
INSERT INTO incidentes (id, pedido_id, tipo, descricao, gravidade, registrado_em) VALUES
(1, 102, 'PNEU_FURADO', 'Pneu traseiro da bike furou na subida da Rua Augusta.', 'ALTA', '2026-09-10T12:05:00Z'),
(2, 102, 'CHUVAS_FORTES', 'Chuva torrencial impossibilitou travessia segura.', 'MEDIA', '2026-09-10T12:15:00Z'),
(3, 103, 'ATRASO_TRANSITO', 'Trânsito totalmente parado na Av. Radial Leste.', 'MEDIA', '2026-09-10T12:00:00Z'),
(4, 105, 'CLIENTE_AUSENTE', 'Entregador aguardou 15 min na portaria sem resposta do cliente.', 'ALTA', '2026-09-10T12:20:00Z');

-- 4. Inserção de Vouchers de Compensação Emitidos
INSERT INTO vouchers (id, pedido_id, cliente_nome, valor, codigo, motivo, status, emitido_em) VALUES
(1, 101, 'Ana Paula Santos', 15.00, 'COMP-101-A1B2', 'Atraso de 10 min na entrega anterior', 'ATIVO', '2026-09-09T18:00:00Z'),
(2, 104, 'Marcos Vinicius', 25.00, 'COMP-104-C3D4', 'Embalagem de comida amassada pelo motoboy', 'ATIVO', '2026-09-09T19:30:00Z'),
(3, 106, 'Fernanda Lima', 10.00, 'COMP-106-E5F6', 'Cortesia por instabilidade no app', 'UTILIZADO', '2026-09-08T14:00:00Z');
