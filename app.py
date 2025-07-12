import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tableau de bord - Tchadelect", layout="wide")

st.title("📊 Tableau de bord de consommation d'électricité - Tchadelect")
st.markdown("Analyse des compteurs prépayés et postpayés")

uploaded_file = st.file_uploader("📎 Importer les données CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Aperçu des données")
    st.dataframe(df.head())

    st.subheader("💡 Statistiques générales")
    st.write(df.describe())

    st.subheader("🔌 Consommation par type de compteur")
    st.bar_chart(df.groupby("type_compteur")["consommation_kwh"].sum())

    st.subheader("📈 Évolution mensuelle")
    df["date"] = pd.to_datetime(df["date"])
    df['mois'] = df['date'].dt.to_period("M").astype(str)
    st.line_chart(df.groupby("mois")["consommation_kwh"].sum())

else:
    st.warning("Veuillez importer un fichier CSV.")

