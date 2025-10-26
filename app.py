import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Photoprotection Catalogue", layout="wide")
st.title("Photoprotection Catalogue")

DATA_XLSX = Path(__file__).parent / "photoprotection_catalogue_template.xlsx"
SHEET_SUN = "Sunscreens"
SHEET_CLO = "Clothing"

@st.cache_data
def load_sheet(path: Path, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    df = df.loc[:, df.columns.tolist()]
    df.columns = [str(c) for c in df.columns]
    return df

def make_label(row: pd.Series, kind: str) -> str:
    brand = row.get("Product Brand", "")
    name = row.get("Product Name", "")
    extra = ""
    if kind == "sun":
        vol = row.get("Volume (ml)", "")
        if str(vol).strip() not in {"", "nan"}:
            extra = f" — {vol} ml"
    elif kind == "cloth":
        mat = row.get("Material", "")
        if str(mat).strip() not in {"", "nan"}:
            extra = f" — {mat}"
    return f"{brand} — {name}{extra}".strip(" —")

# Load sheets
try:
    suns = load_sheet(DATA_XLSX, SHEET_SUN)
except Exception as e:
    suns = pd.DataFrame()
    st.warning(f"Could not load {SHEET_SUN}: {e}")

try:
    cloth = load_sheet(DATA_XLSX, SHEET_CLO)
except Exception as e:
    cloth = pd.DataFrame()
    st.warning(f"Could not load {SHEET_CLO}: {e}")

tab1, tab2 = st.tabs(["Sunscreens", "Clothing"])

with tab1:
    st.caption(f"{SHEET_SUN} • {len(suns)} rows • {len(suns.columns)} columns")
    if suns.empty:
        st.info("Add data to the Sunscreens sheet.")
    else:
        labels = suns.apply(lambda r: make_label(r, "sun"), axis=1)
        left, right = st.columns([2, 1])
        with left:
            chosen = st.multiselect("Choose up to 3 products", options=labels.tolist(), max_selections=3)
        with right:
            show_all = st.toggle("Show all products", value=(len(chosen) == 0))
        view = suns if show_all else suns.loc[labels.isin(chosen), suns.columns.tolist()]
        st.dataframe(view, use_container_width=True, hide_index=True)

with tab2:
    st.caption(f"{SHEET_CLO} • {len(cloth)} rows • {len(cloth.columns)} columns")
    if cloth.empty:
        st.info("Add data to the Clothing sheet.")
    else:
        labels = cloth.apply(lambda r: make_label(r, "cloth"), axis=1)
        left, right = st.columns([2, 1])
        with left:
            chosen = st.multiselect("Choose up to 3 garments", options=labels.tolist(), max_selections=3, key="cloth_sel")
        with right:
            show_all = st.toggle("Show all garments", value=(len(chosen) == 0), key="cloth_all")
        view = cloth if show_all else cloth.loc[labels.isin(chosen), cloth.columns.tolist()]
        st.dataframe(view, use_container_width=True, hide_index=True)
