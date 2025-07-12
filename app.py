import streamlit as st
import pandas as pd
import pydeck as pdk

# Configuration de la page
st.set_page_config(page_title="Tableau de bord - Tchadelect", layout="wide")

# Titre
st.title("📊 Tableau de bord de consommation d'électricité - Tchadelect")
st.markdown("Analyse des compteurs prépayés et postpayés, avec carte des régions")

# Upload du fichier CSV
uploaded_file = st.file_uploader("📎 Importer le fichier CSV", type="csv")

if uploaded_file is not None:
    # Chargement des données
    df = pd.read_csv(uploaded_file)

    # Aperçu
    st.subheader("🔍 Aperçu des données")
    st.dataframe(df.head())

    # Statistiques générales
    st.subheader("💡 Statistiques générales")
    st.write(df.describe())

    # Consommation par type de compteur
    st.subheader("🔌 Consommation par type de compteur")
    st.bar_chart(df.groupby("type_compteur")["consommation_kwh"].sum())

    # Évolution mensuelle
    st.subheader("📈 Évolution mensuelle")
    df["date"] = pd.to_datetime(df["date"])
    df["mois"] = df["date"].dt.to_period("M").astype(str)
    st.line_chart(df.groupby("mois")["consommation_kwh"].sum())

    # Carte interactive par région
    st.subheader("🗺️ Carte de consommation par région")

    # Coordonnées approximatives des grandes villes du Tchad
    coords = {
        "N'Djamena": [15.05, 12.11],
        "Moundou": [16.09, 8.57],
        "Sarh": [18.37, 9.15],
        "Abéché": [20.83, 13.83],
    }

    # Ajout des coordonnées lat/lon
    df["lat"] = df["region"].map(lambda x: coords.get(x, [0, 0])[1])
    df["lon"] = df["region"].map(lambda x: coords.get(x, [0, 0])[0])

    # Affichage de la carte avec PyDeck
    st.write("📍 Données géographiques utilisées pour la carte :")
st.dataframe(df[["region", "lat", "lon", "consommation_kwh"]])

    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(
            latitude=12.1,
            longitude=18.0,
            zoom=5,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=df,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius='consommation_kwh * 1000',
            ),
        ],
    ))

else:
    st.warning("📂 Veuillez importer un fichier CSV contenant les colonnes : date, type_compteur, consommation_kwh, region.")
