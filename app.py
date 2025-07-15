import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from sklearn.linear_model import LinearRegression
from streamlit_option_menu import option_menu

# ---------- CONFIGURATION ----------
st.set_page_config(page_title="Tchadelect Dashboard", layout="wide")

# ---------- VALIDATION DES COLONNES ----------
def validate_columns(df):
    required_columns = {"date", "type_compteur", "consommation_kwh", "region"}
    if not required_columns.issubset(df.columns):
        st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_columns)}")
        return False
    return True

# ---------- PRÉTRAITEMENT ----------
def preprocess(df):
    df["date"] = pd.to_datetime(df["date"])
    df["mois"] = df["date"].dt.to_period("M").astype(str)
    return df

# ---------- VUE GÉNÉRALE ----------
def vue_generale(df):
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

# ---------- CARTE INTERACTIVE ----------
def carte_interactive(df):
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

# ---------- PRÉDICTIONS ----------
def predictions(df):
    st.title("🔮 Prédiction de la consommation")
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
    st.metric("Consommation prévisionnelle totale (6 mois)", int(futur["consommation_kwh"].sum()))

# ---------- MAIN ----------
def main():
    # --- MENU HORIZONTAL ---
    selected = option_menu(
        menu_title=None,
        options=["Vue générale", "Carte interactive", "Prédictions"],
        icons=["bar-chart", "geo-alt", "graph-up"],
        orientation="horizontal"
    )

    # --- FICHIER CSV ---
    uploaded_file = st.file_uploader("📂 Charger un fichier CSV", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        if validate_columns(df):
            df = preprocess(df)

            if selected == "Vue générale":
                vue_generale(df)
            elif selected == "Carte interactive":
                carte_interactive(df)
            elif selected == "Prédictions":
                predictions(df)
    else:
        st.warning("📁 Veuillez importer un fichier CSV contenant les colonnes : date, type_compteur, consommation_kwh, region.")
        st.info("💡 Exemple de fichier disponible [ici](https://example.com/exemple.csv)")

# ---------- LANCEMENT ----------
if __name__ == "__main__":
    main()
