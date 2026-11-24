# Graflarda markaziylik ko'rsatkichlari va ijtimoiy tarmoqlar tahlili

Ushbu loyiha **"Graflarda markaziylik ko'rsatkichlari va ularning ijtimoiy tarmoqlarni tahlil qilishdagi tatbiqlari"** mavzusidagi diplom ishi doirasida yaratilgan interaktiv veb-ilova hisoblanadi.

## 🚀 Imkoniyatlar
*   Stanford universitetining (SNAP) ochiq ma'lumotlar bazasidan avtomatik ma'lumot yuklash.
*   Yo'naltirilgan grafni (kim kimga obuna bo'lgan) qurish.
*   4 ta asosiy markaziylik ko'rsatkichini hisoblash:
    *   **Degree Centrality** (Daraja markaziyligi)
    *   **Betweenness Centrality** (Oraliqlik markaziyligi)
    *   **Closeness Centrality** (Yaqinlik markaziyligi)
    *   **Eigenvector Centrality** (Xos vektor markaziyligi)
*   Interaktiv vizualizatsiya (tugunlarning o'lchami va rangi ko'rsatkichlarga qarab o'zgaradi).
*   **Simulyatsiya:** Tugunlarni real vaqt rejimida o'chirish orqali tarmoq barqarorligini tahlil qilish.

## 🛠 Texnologiyalar
*   Python 3.9+
*   Streamlit, NetworkX, PyVis, Pandas

## 📦 O'rnatish va ishga tushirish (WSL / Linux)
1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `streamlit run app.py`

## 📊 Ma'lumotlar manbasi
Ma'lumotlar [SNAP (Stanford Network Analysis Project)](https://snap.stanford.edu/data/twitter_combined.html) dan olingan.
