import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np # Certifique-se de que o numpy está importado no topo do ficheiro


# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard SUS x IBGE", page_icon="📊", layout="wide")

# Função auxiliar para textos maiores e justificados (Estilo Apresentação)
def apresentar_texto(texto):
    st.markdown(f"""
        <div style='font-size: 1.15rem; line-height: 1.6; text-align: justify; margin-bottom: 20px;'>
            {texto}
        </div>
    """, unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv('BASE_FINAL_BI_SUS.csv', encoding='utf-8-sig')
        df = df.dropna(subset=['TOTAL_REGISTROS', 'Populacao', 'ATENDIMENTOS_POR_100K'])
        df['Populacao'] = pd.to_numeric(df['Populacao'], errors='coerce').fillna(1)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

df_final = carregar_dados()

if not df_final.empty:
    
    # --- CABEÇALHO ---
    st.title("📊 Painel Analítico: Demanda SUS vs. Indicadores IBGE")
    st.info("**Objetivo do Projeto:** Ultrapassar a análise básica de volume. O nosso desafio foi enriquecer os registos de atendimento do SUS com a malha demográfica do IBGE para descobrir o impacto do volume populacional e da educação na sobrecarga da saúde pública do Ceará.")
    st.divider()

    # --- CÁLCULO DAS MÉTRICAS ---
    total_atendimentos = df_final['TOTAL_REGISTROS'].sum()
    populacao_total = df_final['Populacao'].sum()
    taxa_media_estadual = (total_atendimentos / populacao_total) * 100000
    
    df_final['ALERTA_MAIOR_QUE_POPULACAO'] = df_final['TOTAL_REGISTROS'] > df_final['Populacao']
    qtd_alerta_maximo = df_final['ALERTA_MAIOR_QUE_POPULACAO'].sum()
    
    df_final['ACIMA_DA_MEDIA'] = df_final['ATENDIMENTOS_POR_100K'] > taxa_media_estadual
    qtd_acima_media = df_final['ACIMA_DA_MEDIA'].sum()
    percentual_sobrecarga = (qtd_acima_media / len(df_final)) * 100

    # --- SEÇÃO 1: MÉTRICAS ESSENCIAIS & VALIDAÇÃO ---
    st.subheader("1. Validação de Coerência e Panorama Geral")
    
    apresentar_texto("""
        <strong>A primeira etapa da nossa engenharia de dados consistiu na validação da integridade da base.</strong> 
        A nossa equipa procurou responder: <em>Existem municípios com mais atendimentos absolutos do que habitantes?</em> 
        Verificar esta anomalia é crucial para identificar 'Cidades Polo' que recebem um fluxo migratório de saúde de regiões vizinhas ou detetar falhas no registo de dados.
    """)
    
    if qtd_alerta_maximo == 0:
        st.success("**Validação Concluída:** A análise confirmou que nenhum município ultrapassou a sua própria população em volume de atendimentos. Como a nossa base representa uma amostra do sistema, estabelecemos a **Taxa Média Estadual** como o referencial de normalidade.")
    else:
        st.warning(f"**Atenção Analítica:** Foram identificados {qtd_alerta_maximo} municípios com volume de atendimento superior à população residente, um forte indicador de sobrecarga regional.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Atendimentos", f"{total_atendimentos:,.0f}".replace(',', '.'))
    col2.metric("População Alcançada", f"{populacao_total:,.0f}".replace(',', '.'))
    col3.metric("Taxa Média Estadual", f"{taxa_media_estadual:.0f} / 100k hab.")
    col4.metric("Índice de Sobrecarga", f"{percentual_sobrecarga:.1f}%", help="Percentual de municípios acima da média estadual.")

    st.divider()

    # --- SEÇÃO 2: O FALSO PARADIGMA ---
    st.subheader("2. A Ilusão do Volume Absoluto vs. A Realidade Proporcional")
    
    apresentar_texto("""
        <strong>Métricas absolutas enviesam a tomada de decisão.</strong> Se o planeamento público se basear apenas nos números brutos (gráfico à esquerda), os recursos serão sempre canalizados para os grandes centros urbanos. 
        Ao aplicar o nivelamento populacional e focar no nosso <strong>Índice de Sobrecarga</strong> (gráfico de rosca), revelamos a verdadeira percentagem da malha municipal que opera sob forte pressão, demandando mais recursos do SUS do que o aceitável para o seu tamanho.
    """)
    
    col_vol1, col_vol2 = st.columns(2)
    
    with col_vol1:
        df_vol_top15 = df_final.nlargest(15, 'TOTAL_REGISTROS').sort_values('TOTAL_REGISTROS', ascending=True)
        fig_bar_vol = px.bar(
            df_vol_top15, x='TOTAL_REGISTROS', y='MUNICÍPIO', orientation='h', text_auto='.0f',
            title="A Ilusão: Top 15 em Volume Absoluto", color_discrete_sequence=['#3182bd']
        )
        fig_bar_vol.update_layout(yaxis_title=None)
        st.plotly_chart(fig_bar_vol, use_container_width=True)

    with col_vol2:
        df_sobrecarga = df_final['ACIMA_DA_MEDIA'].value_counts().reset_index()
        df_sobrecarga.columns = ['Status', 'Quantidade']
        df_sobrecarga['Status'] = df_sobrecarga['Status'].map({True: 'Em Sobrecarga', False: 'Volume Estável'})
        
        fig_donut = px.pie(
            df_sobrecarga, names='Status', values='Quantidade', hole=0.4, color='Status',
            color_discrete_map={'Em Sobrecarga': '#EF553B', 'Volume Estável': '#636EFA'},
            title="A Realidade: Índice de Sobrecarga Estadual"
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()

    # --- SEÇÃO 3: RANKINGS E INSIGHTS ---
    st.subheader("3. Onde estão os verdadeiros gargalos proporcionais?")
    
    apresentar_texto("""
        <strong>A Taxa de Atendimentos por 100 mil habitantes é o grande equalizador desta análise.</strong> 
        O ranking vermelho destaca os municípios que, independentemente do seu tamanho, representam os maiores gargalos do sistema de saúde. Por outro lado, o ranking verde expõe municípios com pressão minimizada na rede de urgência, o que nos levanta uma nova hipótese analítica: estarão estas cidades a investir de forma eficaz em <strong>Educação e Saúde Preventiva</strong>, ou estaremos perante um cenário de subnotificação de dados?
    """)
    
    col_rank1, col_rank2 = st.columns(2)
    
    with col_rank1:
        df_top10 = df_final.nlargest(10, 'ATENDIMENTOS_POR_100K').sort_values('ATENDIMENTOS_POR_100K', ascending=True)
        fig_top = px.bar(
            df_top10, x="ATENDIMENTOS_POR_100K", y="MUNICÍPIO", orientation='h', text_auto='.0f',
            title="Top 10 Cidades em Alerta (Maior Proporção)", color_discrete_sequence=['indianred']
        )
        fig_top.update_layout(yaxis_title=None)
        st.plotly_chart(fig_top, use_container_width=True)

    with col_rank2:
        df_bottom10 = df_final.nsmallest(10, 'ATENDIMENTOS_POR_100K').sort_values('ATENDIMENTOS_POR_100K', ascending=False)
        fig_bottom = px.bar(
            df_bottom10, x="ATENDIMENTOS_POR_100K", y="MUNICÍPIO", orientation='h', text_auto='.0f',
            title="Top 10 Cidades Estáveis (Menor Proporção)", color_discrete_sequence=['#2CA02C']
        )
        fig_bottom.update_layout(yaxis_title=None)
        st.plotly_chart(fig_bottom, use_container_width=True)

    st.divider()

    # --- SEÇÃO 4: MAPA E CONCLUSÃO ---
    st.subheader("4. Distribuição Geográfica e Recomendações Estratégicas")
    
    col_mapa, col_texto = st.columns([2, 1])
    
    with col_texto:
        apresentar_texto("""
            Insights Finais Gerados: 
            A inteligência espacial é vital na saúde pública. O mapa permite-nos visualizar a formação de <em>clusters</em> (bolsões) de sobrecarga no interior do estado.<br><br>
            O enriquecimento dos dados comprovou que alocar infraestrutura hospitalar baseando-se apenas no volume absoluto ignora as populações mais vulneráveis.<br><br>
            Como próximo passo, sugerimos cruzar diretamente as notas do <strong>IDEB</strong> com estes polos vermelhos para modelar políticas conjuntas entre a Secretaria de Educação e a de Saúde.
        """)
        
    with col_mapa:
        if 'LATITUDE' in df_final.columns and 'LONGITUDE' in df_final.columns:
            fig_map = px.scatter_mapbox(
                df_final, lat="LATITUDE", lon="LONGITUDE", hover_name="MUNICÍPIO",
                size="ATENDIMENTOS_POR_100K", color="ACIMA_DA_MEDIA",
                color_discrete_map={True: '#EF553B', False: '#636EFA'},
                zoom=5.5, center={"lat": -5.20, "lon": -39.30},
                mapbox_style="carto-positron", title="Mapa de Calor da Pressão Hospitalar"
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("🗺️ O mapa aguarda a integração das coordenadas (Latitude/Longitude) no pipeline Pandas para renderizar.")
        st.divider()

    # --- SEÇÃO 5: PROVA ESTATÍSTICA E CIDADES MODELO ---
    st.subheader("5. Prova Estatística: O Impacto da Educação na Saúde")
    
    apresentar_texto("""
        Para além da análise visual, aplicámos testes de <strong>Correlação Estatística (Pearson)</strong> para provar matematicamente a relação entre os indicadores educacionais e a pressão no sistema de saúde.
        Adicionalmente, segmentámos os municípios para identificar as <em>'Cidades Modelo'</em>: locais que atingiram a excelência na educação e, consequentemente ou paralelamente, apresentam baixa sobrecarga hospitalar.
    """)
    
    # 1. Cálculos Estatísticos
    # Correlação
    correlacao_ideb = df_final['IDEB_medio'].corr(df_final['ATENDIMENTOS_POR_100K'])
    correlacao_esc = df_final['TAXA_ESCOLARIZACAO'].corr(df_final['ATENDIMENTOS_POR_100K'])
    
    # Impacto da Escolarização (Mediana)
    mediana_escolarizacao = df_final['TAXA_ESCOLARIZACAO'].median()
    df_final['PERFIL_ESCOLARIZACAO'] = np.where(df_final['TAXA_ESCOLARIZACAO'] >= mediana_escolarizacao, 'Alta Escolarização', 'Baixa Escolarização')
    df_impacto = df_final.groupby('PERFIL_ESCOLARIZACAO')['ATENDIMENTOS_POR_100K'].mean().reset_index()
    
    # Cidades Modelo (Top 25% IDEB + Bottom 25% Demanda)
    ideb_excelente = df_final['IDEB_medio'] >= df_final['IDEB_medio'].quantile(0.75)
    demanda_baixa = df_final['ATENDIMENTOS_POR_100K'] <= df_final['ATENDIMENTOS_POR_100K'].quantile(0.25)
    cidades_modelo = df_final[ideb_excelente & demanda_baixa].sort_values(by='IDEB_medio', ascending=False)

    # 2. Estrutura Visual no Streamlit
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.markdown("#### Teste de Pearson")
        st.metric("Correlação: IDEB x SUS", f"{correlacao_ideb:.3f}", help="Valores negativos indicam que quando o IDEB sobe, a demanda do SUS cai.")
        st.metric("Correlação: Escolas x SUS", f"{correlacao_esc:.3f}", help="Valores negativos indicam que quando a escolarização sobe, a demanda cai.")
        st.caption("*(Um valor negativo comprova a hipótese de que a melhoria na educação alivia o sistema de saúde)*")

    with col_stat2:
        st.markdown("#### Impacto da Escolarização")
        # Gráfico de barras simples para comparar Alta vs Baixa Escolarização
        fig_esc = px.bar(
            df_impacto, x='PERFIL_ESCOLARIZACAO', y='ATENDIMENTOS_POR_100K',
            color='PERFIL_ESCOLARIZACAO',
            color_discrete_map={'Alta Escolarização': '#2CA02C', 'Baixa Escolarização': '#EF553B'},
            text_auto='.0f',
            title="Média de Atendimentos SUS"
        )
        fig_esc.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Taxa por 100k hab.")
        st.plotly_chart(fig_esc, use_container_width=True)

    with col_stat3:
        st.markdown("#### Quadrante de Excelência")
        st.markdown(f"**{len(cidades_modelo)} Cidades Modelo** identificadas (Alto IDEB e Baixa Sobrecarga):")
        # Mostra a tabela limpa e formatada
        st.dataframe(
            cidades_modelo[['MUNICÍPIO', 'IDEB_medio', 'ATENDIMENTOS_POR_100K']], 
            use_container_width=True, 
            hide_index=True
        )