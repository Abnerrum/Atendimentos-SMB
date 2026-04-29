"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   SISTEMA DE CADASTRO DE ATENDIMENTOS — Samsung SMB                          ║
║   Interface Profissional | SQLite | Dashboard | E-mail Automático            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# Importa os módulos locais
from database import (
    salvar_atendimento,
    carregar_atendimentos,
    contar_atendimentos,
    obter_valor_total,
    estatisticas_por_atendente,
    estatisticas_por_periodo,
    limpar_todos_dados,
)
from email_sender import enviar_confirmacao, email_configurado

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO DE SEGURANÇA PARA SEGREDOS
# ═══════════════════════════════════════════════════════════════════════════════

def get_secret(key, default=None):
    """Evita o erro StreamlitSecretNotFoundError se o arquivo não existir."""
    try:
        val = st.secrets.get(key)
        if val is not None:
            return val
    except Exception:
        pass
    return os.environ.get(key, default)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Cadastro de Atendimentos — Samsung SMB",
    page_icon="📱",
    layout="wide",
)

# Constantes
SENHA_ADMIN = get_secret("ADMIN_PASSWORD", "admin123")

# ═══════════════════════════════════════════════════════════════════════════════
# CSS CUSTOMIZADO
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .header-banner {
        background: linear-gradient(135deg, #034EA2 0%, #002E6E 100%);
        color: white;
        padding: 32px 40px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 28px;
    }
    .header-banner h1 { margin: 0; font-size: 2rem; }
    .header-banner p  { margin: 8px 0 0; opacity: 0.85; font-size: 1rem; }

    .metric-card {
        background: white;
        border: 1px solid #e5e9f0;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,.06);
    }
    .metric-card .value { font-size: 2rem; font-weight: 700; color: #034EA2; }
    .metric-card .label { font-size: 0.85rem; color: #6b7280; margin-top: 4px; }

    .success-box {
        background: #ecfdf5;
        border-left: 4px solid #10b981;
        padding: 16px 20px;
        border-radius: 8px;
        color: #065f46;
    }
    .offline-box {
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 14px 18px;
        border-radius: 8px;
        color: #1e40af;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CABEÇALHO
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="header-banner">
    <h1>📱 Cadastro de Atendimentos — SMB</h1>
    <p>Preencha os dados abaixo para registrar um novo atendimento Samsung</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MÉTRICAS GLOBAIS
# ═══════════════════════════════════════════════════════════════════════════════

total_atend = contar_atendimentos()
valor_total = obter_valor_total()
ticket_medio = (valor_total / total_atend) if total_atend > 0 else 0.0

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="value">{total_atend}</div>
        <div class="label">Total de Atendimentos</div>
    </div>""", unsafe_allow_html=True)
with col_m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="value">R$ {valor_total:,.2f}</div>
        <div class="label">Valor Total Acumulado</div>
    </div>""", unsafe_allow_html=True)
with col_m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="value">R$ {ticket_medio:,.2f}</div>
        <div class="label">Ticket Médio</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AVISO DE MODO (E-MAIL)
# ═══════════════════════════════════════════════════════════════════════════════

if not email_configurado():
    st.markdown("""
    <div class="offline-box">
        ⚠️ <strong>E-mail não configurado.</strong>
        Configure as variáveis <code>SMTP_USER</code> e <code>SMTP_PASSWORD</code>
        nos Secrets do Streamlit Cloud para ativar o envio automático de confirmação ao cliente.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ABAS PRINCIPAIS
# ═══════════════════════════════════════════════════════════════════════════════

tab1, tab2 = st.tabs(["📝 Novo Atendimento", "🔐 Administração"])

# ───────────────────────────────────────────────────────────────────────────────
# ABA 1 — FORMULÁRIO DE CADASTRO
# ───────────────────────────────────────────────────────────────────────────────

with tab1:
    st.subheader("Formulário de Cadastro")

    with st.form("form_atendimento", clear_on_submit=True):

        # — Seção: Identificação do Atendente
        st.markdown("### 👤 Identificação do Atendente")
        col1, col2 = st.columns(2)
        with col1:
            atendente = st.text_input(
                "Nome Completo do Atendente *",
                placeholder="Ex: Ana Paula Lima",
            )
        with col2:
            data_atendimento = st.date_input(
                "Data do Atendimento *",
                value=date.today(),
            )

        st.divider()

        # — Seção: Detalhes da Venda
        st.markdown("### 🔢 Detalhes da Venda")
        col3, col4 = st.columns(2)
        with col3:
            numero_pedido = st.text_input(
                "Número do Pedido *",
                placeholder="Ex: PED-2024-001",
            )
        with col4:
            valor_pedido = st.number_input(
                "Valor do Pedido (R$) *",
                min_value=0.0,
                step=0.01,
                format="%.2f",
            )

        st.divider()

        # — Seção: Informações do Cliente
        st.markdown("### 👥 Informações do Cliente")
        col5, col6 = st.columns(2)
        with col5:
            nome_cliente = st.text_input(
                "Nome Completo do Cliente *",
                placeholder="Ex: João Silva",
            )
        with col6:
            email_cliente = st.text_input(
                "E-mail do Cliente (opcional)",
                placeholder="cliente@email.com",
            )

        st.divider()

        # — Seção: Comprovação
        st.markdown("### 📎 Comprovação")
        arquivo = st.file_uploader(
            "Anexar comprovante *",
            type=["pdf", "png", "jpg", "webp"],
            help="Formatos aceitos: PDF, PNG, JPG, WEBP — até 200 MB",
        )

        st.caption("• Todos os campos marcados com * são obrigatórios")

        submetido = st.form_submit_button(
            "✅ Cadastrar Atendimento",
            use_container_width=True,
        )

    # ── Processamento do formulário
    if submetido:
        erros = []
        if not atendente.strip():
            erros.append("Nome Completo do Atendente")
        if not numero_pedido.strip():
            erros.append("Número do Pedido")
        if not nome_cliente.strip():
            erros.append("Nome Completo do Cliente")
        if valor_pedido <= 0:
            erros.append("Valor do Pedido (deve ser maior que zero)")
        if arquivo is None:
            erros.append("Comprovante (arquivo obrigatório)")

        if erros:
            st.error(f"⚠️ Preencha os campos obrigatórios: {', '.join(erros)}.")
        else:
            dados = {
                "atendente": atendente.strip(),
                "data_atendimento": data_atendimento.strftime("%d/%m/%Y"),
                "numero_pedido": numero_pedido.strip(),
                "nome_cliente": nome_cliente.strip(),
                "valor_pedido": float(valor_pedido),
                "email_cliente": email_cliente.strip(),
                "arquivo_comprovante": arquivo.name if arquivo else "",
                "data_hora_registro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            }

            try:
                salvar_atendimento(dados)

                # Tenta enviar e-mail de confirmação
                email_enviado = False
                if email_cliente and email_configurado():
                    try:
                        email_enviado = enviar_confirmacao(email_cliente, dados)
                    except Exception:
                        pass

                st.balloons()
                msg_extra = " Um e-mail de confirmação foi enviado ao cliente." if email_enviado else ""
                st.success(
                    f"✅ Atendimento do pedido **{numero_pedido}** cadastrado com sucesso!{msg_extra}"
                )
                st.rerun()

            except ValueError as ve:
                st.error(f"⚠️ {ve}")
            except Exception as ex:
                st.error(f"❌ Erro ao salvar: {ex}")

# ───────────────────────────────────────────────────────────────────────────────
# ABA 2 — ADMINISTRAÇÃO
# ───────────────────────────────────────────────────────────────────────────────

with tab2:
    st.subheader("🔐 Painel de Controle")
    senha_input = st.text_input("Senha de Administrador", type="password")

    if senha_input == SENHA_ADMIN:
        subtab1, subtab2 = st.tabs(["📋 Histórico Completo", "📊 Dashboard de Análise"])

        # ── Aba: Histórico
        with subtab1:
            atendimentos = carregar_atendimentos()

            if atendimentos:
                df = pd.DataFrame(atendimentos)
                df_display = df[[
                    "id", "atendente", "data_atendimento",
                    "numero_pedido", "nome_cliente",
                    "valor_pedido", "email_cliente",
                    "arquivo_comprovante", "data_hora_registro",
                ]].rename(columns={
                    "id": "ID",
                    "atendente": "Atendente",
                    "data_atendimento": "Data do Atendimento",
                    "numero_pedido": "Nº Pedido",
                    "nome_cliente": "Cliente",
                    "valor_pedido": "Valor (R$)",
                    "email_cliente": "E-mail",
                    "arquivo_comprovante": "Comprovante",
                    "data_hora_registro": "Registrado em",
                })

                st.metric("Total de Registros", len(df_display))
                st.dataframe(df_display, use_container_width=True)

                # ── Exportação Excel (corrigido)
                import io
                buffer = io.BytesIO()
                df_display.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)
                st.download_button(
                    label="📥 Baixar Histórico em Excel",
                    data=buffer,
                    file_name=f"atendimentos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                # ── Editor de Registros
                st.markdown("---")
                st.markdown("### ✏️ Editar Atendimento")
                ids_disponiveis = [r["id"] for r in atendimentos]
                id_editar = st.selectbox(
                    "Selecione o ID do atendimento para editar:",
                    ids_disponiveis,
                    format_func=lambda x: f"ID {x} — " + next(
                        (f"{r['numero_pedido']} | {r['nome_cliente']}" for r in atendimentos if r["id"] == x), ""
                    ),
                )

                registro = next((r for r in atendimentos if r["id"] == id_editar), None)
                if registro:
                    with st.form(f"form_editar_{id_editar}"):
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            ed_atendente = st.text_input("Atendente", value=registro["atendente"])
                            ed_pedido = st.text_input("Nº Pedido", value=registro["numero_pedido"])
                            ed_cliente = st.text_input("Cliente", value=registro["nome_cliente"])
                        with col_e2:
                            try:
                                dt_parse = datetime.strptime(registro["data_atendimento"], "%d/%m/%Y").date()
                            except Exception:
                                dt_parse = date.today()
                            ed_data = st.date_input("Data do Atendimento", value=dt_parse)
                            ed_valor = st.number_input(
                                "Valor do Pedido (R$)",
                                value=float(registro["valor_pedido"]),
                                min_value=0.0,
                                step=0.01,
                                format="%.2f",
                            )
                            ed_email = st.text_input("E-mail do Cliente", value=registro.get("email_cliente", ""))

                        salvar_edicao = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)

                    if salvar_edicao:
                        from database import atualizar_atendimento
                        try:
                            atualizar_atendimento(id_editar, {
                                "atendente": ed_atendente.strip(),
                                "data_atendimento": ed_data.strftime("%d/%m/%Y"),
                                "numero_pedido": ed_pedido.strip(),
                                "nome_cliente": ed_cliente.strip(),
                                "valor_pedido": float(ed_valor),
                                "email_cliente": ed_email.strip(),
                            })
                            st.success(f"✅ Atendimento ID {id_editar} atualizado com sucesso!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"❌ Erro ao salvar: {ex}")

            else:
                st.info("Nenhum atendimento cadastrado ainda.")

        # ── Aba: Dashboard
        with subtab2:
            st.markdown("### 📊 Análise de Atendimentos")

            stats_atendente = estatisticas_por_atendente()
            stats_periodo = estatisticas_por_periodo()

            if not stats_atendente:
                st.info("Sem dados suficientes para exibir os gráficos.")
            else:
                # Gráficos por Atendente
                st.markdown("#### Por Atendente")
                df_at = pd.DataFrame(stats_atendente)

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.bar_chart(
                        df_at.set_index("atendente")["total_atendimentos"],
                        use_container_width=True,
                        color="#034EA2",
                    )
                    st.caption("Quantidade de atendimentos por atendente")

                with col_g2:
                    st.bar_chart(
                        df_at.set_index("atendente")["valor_total"],
                        use_container_width=True,
                        color="#10b981",
                    )
                    st.caption("Faturamento total por atendente (R$)")

                # Gráficos por Período
                if stats_periodo:
                    st.markdown("#### Evolução Temporal")
                    df_per = pd.DataFrame(stats_periodo)
                    df_per["data_atendimento"] = pd.to_datetime(
                        df_per["data_atendimento"], dayfirst=True, errors="coerce"
                    )
                    df_per = df_per.dropna(subset=["data_atendimento"]).sort_values("data_atendimento")

                    col_g3, col_g4 = st.columns(2)
                    with col_g3:
                        st.line_chart(
                            df_per.set_index("data_atendimento")["total_atendimentos"],
                            use_container_width=True,
                            color="#034EA2",
                        )
                        st.caption("Evolução da quantidade de atendimentos")

                    with col_g4:
                        st.line_chart(
                            df_per.set_index("data_atendimento")["valor_total"],
                            use_container_width=True,
                            color="#f59e0b",
                        )
                        st.caption("Evolução do faturamento (R$)")

                # Tabela resumo por atendente
                st.markdown("#### Resumo por Atendente")
                df_resumo = df_at.rename(columns={
                    "atendente": "Atendente",
                    "total_atendimentos": "Total",
                    "valor_total": "Valor Total (R$)",
                    "valor_medio": "Ticket Médio (R$)",
                })
                df_resumo["Valor Total (R$)"] = df_resumo["Valor Total (R$)"].map(
                    lambda x: f"R$ {x:,.2f}"
                )
                df_resumo["Ticket Médio (R$)"] = df_resumo["Ticket Médio (R$)"].map(
                    lambda x: f"R$ {x:,.2f}"
                )
                st.dataframe(df_resumo, use_container_width=True, hide_index=True)

    elif senha_input:
        st.error("❌ Senha incorreta.")

# ═══════════════════════════════════════════════════════════════════════════════
# RODAPÉ
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.caption("📱 Sistema de Cadastro de Atendimentos — Samsung SMB | Versão 2.0")