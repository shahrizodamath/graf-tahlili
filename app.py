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
st.markdown("""
Ushbu dastur ijtimoiy tarmoq graflarini tahlil qiladi va **4 ta asosiy markaziylik ko'rsatkichini** hisoblaydi:
1. **Degree (Daraja)** - bog'lanishlar soni.
2. **Betweenness (Oraliqlik)** - guruhlarni bog'lovchi "ko'prik".
3. **Closeness (Yaqinlik)** - ma'lumotni eng tez tarqatuvchi.
4. **Eigenvector (Ta'sir)** - boshqa muhim odamlar bilan bog'langan "elita".
""")

# --- 2. YON PANEL: Ma'lumotlar manbasini tanlash ---
st.sidebar.header("1. Ma'lumotlar manbasi")
data_source = st.sidebar.radio(
    "Qaysi ma'lumotlar bilan ishlaysiz?",
    ["O'z faylimni yuklash (CSV)", "Stanford (SNAP) bazasidan yuklash"]
)

df_edges = None

# Agar foydalanuvchi o'z faylini yuklashni tanlasa
if data_source == "O'z faylimni yuklash (CSV)":
    uploaded_file = st.sidebar.file_uploader("CSV faylni tanlang (ustunlar: source, target)", type=["csv"])
    if uploaded_file is not None:
        try:
            df_edges = pd.read_csv(uploaded_file)
            if 'source' not in df_edges.columns or 'target' not in df_edges.columns:
                st.sidebar.error("Xatolik: CSV faylda 'source' va 'target' ustunlari bo'lishi shart!")
                df_edges = None
            else:
                st.sidebar.success("Fayl muvaffaqiyatli yuklandi!")
        except Exception as e:
            st.sidebar.error(f"Xatolik: {e}")

