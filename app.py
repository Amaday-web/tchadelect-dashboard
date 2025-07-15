import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from sklearn.linear_model import LinearRegression
from streamlit_option_menu import option_menu

class TchadelectApp:
    def __init__(self):
        st.set_page_config(page_title="Tchadelect Dashboard", layout="wide")
        self.df = None
        self.pages = {
            "📊 Vue générale": self.vue_generale,
            "🗺️ Carte interactive": self.carte_interactive,
            "🔮 Prédictions": self.predictions
        }

    def load_data(self, file):
        df = pd.read_csv(file)
        cols = {"date", "type_compteur", "consommation_kwh", "region"}
        if not cols.issubset(df.columns):
            st.error(f"Le CSV doit contenir : {', '.join(cols)}")
            return None
        df["date"] = pd.to_datetime(df["date"])
        df["mois"] = df["date"].dt.to_period("M").astype(str)
        return df

    def header_menu(self):
        st.markdown("## 🔌 Tchadelect - Société nationale d'électricité")
        choice = option_menu(
            menu_title=None,
            options=list(self.pages.keys()),
            icons=["graph-up", "geo-alt", "forecast"],  # choix d’icônes
            orientation="horizontal"
        )
        return choice

    def vue_generale(self):
        st.subheader("📊 Vue générale")
        col1, col2 = st.columns(2)
        col1.metric("Consommation totale (kWh)", int(self.df['consommation_kwh'].sum()))
        col2.metric("Nombre d'enregistrements", len(self.df))
        st.dataframe(self.df.head())
        st.bar_chart(self.df.groupby("type_compteur")["consommation_kwh"].sum())
        st.line_chart(self.df.groupby("mois")["consommation_kwh"].sum())

    def carte_interactive(self):
        st.subheader("🗺️ Carte interactive")
        coords = {
            "N'Djamena": [15.05, 12.11],
            "Moundou": [16.09, 8.57],
            "Sarh": [18.37, 9.15],
            "Abéché": [20.83, 13.83],
        }
        self.df["lat"] = self.df["region"].map(lambda x: coords.get(x, [0,0])[1])
        self.df["lon"] = self.df["region"].map(lambda x: coords.get(x, [0,0])[0])
        self.df["rayon"] = np.log1p(self.df["consommation_kwh"]) * 10000
        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(latitude=12.1, longitude=18.0, zoom=5),
            layers=[pdk.Layer(
                "ScatterplotLayer",
                data=self.df,
                get_position="[lon, lat]",
                get_color="[200, 30, 0, 160]",
                get_radius="rayon"
            )]
        ))

    def predictions(self):
        st.subheader("🔮 Prédictions")
        dfg = self.df.groupby("mois")["consommation_kwh"].sum().reset_index()
        dfg["mois_d"] = pd.to_datetime(dfg["mois"])
        dfg["num"] = (dfg["mois_d"].dt.year - dfg["mois_d"].dt.year.min())*12 + dfg["mois_d"].dt.month
        X = dfg[["num"]]; y = dfg["consommation_kwh"]
        model = LinearRegression().fit(X, y)
        futur = pd.DataFrame({"num":[X["num"].max()+i for i in range(1,7)]})
        futur["mois_d"] = pd.date_range(start=dfg["mois_d"].max()+pd.offsets.MonthBegin(1), periods=6, freq="M")
        futur["mois"] = futur["mois_d"].dt.to_period("M").astype(str)
        futur["consommation_kwh"] = model.predict(futur[["num"]])
        dfp = pd.concat([dfg[["mois","consommation_kwh"]], futur[["mois","consommation_kwh"]]]).set_index("mois")
        st.line_chart(dfp)
        st.metric("Prévision 6 mois", f"{int(futur['consommation_kwh'].sum()):,} kWh")

    def run(self):
        uploaded = st.file_uploader("📂 Charger un CSV", type="csv")
        if uploaded:
            self.df = self.load_data(uploaded)
            if self.df is not None:
                page = self.header_menu()
                self.pages[page]()
        else:
            st.warning("📁 Veuillez charger un fichier CSV.")
            st.info("💡 Exemple dispo [ici](https://example.com/exemple.csv)")

if __name__ == "__main__":
    TchadelectApp().run()
