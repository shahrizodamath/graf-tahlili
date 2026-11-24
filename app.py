import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os
import urllib.request
import gzip
import shutil
import tempfile

# --- 1. Sahifa sozlamalari ---
st.set_page_config(page_title="Graf Markaziyligi Analizatori", layout="wide")
st.title("Graflarda markaziylik ko'rsatkichlari tahlili")

# --- 2. SNAP bazasidagi mavjud graflar ro'yxati ---
SNAP_DATASETS = {
    "Kichik: Congress Twitter (475 ta tugun)": "https://snap.stanford.edu/data/congress-twitter.txt.gz",
    "O'rtacha: Email EU Core (1005 ta tugun)": "https://snap.stanford.edu/data/email-Eu-core.txt.gz",
    "Katta: Twitter Ego (81,000 ta tugun)": "https://snap.stanford.edu/data/twitter_combined.txt.gz"
}

# --- 3. YON PANEL: Ma'lumotlar manbasini tanlash ---
st.sidebar.header("1. Ma'lumotlar manbasi")
data_source = st.sidebar.radio(
    "Qaysi usulda yuklaymiz?",
    ["Avtomatik (SNAP serveridan)", "Fayl yuklash (CSV yoki TXT)"]
)

df_edges = None

# Xotirani tozalash
if st.sidebar.button("Xotirani tozalash / Yangidan boshlash"):
    for key in ['df_edges', 'graph', 'original_graph']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

