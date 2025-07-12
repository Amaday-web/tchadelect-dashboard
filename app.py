import streamlit as st
import pandas as pd
import pydeck as pdk
from sklearn.linear_model import LinearRegression
import numpy as np

# Configuration de la page
st.set_page_config(page_title="Tchadelect Dashboard", layout="wide")

# Barre latérale
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Flag_of_Chad.svg/2560px-Flag_of_Chad.svg.png", width=100)
st.sidebar.title("🔌 Tchadelect")
st.sidebar.markdown("""
**Société nationale d'électricité**

Analyse des données :
- Tableau de bord
- Carte interactive
- Prédictions
""")

# Choix de page
page = st.sidebar.radio("Navigation", ["Vue générale", "Carte interactive", "Prédictions"])

# Upload du fichier CSV
uploaded_file = st.sidebar.file_uploader("📂 Charger les données CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df["mois"] = df["date"].dt.to_period("M").astype(str)

    if page == "Vue générale":
        st.title("📊 Vue générale de la consommation")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Consommation totale (kWh)", int(df['consommation_kwh'].sum()))
        with col2:
            st.metric("Nombre d'enregistrements", len(df))

        st.subheader("🔍 Aperçu des données")
        st.dataframe(df.head())

        st.subheader("🔌 Par type de compteur")
        st.bar_chart(df.groupby("type_compteur")["consommation_kwh"].sum())

        st.subheader("📈 Évolution mensuelle")
        st.line_chart(df.groupby("mois")["consommation_kwh"].sum())

    elif page == "Carte interactive":
        st.title("🗺️ Carte de consommation par région")

        coords = {
            "N'Djamena": [15.05, 12.11],
            "Moundou": [16.09, 8.57],
            "Sarh": [18.37, 9.15],
            "Abéché": [20.83, 13.83],
        }

        df["lat"] = df["region"].map(lambda x: coords.get(x, [0, 0])[1])
        df["lon"] = df["region"].map(lambda x: coords.get(x, [0, 0])[0])

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(latitude=12.1, longitude=18.0, zoom=5),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df,
                    get_position='[lon, lat]',
                    get_color='[200, 30, 0, 160]',
                    get_radius='consommation_kwh * 1000'
                ),
            ]
        ))

    elif page == "Prédictions":
        st.title("🔮 Prédiction de la consommation (modèle simple)")

        if "mois" in df.columns:
            df_grouped = df.groupby("mois")["consommation_kwh"].sum().reset_index()
            df_grouped["mois_num"] = pd.to_datetime(df_grouped["mois"]).dt.month + 12 * pd.to_datetime(df_grouped["mois"]).dt.year

            X = df_grouped[["mois_num"]]
            y = df_grouped["consommation_kwh"]

            model = LinearRegression().fit(X, y)
            futur = pd.DataFrame({"mois_num": [X["mois_num"].max() + i for i in range(1, 7)]})
            pred = model.predict(futur)

            futur["mois"] = pd.date_range(start=df_grouped["mois"].max(), periods=6, freq="M").strftime("%Y-%m")
            futur["consommation_kwh"] = pred

            st.line_chart(pd.concat([
                df_grouped[["mois", "consommation_kwh"]],
                futur[["mois", "consommation_kwh"]].rename(columns={"mois": "mois", "consommation_kwh": "consommation_kwh"})
            ]).set_index("mois"))

        else:
            st.warning("Aucune colonne 'mois' trouvée pour prédire")

else:
    st.warning("📁 Veuillez importer un fichier CSV avec les colonnes : date, type_compteur, consommation_kwh, region.")
