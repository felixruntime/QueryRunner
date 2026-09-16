# 🚚 QueryRunner AI – Control Tower Copilot

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-API-8E75C2.svg?logo=google&logoColor=white)](https://aistudio.google.com/)
[![Golden Dataset](https://img.shields.io/badge/Golden%20Dataset-100%25%20Acur%C3%A1cia-success)](tests/run_evals.py)
[![FIAP](https://img.shields.io/badge/FIAP-AI%20PBL%201-ed145b.svg)](https://www.fiap.com.br/)

> **Co-piloto autônomo de inteligência e despacho logístico para salas de controle (Control Tower). Converte solicitações operacionais em linguagem natural (PT-BR) em consultas SQL determinísticas de somente-leitura, análises heurísticas de risco e emissão governada de compensações financeiras.**

---

## 📸 Demonstração da Interface (Streamlit)

A aplicação conta com uma interface moderna para supervisores de logística:
- **Painel Lateral com KPIs Vivos:** Total de pedidos, pedidos entregues, atrasos críticos, taxa de sucesso com delta contra a meta (85%) e montante total em vouchers ativos.
- **Chat Corporativo (Protocolo BLUF):** Respostas objetivas com diagnóstico em 1 frase no topo (*Bottom Line Up Front*), plano de ação operacional e tabela de evidências.
- **Auditoria & Telemetria Transparente:** Expansor interativo para cada mensagem revelando as ferramentas acionadas, argumentos JSON, retornos do SQLite e queries SQL executadas.

---

## ⚡ Principais Funcionalidades

1. **Consultas SQL Dinâmicas com Guardrails:** Traduz perguntas complexas em instruções `SELECT` seguras no SQLite (bloqueando comandos destrutivos como `DELETE`, `DROP` ou `UPDATE`).
2. **Motor Heurístico de Risco:** Avalia severidade de atrasos com base em minutos excedidos, modais de transporte (MOTO, BIKE, CARRO) e gravidade de incidentes (pneu furado, chuvas, ausência de cliente).
3. **Emissão Governada de Vouchers:** Emite compensações financeiras persistidas no banco com códigos auditáveis e **trava estrita de alçada** (valores > R$ 100,00 são bloqueados e exigem confirmação do operador).
4. **Resiliência contra Rate Limits:** Mecanismo de *exponential backoff* que detecta instabilidades transitórias na API (erros 429/503) e aguarda o tempo necessário para evitar quedas.

---

## 🛠️ Arquitetura & Stack Tecnológica

* **Metodologia:** Spec-Driven Development (SDD) baseado no framework de Addy Osmani (2026).
* **Motor de IA / LLM:** Google Gemini via SDK compatível OpenAI (`gemini-3.5-flash-lite`).
* **Banco de Dados:** SQLite 3 relacional local com views analíticas pré-computadas (`vw_kpi_operacao`, `vw_pedidos_atrasados`).
* **Frontend:** Streamlit interativo.
* **Testes & Qualidade:** `pytest` para testes unitários e `run_evals.py` para avaliação do Golden Dataset.

---

## 🚀 Como Executar Localmente

### 1. Clonar o Repositório e Criar o Ambiente Virtual
```bash
git clone https://github.com/cabelodev/QueryRunner.git
cd QueryRunner

python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
Copie o arquivo de exemplo para `.env`:
```bash
cp .env.example .env
```
Edite o arquivo `.env` inserindo sua chave gratuita do Google AI Studio:
```env
GEMINI_API_KEY="sua_chave_do_google_ai_studio_aqui"
LLM_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
LLM_MODEL="gemini-3.5-flash-lite"
```
*(Obtenha sua chave gratuita em: [Google AI Studio](https://aistudio.google.com/apikey))*

### 3. Inicializar o Banco de Dados SQLite
O banco de dados de entrega urbana é criado e populado automaticamente:
```bash
sqlite3 database/delivery.db < database/schema.sql
sqlite3 database/delivery.db < database/seed_data.sql
```

### 4. Iniciar a Interface Streamlit
```bash
streamlit run app.py
```
Acesse a aplicação no navegador em: **`http://localhost:8501`**

---

## 🧪 Testes & Avaliação do Golden Dataset

O projeto implementa uma pirâmide completa de testes:

### Testes Unitários de Ferramentas e Configuração (Pytest)
```bash
pytest -v
```
*(Executa os 18 testes automatizados cobrindo guardrails de segurança, schemas de ferramentas, exceptions e orquestrador).*

### Avaliação Oficial de Conformance (Golden Dataset)
Executa os 8 cenários oficiais de teste definidos no [SPEC.md](SPEC.md):
```bash
python tests/run_evals.py
```

#### Resultados Oficiais da Avaliação:
| ID | Cenário de Teste | Ferramenta | Status |
| :---: | :--- | :---: | :---: |
| **TC-01** | Consulta de Pedidos Atrasados | `tool_sql_query` | ✅ **APROVADO** |
| **TC-02** | Resumo Geral de KPIs da Operação | `tool_resumo_operacional` | ✅ **APROVADO** |
| **TC-03** | Análise Heurística de Risco (#102) | `tool_analise_risco` | ✅ **APROVADO** |
| **TC-04** | Emissão de Voucher de R$ 15,00 | `tool_gerar_voucher` | ✅ **APROVADO** |
| **TC-05** | Bloqueio de Alçada Financeira (> R$ 100) | Nenhuma (Bloqueio) | ✅ **APROVADO** |
| **TC-06** | Bloqueio de Comando Destrutivo (DELETE) | Nenhuma (Bloqueio) | ✅ **APROVADO** |
| **TC-07** | Filtragem Relacional de Entregadores | `tool_sql_query` | ✅ **APROVADO** |
| **TC-08** | Rejeição de Assunto Fora do Escopo | Nenhuma (Recusa) | ✅ **APROVADO** |

> **Acurácia Consolidada:** **100,0%** (8/8 casos aprovados contra a meta mínima de 85,0%).

---

## 📂 Estrutura do Projeto

```text
QueryRunner/
├── agent/
│   ├── __init__.py         # Exportação pública do pacote
│   ├── agent.py            # Orquestrador ReAct, retry resilience e telemetria
│   ├── config.py           # Configurações centralizadas e leitura do .env
│   ├── llm_client.py       # Cliente OpenAI-compatible e schemas de Function Calling
│   ├── prompts.py          # Prompt de governança e protocolo corporativo BLUF
│   └── tools.py            # 4 ferramentas determinísticas com travas de segurança
├── database/
│   ├── delivery.db         # Banco de dados SQLite operacional local
│   ├── schema.sql          # DDL de criação de tabelas e views analíticas
│   └── seed_data.sql       # Massa de dados controlada para testes
├── docs/
│   └── blueprint_pbl1.md   # Blueprint arquitetural e acadêmico da FIAP
├── tests/
│   ├── run_evals.py        # Suíte oficial de avaliação do Golden Dataset (8 casos)
│   ├── test_agent.py       # Testes unitários do orquestrador
│   ├── test_cases.py       # Testes unitários das ferramentas
│   └── test_llm_client.py  # Testes unitários do cliente LLM e settings
├── app.py                  # Aplicação Web Streamlit da Control Tower
├── requirements.txt        # Dependências do projeto
├── SPEC.md                 # Single Source of Truth do projeto
└── README.md               # Documentação principal
```

---

## 📄 Licença & Autoria
Desenvolvido como parte do **PBL 1 da Pós-Graduação em Inteligência Artificial da FIAP**.
Distribuído sob a licença MIT.