if data_source == "Avtomatik (SNAP serveridan)":
    selected_dataset = st.sidebar.selectbox("Grafni tanlang:", list(SNAP_DATASETS.keys()))
    if st.sidebar.button("Grafni yuklash"):
        url = SNAP_DATASETS[selected_dataset]
        filename_gz = "temp_data.txt.gz"
        filename_txt = "temp_data.txt"
        
        with st.spinner("Ma'lumotlar yuklanmoqda... Iltimos kuting..."):
            try:
                urllib.request.urlretrieve(url, filename_gz)
                with gzip.open(filename_gz, 'rb') as f_in:
                    with open(filename_txt, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(filename_gz)
                
                df_edges = pd.read_csv(filename_txt, sep=r'\s+', names=["source", "target"], comment='#', header=None)
                st.session_state.df_edges = df_edges
                st.sidebar.success(f"Yuklandi! Qirralar soni: {len(df_edges)}")
            except Exception as e:
                st.sidebar.error(f"Yuklashda xatolik: {e}")

elif data_source == "Fayl yuklash (CSV yoki TXT)":
    uploaded_file = st.sidebar.file_uploader("Faylni tanlang (ustunlar: source, target)", type=["csv", "txt"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_edges = pd.read_csv(uploaded_file)
            else:
                df_edges = pd.read_csv(uploaded_file, sep=r'\s+', names=["source", "target"], comment='#', header=None)
            
            if 'source' not in df_edges.columns or 'target' not in df_edges.columns:
                if len(df_edges.columns) >= 2:
                    df_edges.columns = ['source', 'target'] + list(df_edges.columns[2:])
                else:
                    st.sidebar.error("Xatolik: Faylda kamida 2 ta ustun bo'lishi kerak!")
                    df_edges = None
            else:
                st.session_state.df_edges = df_edges
                st.sidebar.success("Fayl muvaffaqiyatli yuklandi!")
        except Exception as e:
            st.sidebar.error(f"Xatolik: {e}")

if 'df_edges' in st.session_state:
    df_edges = st.session_state.df_edges

# --- 4. Grafni qurish va tahlil qilish ---
if df_edges is not None and len(df_edges) > 0:
    
    unique_nodes = pd.concat([df_edges['source'], df_edges['target']]).unique()
    if len(unique_nodes) > 5000:
        st.warning(f"⚠️ Diqqat! Sizning grafingizda {len(unique_nodes)} ta tugun bor. Streamlit bepul serverida hisoblash sekinlashishi mumkin.")
    
    G_full = nx.from_pandas_edgelist(df_edges, 'source', 'target', create_using=nx.DiGraph())

    if 'graph' not in st.session_state or st.sidebar.button("Grafni qayta yuklash"):
        st.session_state.graph = G_full.copy()
        st.session_state.original_graph = G_full.copy()
        st.rerun()

    G = st.session_state.graph

    if G.number_of_nodes() == 0:
        st.warning("Graf bo'sh.")
    else:
        with st.spinner("Markaziylik ko'rsatkichlari hisoblanmoqda..."):
            degree_cen = nx.degree_centrality(G)
            betweenness_cen = nx.betweenness_centrality(G)
            closeness_cen = nx.closeness_centrality(G)
            
            try:
                eigenvector_cen = nx.eigenvector_centrality(G, max_iter=1000)
            except nx.PowerIterationFailedConvergence:
                eigenvector_cen = {node: 0 for node in G.nodes()}

        # --- 6. ENG MUHIM 4 TA TUGUNNI ANIQLASH ---
        top_degree_node = max(degree_cen, key=degree_cen.get)
        top_betw_node = max(betweenness_cen, key=betweenness_cen.get)
        top_close_node = max(closeness_cen, key=closeness_cen.get)
        top_eigen_node = max(eigenvector_cen, key=eigenvector_cen.get)

        st.markdown("### 🏆 Eng muhim 4 ta tugun (Markazlar)")
        col1, col2, col3, col4 = st.columns(4)
        col1.info(f"**Degree:** Tugun `{top_degree_node}`\n\nQiymat: {degree_cen[top_degree_node]:.3f}")
        col2.success(f"**Betweenness:** Tugun `{top_betw_node}`\n\nQiymat: {betweenness_cen[top_betw_node]:.3f}")
        col3.warning(f"**Closeness:** Tugun `{top_close_node}`\n\nQiymat: {closeness_cen[top_close_node]:.3f}")
        col4.error(f"**Eigenvector:** Tugun `{top_eigen_node}`\n\nQiymat: {eigenvector_cen[top_eigen_node]:.3f}")

        metrics_df = pd.DataFrame({
            'Tugun (ID)': list(G.nodes()),
            '1. Degree (Daraja)': [degree_cen.get(n, 0) for n in G.nodes()],
            '2. Betweenness (Oraliqlik)': [betweenness_cen.get(n, 0) for n in G.nodes()],
            '3. Closeness (Yaqinlik)': [closeness_cen.get(n, 0) for n in G.nodes()],
            '4. Eigenvector (Ta\'sir)': [eigenvector_cen.get(n, 0) for n in G.nodes()]
        }).sort_values(by='1. Degree (Daraja)', ascending=False)

        # --- 7. Simulyatsiya (Bir nechta tugunni o'chirish) ---
        st.sidebar.subheader("2. Simulyatsiya (O'chirish)")
        nodes_list = list(G.nodes())
        nodes_list.sort()
        
        if nodes_list:
            nodes_to_delete = st.sidebar.multiselect("O'chirish uchun tugunlarni tanlang:", nodes_list)
            
            col1, col2 = st.sidebar.columns(2)
            if col1.button("O'chirish"):
                if nodes_to_delete:
                    G.remove_nodes_from(nodes_to_delete)
                    st.session_state.graph = G
                    st.rerun()
            if col2.button("Barchasini tiklash"):
                st.session_state.graph = st.session_state.original_graph.copy()
                st.rerun()

        # --- 8. Vizualizatsiya ---
        st.subheader("Grafning interaktiv vizualizatsiyasi")
        
        st.markdown("""
        **Grafdagi ranglar va belgilar:**
        *   🟡 **Oltin (Sariq)** = Eng katta **Degree** ga ega tugun.
        *   🔵 **Ko'k** = Eng katta **Betweenness** ga ega tugun.
        *   🟢 **Yashil** = Eng katta **Closeness** ga ega tugun.
        *   🔴 **Qizil** = Eng katta **Eigenvector** ga ega tugun.
        """)
        
        net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", directed=True)
        net.force_atlas_2based(central_gravity=0.015, spring_length=100)
        
        max_b = max(betweenness_cen.values()) if betweenness_cen else 1
        
        for node in G.nodes():
            size = 10 + (degree_cen.get(node, 0) * 150)
            b_val = betweenness_cen.get(node, 0)
            norm_b = b_val / max_b if max_b > 0 else 0
            
            if node == top_degree_node:
                color = "gold"
                size += 10
            elif node == top_betw_node:
                color = "cyan"
                size += 10
            elif node == top_close_node:
                color = "lime"
                size += 10
            elif node == top_eigen_node:
                color = "magenta"
                size += 10
            else:
                color = f"rgba({int(255 * norm_b)}, 100, {255 - int(255 * norm_b)}, 0.9)"
                
            title = f"Tugun: {node}\nDegree: {degree_cen.get(node, 0):.3f}\nBetweenness: {b_val:.3f}"
            net.add_node(node, label=str(node), size=size, color=color, title=title)
            
        for edge in G.edges():
            net.add_edge(edge[0], edge[1], color="#888888", arrows="to")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            net.save_graph(tmp.name)
            HtmlFile = open(tmp.name, 'r', encoding='utf-8')
            components.html(HtmlFile.read(), height=600)

        # --- 9. Jadval ---
        st.subheader("Barcha tugunlarning markaziylik ko'rsatkichlari jadvali")
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
else:
    st.info("👈 Boshlash uchun chap tomondagi paneldan ma'lumotlarni yuklang.")