# Agar foydalanuvchi Stanford bazasini tanlasa
elif data_source == "Stanford (SNAP) bazasidan yuklash":
    st.sidebar.info("Diqqat! Ma'lumotlar hajmi katta (200MB+). Yuklash 1-2 daqiqa vaqt olishi mumkin.")
    if st.sidebar.button("Stanford ma'lumotlarini yuklash"):
        with st.spinner("Stanford (SNAP) bazasidan ma'lumotlar yuklanmoqda... Iltimos kuting..."):
            DATA_URL = "https://snap.stanford.edu/data/twitter_combined.txt.gz"
            GZ_FILE = "twitter_combined.txt.gz"
            TXT_FILE = "twitter_combined.txt"
            
            if not os.path.exists(TXT_FILE):
                urllib.request.urlretrieve(DATA_URL, GZ_FILE)
                with gzip.open(GZ_FILE, 'rb') as f_in:
                    with open(TXT_FILE, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(GZ_FILE)
            
            # Tahlil tezligi uchun faqat 10,000 qator o'qiymiz
            df_edges = pd.read_csv(TXT_FILE, sep=" ", names=["source", "target"], nrows=10000)
            st.session_state.df_edges = df_edges
            st.sidebar.success("Ma'lumotlar yuklandi!")

# Sessiyada saqlangan ma'lumotlarni tekshirish
if 'df_edges' in st.session_state and st.session_state.df_edges is not None:
    df_edges = st.session_state.df_edges


# --- 3. Grafni qurish va tahlil qilish ---
if df_edges is not None:
    # Tahlil uchun dastlabki 1000 ta noyob tugunni ajratamiz
    unique_users = pd.concat([df_edges['source'], df_edges['target']]).unique()
    subset_users = unique_users[:1000] 
    df_subset = df_edges[df_edges['source'].isin(subset_users) & df_edges['target'].isin(subset_users)]

    G_full = nx.from_pandas_edgelist(df_subset, 'source', 'target', create_using=nx.DiGraph())

    # Sessiya holatini sozlash
    if 'graph' not in st.session_state or st.sidebar.button("Grafni qayta yuklash"):
        st.session_state.graph = G_full.copy()
        st.session_state.original_graph = G_full.copy()
        st.rerun()

    G = st.session_state.graph

    if G.number_of_nodes() == 0:
        st.warning("Graf bo'sh.")
    else:
        # --- 4. Markaziylikni hisoblash ---
        degree_cen = nx.degree_centrality(G)
        betweenness_cen = nx.betweenness_centrality(G)
        closeness_cen = nx.closeness_centrality(G)
        
        try:
            eigenvector_cen = nx.eigenvector_centrality(G, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            eigenvector_cen = {node: 0 for node in G.nodes()}

        # Jadvalni shakllantirish
        metrics_df = pd.DataFrame({
            'Tugun (ID)': list(G.nodes()),
            '1. Degree (Daraja)': [degree_cen.get(n, 0) for n in G.nodes()],
            '2. Betweenness (Oraliqlik)': [betweenness_cen.get(n, 0) for n in G.nodes()],
            '3. Closeness (Yaqinlik)': [closeness_cen.get(n, 0) for n in G.nodes()],
            '4. Eigenvector (Ta\'sir)': [eigenvector_cen.get(n, 0) for n in G.nodes()]
        }).sort_values(by='1. Degree (Daraja)', ascending=False)

        # --- 5. Simulyatsiya paneli ---
        st.sidebar.subheader("2. Simulyatsiya (Tugunni o'chirish)")
        st.sidebar.markdown("Tugunni o'chirib, uning o'rniga qaysi tugun markaziy bo'lib qolishini ko'ring.")
        nodes_list = list(G.nodes())
        nodes_list.sort()
        
        if nodes_list:
            node_to_delete = st.sidebar.selectbox("O'chirish uchun tugunni tanlang:", nodes_list)
            col1, col2 = st.sidebar.columns(2)
            if col1.button("O'chirish"):
                G.remove_node(node_to_delete)
                st.session_state.graph = G
                st.rerun()
            if col2.button("Tiklash"):
                st.session_state.graph = st.session_state.original_graph.copy()
                st.rerun()

        # --- 6. Vizualizatsiya ---
        st.subheader("Grafning interaktiv vizualizatsiyasi")
        
        # Legenda (Qaysi rang nimani anglatadi)
        st.markdown("""
        **Grafdagi belgilar:**
        *   🔴 **Tugun o'lchami (Kattaligi)** = **Degree (Daraja)** ko'rsatkichiga bog'liq (qanchalik katta bo'lsa, shunchalik ko'p obunachisi bor).
        *   🟡 **Tugun rangi (Qizilligi)** = **Betweenness (Oraliqlik)** ko'rsatkichiga bog'liq (qizilroq bo'lsa, u shunchalik muhim "ko'prik" hisoblanadi).
        """)
        
        net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", directed=True)
        net.force_atlas_2based(central_gravity=0.015, spring_length=100)
        
        max_b = max(betweenness_cen.values()) if betweenness_cen else 1
        
        for node in G.nodes():
            size = 10 + (degree_cen.get(node, 0) * 150)
            b_val = betweenness_cen.get(node, 0)
            norm_b = b_val / max_b if max_b > 0 else 0
            color = f"rgba({int(255 * norm_b)}, 100, {255 - int(255 * norm_b)}, 0.9)"
            title = f"Tugun: {node}\nDegree: {degree_cen.get(node, 0):.3f}\nBetweenness: {b_val:.3f}"
            net.add_node(node, label=str(node), size=size, color=color, title=title)
            
        for edge in G.edges():
            net.add_edge(edge[0], edge[1], color="#888888", arrows="to")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            net.save_graph(tmp.name)
            HtmlFile = open(tmp.name, 'r', encoding='utf-8')
            components.html(HtmlFile.read(), height=600)

        # --- 7. Jadval ---
        st.subheader("Markaziylik ko'rsatkichlari jadvali")
        st.markdown("Jadvaldagi ustunlar sizga kerakli 4 ta asosiy ko'rsatkichdir:")
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
else:
    # Agar hech qanday ma'lumot yuklanmagan bo'lsa, foydalanuvchiga ko'rsatma
    st.info("👈 Boshlash uchun chap tomondagi paneldan ma'lumotlar manbasini tanlang.")