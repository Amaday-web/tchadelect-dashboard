import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from sklearn.linear_model import LinearRegression
from streamlit_option_menu import option_menu

# Configuration de la page
st.set_page_config(page_title="Tchadelect Dashboard", layout="wide")

# ---------- CSS pour menu fixe ----------
st.markdown("""
    <style>
        .css-1r6slb0.e1tzin5v3 {position: sticky; top: 0; z-index: 999; background-color: white;}
    </style>
""", unsafe_allow_html=True)

# ---------- MENU HORIZONTAL ----------
selected = option_menu(
    menu_title=None,
    options=["Vue générale", "Carte interactive", "Prédictions"],
    icons=["bar-chart", "geo-alt", "graph-up"],
    orientation="horizontal",
)

# ---------- UPLOAD ----------
uploaded_file = st.file_uploader("📂 Charger les données CSV", type="csv")

# ---------- VALIDATION ----------
def validate_columns(df):
    required = {"date", "type_compteur", "consommation_kwh", "region"}
    return required.issubset(df.columns)

# ---------- PRÉTRAITEMENT ----------
def preprocess(df):
    df["date"] = pd.to_datetime(df["date"])
    df["mois"] = df["date"].dt.to_period("M").astype(str)
    return df

# ---------- FILTRES ----------
def filtrer_donnees(df):
    regions = st.sidebar.multiselect("Filtrer par région", options=sorted(df["region"].unique()))
    types = st.sidebar.multiselect("Filtrer par type de compteur", options=sorted(df["type_compteur"].unique()))
    
    if regions:
        df = df[df["region"].isin(regions)]
    if types:
        df = df[df["type_compteur"].isin(types)]
    return df

# ---------- VUE GÉNÉRALE ----------
def vue_generale(df):
    st.header("📊 Vue générale de la consommation")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total consommation (kWh)", int(df['consommation_kwh'].sum()))
    col2.metric("Nb d'enregistrements", len(df))
    col3.metric("Consommation moyenne", round(df['consommation_kwh'].mean(), 2))

    st.subheader("🔍 Aperçu des données")
    st.dataframe(df.head())

    st.subheader("🔌 Consommation par type de compteur")
    st.bar_chart(df.groupby("type_compteur")["consommation_kwh"].sum())

    st.subheader("📈 Évolution mensuelle")
    st.line_chart(df.groupby("mois")["consommation_kwh"].sum())

# ---------- CARTE INTERACTIVE ----------
def carte_interactive(df):
    st.header("🗺️ Carte de consommation par région")
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
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                get_color='[200, 30, 0, 160]',
                get_radius="rayon",
            )
        ]
    ))

# ---------- PRÉDICTIONS ----------
def predictions(df):
    st.header("🔮 Prédiction de la consommation")

    df_grp = df.groupby("mois")["consommation_kwh"].sum().reset_index()
    df_grp["mois_date"] = pd.to_datetime(df_grp["mois"])
    df_grp["mois_num"] = (df_grp["mois_date"].dt.year - df_grp["mois_date"].dt.year.min()) * 12 + df_grp["mois_date"].dt.month

    X = df_grp[["mois_num"]]
    y = df_grp["consommation_kwh"]
    model = LinearRegression().fit(X, y)

    futur = pd.DataFrame({"mois_num": [X["mois_num"].max() + i for i in range(1, 7)]})
    futur["mois_date"] = pd.date_range(start=df_grp["mois_date"].max() + pd.offsets.MonthBegin(1), periods=6, freq="M")
    futur["mois"] = futur["mois_date"].dt.to_period("M").astype(str)
    futur["consommation_kwh"] = model.predict(futur[["mois_num"]])

    df_plot = pd.concat([df_grp[["mois", "consommation_kwh"]], futur[["mois", "consommation_kwh"]]]).set_index("mois")

    st.line_chart(df_plot)
    st.metric("🔮 Consommation prévisionnelle (6 mois)", int(futur["consommation_kwh"].sum()))

# ---------- MAIN ----------
def main():
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if validate_columns(df):
            df = preprocess(df)
            df = filtrer_donnees(df)

            if selected == "Vue générale":
                vue_generale(df)
            elif selected == "Carte interactive":
                carte_interactive(df)
            elif selected == "Prédictions":
                predictions(df)
        else:
            st.error("❌ Fichier invalide. Colonnes requises : date, type_compteur, consommation_kwh, region.")
    else:
        st.info("📁 Veuillez importer un fichier CSV pour commencer.")

# ---------- LANCEMENT ----------
if __name__ == "__main__":
    main()
