import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gestão de Produtividade - Indústria", layout="wide")

st.title("📊 Central de Produtividade Industrial")

# ---------------------------------------------------------
# 1. BARRA LATERAL: SELEÇÃO DE SETOR
# ---------------------------------------------------------
st.sidebar.header("Filtros Globais")
setores_disponiveis = ["Modelagem", "Corte", "Costura", "Montagem", "Embalagem"]
setor_selecionado = st.sidebar.selectbox("Selecione o Setor", setores_disponiveis)

# ---------------------------------------------------------
# 2. CONEXÃO COM O GOOGLE SHEETS (LEITURA E ESCRITA)
# ---------------------------------------------------------
@st.cache_resource
def ligar_google_sheets():
    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    cred_dict = dict(st.secrets["gcp_service_account"])
    credenciais = Credentials.from_service_account_info(cred_dict, scopes=escopos)
    cliente = gspread.authorize(credenciais)
    planilha = cliente.open("COLETA DE MODELAGEM")
    aba = planilha.worksheet("DADOS")
    return aba

# Carregar dados da planilha (com fallback para testes caso os Secrets ainda não estejam configurados)
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        aba = ligar_google_sheets()
        registos = aba.get_all_records()
        if registos:
            df = pd.DataFrame(registos)
        else:
            raise ValueError("Planilha vazia")
    except Exception:
        # Dados de demonstração caso a ligação ainda não esteja ativa
        df = pd.DataFrame({
            "Data": ["2026-04-01", "2026-04-02", "2026-04-03"],
            "Setor": ["Modelagem", "Modelagem", "Modelagem"],
            "Turno": ["Turno 1", "Turno 2", "Turno 1"],
            "Producao_Planejada": [300, 310, 290],
            "Producao_Real": [310, 285, 315],
            "Refugo": [5, 10, 3],
            "Tempo_Parada_min": [15, 30, 10]
        })
    return df

df = carregar_dados()

# Filtrar por setor selecionado
if "Setor" in df.columns:
    df_setor = df[df["Setor"] == setor_selecionado]
else:
    df_setor = df

# Converter colunas numéricas para segurança nos cálculos
for col in ["Producao_Planejada", "Producao_Real", "Refugo", "Tempo_Parada_min"]:
    if col in df_setor.columns:
        df_setor[col] = pd.to_numeric(df_setor[col], errors="coerce").fillna(0)

# Cálculo de indicadores
if "Producao_Planejada" in df_setor.columns and "Producao_Real" in df_setor.columns:
    df_setor["Eficiencia_%"] = (df_setor["Producao_Real"] / df_setor["Producao_Planejada"]) * 100
    df_setor["Taxa_Qualidade_%"] = ((df_setor["Producao_Real"] - df_setor["Refugo"]) / df_setor["Producao_Real"]) * 100
else:
    df_setor["Eficiencia_%"] = 0
    df_setor["Taxa_Qualidade_%"] = 0

# ---------------------------------------------------------
# 3. PAINEL DE VISUALIZAÇÃO (DASHBOARD)
# ---------------------------------------------------------
st.subheader(f"Desempenho Atual - Setor: {setor_selecionado}")

col1, col2, col3, col4 = st.columns(4)
total_real = df_setor['Producao_Real'].sum() if not df_setor.empty else 0
media_ef = df_setor['Eficiencia_%'].mean() if not df_setor.empty else 0
media_qual = df_setor['Taxa_Qualidade_%'].mean() if not df_setor.empty else 0
total_parada = df_setor['Tempo_Parada_min'].sum() if not df_setor.empty else 0

col1.metric("Produção Total Real", f"{total_real:,.0f} un")
col2.metric("Eficiência Média", f"{media_ef:.2f}%")
col3.metric("Qualidade Média", f"{media_qual:.2f}%")
col4.metric("Total de Paradas", f"{total_parada:,.0f} min")

st.markdown("---")

# Gráficos dinâmicos
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Planejado vs. Realizado")
    if not df_setor.empty and "Producao_Planejada" in df_setor.columns:
        fig_prod = px.bar(
            df_setor, x="Data", y=["Producao_Planejada", "Producao_Real"],
            barmode="group", labels={"value": "Quantidade", "variable": "Métrica"}
        )
        st.plotly_chart(fig_prod, use_container_width=True, key="grafico_producao")
    else:
        st.info("Sem dados para exibir no gráfico.")

with col_right:
    st.markdown("### Evolução da Eficiência (%)")
    if not df_setor.empty and "Eficiencia_%" in df_setor.columns:
        fig_ef = px.line(
            df_setor, x="Data", y="Eficiencia_%", markers=True,
            labels={"Eficiencia_%": "Eficiência (%)"}
        )
        fig_ef.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Meta (100%)")
        st.plotly_chart(fig_ef, use_container_width=True, key="grafico_eficiencia")
    else:
        st.info("Sem dados para exibir no gráfico.")

# ---------------------------------------------------------
# 4. FORMULÁRIO DE COLETA DE DADOS (GRAVAÇÃO NA NUVEM)
# ---------------------------------------------------------
st.markdown("---")
with st.expander(f"➕ Registar Nova Produção para {setor_selecionado}", expanded=False):
    with st.form(key="form_producao", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            data_registro = st.date_input("Data do Apontamento")
            turno = st.selectbox("Turno", ["Turno 1", "Turno 2", "Turno 3"])
        with col_f2:
            prod_plan = st.number_input("Produção Planejada", min_value=0, value=300)
            prod_real = st.number_input("Produção Real", min_value=0, value=300)
        with col_f3:
            refugo = st.number_input("Peças com Defeito (Refugo)", min_value=0, value=0)
            parada = st.number_input("Tempo de Parada (min)", min_value=0, value=0)
        
        submit_button = st.form_submit_button(label="Guardar na Planilha Central")
        
        if submit_button:
            try:
                aba_dados = ligar_google_sheets()
                nova_linha = [
                    str(data_registro),
                    setor_selecionado,
                    turno,
                    int(prod_plan),
                    int(prod_real),
                    int(refugo),
                    int(parada)
                ]
                aba_dados.append_row(nova_linha)
                st.success(f"Registo do setor **{setor_selecionado}** guardado com sucesso na nuvem! Atualize a página para atualizar os gráficos.")
            except Exception as e:
                st.error(f"Erro ao guardar na planilha. Certifique-se de que configurou os Secrets no Streamlit Cloud. Detalhe: {e}")
