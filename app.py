import pandas as pd
import streamlit as st

st.set_page_config(page_title="Photoprotection Catalogue", layout="wide")
st.title("Photoprotection Catalogue")

@st.cache_data
def load_data():
    suns = pd.read_csv("sunscreens.csv")   # see schema in the message
    cloth = pd.read_csv("clothing.csv")
    return suns, cloth

suns, cloth = load_data()

tab1, tab2 = st.tabs(["Sunscreens", "Clothing"])

with tab1:
    left, right = st.columns([2,1])
    with left:
        brands = suns["brand"].astype(str) + " — " + suns["name"].astype(str)
        selected = st.multiselect("Choose up to 3 sunscreens", options=brands.unique().tolist(), max_selections=3)
        if selected:
            df = suns.loc[brands.isin(selected)].copy()
            # cost per 100 ml
            df["cost_per_100ml"] = (df["price_gbp"] / (df["size_ml"]/100)).round(2)
            show = df[[
                "brand","name","spf_measured","uva_pf",
                "block_UVA","block_UVB","block_HEV","block_VIS",
                "size_ml","price_gbp","cost_per_100ml","filters","water_resistant","porphyria_note"
            ]].rename(columns={
                "block_UVA":"% blocked UVA",
                "block_UVB":"% blocked UVB",
                "block_HEV":"% blocked HEV",
                "block_VIS":"% blocked Visible",
                "price_gbp":"£ price"
            })
            st.dataframe(show, use_container_width=True)
        else:
            st.info("Pick 1–3 items to compare.")
    with right:
        st.markdown("**Notes**")
        st.write("- Measured SPF is from your lab testing.")
        st.write("- Blocking values are % irradiance blocked.")
        st.write("- Porphyria-relevant bands: UVA/UVB/HEV/Visible.")

with tab2:
    brands = cloth["label"].astype(str)
    selected = st.multiselect("Choose up to 3 garments", options=brands.unique().tolist(), max_selections=3)
    if selected:
        df = cloth.loc[brands.isin(selected)].copy()
        show = df[[
            "label","material","gsm","upf_measured",
            "block_UVA","block_UVB","block_HEV","block_VIS",
            "price_gbp","notes"
        ]].rename(columns={
            "block_UVA":"% blocked UVA",
            "block_UVB":"% blocked UVB",
            "block_HEV":"% blocked HEV",
            "block_VIS":"% blocked Visible",
            "price_gbp":"£ price"
        })
        st.dataframe(show, use_container_width=True)
    else:
        st.info("Pick 1–3 garments to compare.")
