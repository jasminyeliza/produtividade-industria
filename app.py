import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Produtividade - Indústria", layout="wide")

st.title("📊 Central de Produtividade Industrial")

# ---------------------------------------------------------
# 1. BARRA LATERAL: SELEÇÃO DE SETOR E NAVEGAÇÃO
# ---------------------------------------------------------
st.sidebar.header("Filtros Globais")
setores_disponiveis = ["Modelagem", "Corte", "Costura", "Montagem", "Embalagem"]
setor_selecionado = st.sidebar.selectbox("Selecione o Setor", setores_disponiveis)

# ---------------------------------------------------------
# 2. SIMULAÇÃO DE BANCO DE DADOS / CONEXÃO CENTRALIZADA
# ---------------------------------------------------------
# Em produção, isso pode vir de um Google Sheets (usando gspread) ou PostgreSQL
@st.cache_data
def carregar_dados():
    # Dados fictícios para demonstração alinhados ao schema padrão
    data = {
        "Data": pd.date_range(start="2026-04-01", periods=10, freq="D"),
        "Setor": ["Modelagem"] * 10,
        "Producao_Planejada": [300, 300, 310, 290, 300, 310, 320, 300, 295, 310],
        "Producao_Real": [310, 285, 315, 290, 305, 320, 315, 310, 300, 312],
        "Refugo": [5, 10, 3, 2, 4, 6, 5, 2, 3, 4],
        "Tempo_Parada_min": [15, 30, 10, 20, 10, 5, 15, 10, 20, 12]
    }
    return pd.DataFrame(data)

df = carregar_dados()
df_setor = df[df["Setor"] == setor_selecionado]

# ---------------------------------------------------------
# 3. CÁLCULO DE INDICADORES PADRONIZADOS (ENGINEERING METRICS)
# ---------------------------------------------------------
df_setor["Eficiencia_%"] = (df_setor["Producao_Real"] / df_setor["Producao_Planejada"]) * 100
df_setor["Taxa_Qualidade_%"] = ((df_setor["Producao_Real"] - df_setor["Refugo"]) / df_setor["Producao_Real"]) * 100

# ---------------------------------------------------------
# 4. PAINEL DE VISUALIZAÇÃO (DASHBOARD INTEGRADO)
# ---------------------------------------------------------
st.subheader(f"Desempenho Atual - Setor: {setor_selecionado}")

# Métricas principais (KPI Cards)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Produção Total Real", f"{df_setor['Producao_Real'].sum():,.0f} un")
col2.metric("Eficiência Média", f"{df_setor['Eficiencia_%'].mean():.2f}%")
col3.metric("Qualidade Média", f"{df_setor['Taxa_Qualidade_%'].mean():.2f}%")
col4.metric("Total de Paradas", f"{df_setor['Tempo_Parada_min'].sum():,.0f} min")

st.markdown("---")

# Gráficos dinâmicos com Plotly
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Planejado vs. Realizado")
    fig_prod = px.bar(
        df_setor, x="Data", y=["Producao_Planejada", "Producao_Real"],
        barmode="group", labels={"value": "Quantidade", "variable": "Métrica"}
    )
    st.plotly_chart(fig_prod, width='stretch')

with col_right:
    st.markdown("### Evolução da Eficiência (%)")
    fig_ef = px.line(
        df_setor, x="Data", y="Eficiencia_%", markers=True,
        labels={"Eficiencia_%": "Eficiência (%)"}
    )
    fig_ef.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Meta (100%)")
    st.plotly_chart(fig_prod, use_container_width=True)

# ---------------------------------------------------------
# 5. FORMULÁRIO DE ENTRADA DE DADOS (CENTRALIZAÇÃO DA COLETA)
# ---------------------------------------------------------
with st.expander(f"➕ Registrar Nova Produção para {setor_selecionado}"):
    with st.form(key="form_producao"):
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
        
        submit_button = st.form_submit_button(label="Salvar Apontamento")
        
        if submit_button:
            # Aqui entraria a lógica para salvar no banco de dados ou append no Google Sheets
            st.success(f"Dados do setor {setor_selecionado} salvos com sucesso para o dia {data_registro}!")
