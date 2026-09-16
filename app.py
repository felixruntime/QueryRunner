"""
QueryRunner AI - Control Tower Web Interface
"""

import streamlit as st
from typing import List, Dict, Any

from agent import run_agent, tool_resumo_operacional
from agent.config import settings

# -----------------------------------------------------------------------------
# Configuração Geral da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="QueryRunner AI | Control Tower",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Estilização CSS Personalizada (Modern Dark/Light Control Tower Look)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Estilização Geral */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header e Badges */
    .control-tower-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: #38bdf8;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        border: 1px solid rgba(56, 189, 248, 0.25);
        margin-bottom: 8px;
    }
    
    .kpi-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    
    .sql-pill {
        background-color: #0f172a;
        color: #a5b4fc;
        font-family: monospace;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Gerenciamento de Estado da Sessão (Session State)
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "quick_prompt_input" not in st.session_state:
    st.session_state.quick_prompt_input = None


def carregar_kpis_sidebar():
    """Busca os dados consolidados da view de KPIs no SQLite."""
    try:
        res = tool_resumo_operacional()
        if res.get("status") == "success":
            return res.get("kpis", {})
    except Exception:
        pass
    return {}


# -----------------------------------------------------------------------------
# Barra Lateral (Sidebar) - Painel de Controle e Telemetria
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="control-tower-badge">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10b981;"></span>
            Control Tower Ativa
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("QueryRunner AI")
    st.caption("Co-piloto de Despacho & Inteligência de Última Milha")

    st.markdown("---")

    # KPIs em Tempo Real
    st.subheader("📊 Saúde da Operação (Hoje)")
    kpis = carregar_kpis_sidebar()

    if kpis:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total Pedidos", value=kpis.get("total_pedidos", 0))
            st.metric(label="Entregues", value=kpis.get("total_entregues", 0))
        with col2:
            st.metric(
                label="Sucesso",
                value=f"{kpis.get('taxa_sucesso_pct', 0.0):.1f}%",
                delta=f"{kpis.get('taxa_sucesso_pct', 0.0) - 85.0:.1f}% vs Meta (85%)"
            )
            st.metric(
                label="Atrasados",
                value=kpis.get("total_atrasados", 0),
                delta_color="inverse"
            )

        st.metric(
            label="Total em Vouchers Emitidos",
            value=f"R$ {kpis.get('total_vouchers_brl', 0.0):.2f}",
        )
    else:
        st.info("Banco de dados SQLite inicializado.")

    st.markdown("---")

    # Prompts Rápidos do Golden Dataset
    st.subheader("⚡ Prompts Rápidos de Operação")
    quick_prompts = [
        ("Qual a situação geral da operação hoje?", "📊 Resumo Geral"),
        ("Quantos pedidos estão atrasados agora?", "🚨 Pedidos Atrasados"),
        ("Analise o risco do pedido #102.", "⚠️ Risco Pedido #102"),
        ("Quais entregadores de moto estão disponíveis no Centro?", "🛵 Motos no Centro"),
        ("Gere um voucher de R$ 15 para o pedido #105 por atraso.", "🎟️ Emitir Voucher"),
    ]

    for prompt_text, button_label in quick_prompts:
        if st.button(button_label, use_container_width=True):
            st.session_state.quick_prompt_input = prompt_text
            st.rerun()

    st.markdown("---")

    # Informações Técnicas do Modelo e Limpeza
    st.caption(f"**Modelo LLM:** `{settings.LLM_MODEL}`")
    st.caption(f"**Provedor:** Google AI Studio / Gemini")

    if st.button("🗑️ Limpar Conversa", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.quick_prompt_input = None
        st.rerun()

# -----------------------------------------------------------------------------
# Painel Principal (Chat & Interação)
# -----------------------------------------------------------------------------
st.markdown("## 🚚 Control Tower Dispatch & Analytics")
st.caption(
    "Assistente analítico determinístico com acesso direto ao SQLite, governança de alçadas "
    "e protocolo corporativo **BLUF (Bottom Line Up Front)**."
)

# Renderização do Histórico de Mensagens
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Exibição de Telemetria e Auditoria se disponível
        if msg.get("tool_calls"):
            with st.expander("🔍 Auditoria de Execução & Telemetria", expanded=False):
                st.caption(f"**Iterações executadas:** {msg.get('iterations', 1)}")
                for i, tc in enumerate(msg["tool_calls"], 1):
                    tool_name = tc.get("tool", "")
                    tool_args = tc.get("arguments", {})
                    tool_res = tc.get("result", {})

                    st.markdown(f"**Passo {i}:** `{tool_name}`")
                    st.json({"argumentos": tool_args, "retorno": tool_res})

# Captura de Nova Mensagem do Usuário (seja via chat_input ou quick_prompt)
user_prompt = st.chat_input("Digite sua solicitação operacional (ex: Quais pedidos estão atrasados?)...")

if st.session_state.quick_prompt_input:
    user_prompt = st.session_state.quick_prompt_input
    st.session_state.quick_prompt_input = None

if user_prompt:
    # 1. Registra e renderiza o prompt do usuário
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # 2. Executa o Agente com indicador visual de progresso
    with st.chat_message("assistant"):
        with st.spinner("Analisando bases operacionais e executando ferramentas..."):
            # Monta o histórico compatível para contextualização
            history_payload = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
                if m["role"] in ("user", "assistant")
            ]

            result = run_agent(user_prompt=user_prompt, chat_history=history_payload)
            response_text = result.get("response", "Nenhuma resposta retornada.")
            tool_calls = result.get("tool_calls_executed", [])
            iterations = result.get("iterations", 1)

            st.markdown(response_text)

            # Exibe expander de auditoria da resposta recém-gerada
            if tool_calls:
                with st.expander("🔍 Auditoria de Execução & Telemetria", expanded=False):
                    st.caption(f"**Iterações executadas:** {iterations}")
                    for i, tc in enumerate(tool_calls, 1):
                        tool_name = tc.get("tool", "")
                        tool_args = tc.get("arguments", {})
                        tool_res = tc.get("result", {})

                        st.markdown(f"**Passo {i}:** `{tool_name}`")
                        st.json({"argumentos": tool_args, "retorno": tool_res})

    # 3. Salva no estado da sessão
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "tool_calls": tool_calls,
        "iterations": iterations,
    })
