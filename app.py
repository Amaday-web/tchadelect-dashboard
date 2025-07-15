import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from sklearn.linear_model import LinearRegression
from streamlit_option_menu import option_menu

# ---------- CONFIGURATION ----------
st.set_page_config(page_title="Tchadelect Dashboard", layout="wide")

# ---------- STYLE CSS ----------
st.markdown("""
    <style>
    /* Fixer le menu horizontal en haut */
    .css-18e3th9 {
        padding-top: 5rem;
    }
    .menu-container {
        position: fixed;
        top: 0;
        width: 100%;
        z-index: 100;
        background-color: white;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# ---------- MENU HORIZONTAL ----------
with st.container():
    st.markdown('<div class="menu-container">', unsafe_allow_html=True)
    selected = option_menu(
        menu_title=None,
        options=["Vue générale", "Carte interactive", "Prédictions"],
        icons=["bar-chart", "geo-alt", "graph-up"],
        orientation="horizontal",
        default_index=0,
        key="menu",
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- UPLOAD & VALIDATION ----------
uploaded_file = st.sidebar.file_uploader("📂 Charger les données CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    required_columns = {"date", "type_compteur", "consommation_kwh", "region"}
    if not required_columns.issubset(df.columns):
        st.error("❌ Le fichier doit contenir les colonnes : date, type_compteur, consommation_kwh, region.")
        st.stop()

    df["date"] = pd.to_datetime(df["date"])
    df["mois"] = df["date"].dt.to_period("M").astype(str)

    # Filtres dynamiques
    with st.sidebar:
        region = st.multiselect("🌍 Région", options=df["region"].unique(), default=list(df["region"].unique()))
        type_compteur = st.multiselect("⚡ Type de compteur", options=df["type_compteur"].unique(), default=list(df["type_compteur"].unique()))
    df = df[df["region"].isin(region) & df["type_compteur"].isin(type_compteur)]

    # ---------- PAGE : Vue générale ----------
    if selected == "Vue générale":
        st.title("📊 Vue générale de la consommation")
        col1, col2 = st.columns(2)
        col1.metric("Consommation totale (kWh)", int(df['consommation_kwh'].sum()))
        col2.metric("Nombre d'enregistrements", len(df))

        st.subheader("🔍 Aperçu des données")
        st.dataframe(df.head(), use_container_width=True)

        st.subheader("🔌 Consommation par type de compteur")
        st.bar_chart(df.groupby("type_compteur")["consommation_kwh"].sum())

        st.subheader("📈 Évolution mensuelle")
        st.line_chart(df.groupby("mois")["consommation_kwh"].sum())

    # ---------- PAGE : Carte interactive ----------
    elif selected == "Carte interactive":
        st.title("🗺️ Carte de consommation par région")

        coords = {
            "N'Djamena": [15.05, 12.11],
            "Moundou": [16.09, 8.57],
            "Sarh": [18.37, 9.15],
            "Abéché": [20.83, 13.83],
        }

        df["lat"] = df["region"].map(lambda x: coords.get(x, [0, 0])[1])
        df["lon"] = df["region"].map(lambda x: coords.get(x, [0, 0])[0])
        df["rayon"] = np.log1p(df["consommation_kwh"]) * 10000

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(latitude=12.1, longitude=18.0, zoom=5),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df,
                    get_position='[lon, lat]',
                    get_color='[200, 30, 0, 160]',
                    get_radius='rayon'
                ),
            ]
        ))

    # ---------- PAGE : Prédictions ----------
    elif selected == "Prédictions":
        st.title("🔮 Prédiction de la consommation (6 mois)")

        df_grouped = df.groupby("mois")["consommation_kwh"].sum().reset_index()
        df_grouped["mois_date"] = pd.to_datetime(df_grouped["mois"])
        df_grouped["mois_num"] = (df_grouped["mois_date"].dt.year - df_grouped["mois_date"].dt.year.min()) * 12 + df_grouped["mois_date"].dt.month

        X = df_grouped[["mois_num"]]
        y = df_grouped["consommation_kwh"]

        model = LinearRegression().fit(X, y)

        futur = pd.DataFrame({
            "mois_num": [X["mois_num"].max() + i for i in range(1, 7)]
        })
        futur["mois_date"] = pd.date_range(start=df_grouped["mois_date"].max() + pd.offsets.MonthBegin(1), periods=6, freq="M")
        futur["mois"] = futur["mois_date"].dt.to_period("M").astype(str)
        futur["consommation_kwh"] = model.predict(futur[["mois_num"]])

        df_plot = pd.concat([
            df_grouped[["mois", "consommation_kwh"]],
            futur[["mois", "consommation_kwh"]]
        ]).set_index("mois")

        st.line_chart(df_plot)
        st.metric("🔋 Total prévisionnel (6 mois)", int(futur["consommation_kwh"].sum()))

else:
    st.warning("📁 Veuillez importer un fichier CSV avec les colonnes : date, type_compteur, consommation_kwh, region.")
    st.info("💡 Exemple de fichier disponible [ici](https://example.com/exemple.csv)")
