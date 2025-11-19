import pandas as pd
import streamlit as st
from pathlib import Path
import plotly.express as px

# ----------------- BASIC SETUP -----------------

st.set_page_config(page_title="Photoprotection Catalogue", layout="wide")
st.title("Photoprotection Catalogue")

DATA_XLSX = Path(__file__).parent / "photoprotection_catalogue_template.xlsx"
SHEET_SUN = "Sunscreens"
SHEET_CLO = "Clothing"

# Columns shown to patients in the tables (NOW includes Image)
SUN_DISPLAY_COLS = [
    "Product Brand",
    "Product Name",
    "Price (£)",
    "Volume (ml)",
    "Price / ml",
    "SPF (lab)",
    "UVA Protection (Lab)",
    "Blue Light Protection (lab)",
    "Visible Protection (lab)",
    "Image",
]

CLO_DISPLAY_COLS = [
    "Product Brand",
    "Product Name",
    "Price (£)",
    "SPF (lab)",
    "UVA Protection (Lab)",
    "Blue Light Protection (lab)",
    "Visible Protection (lab)",
    "Image",
]


# ----------------- DATA LOADING -----------------

@st.cache_data
def load_sheet(path: Path, sheet: str) -> pd.DataFrame:
    """Load a sheet as text, keep headers & order exactly as in Excel."""
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl", dtype=str)
    df = df.fillna("")
    df.columns = [str(c) for c in df.columns]
    return df


def make_label(row: pd.Series, kind: str) -> str:
    """
    Human-readable labels for dropdowns.

    Sunscreens: Brand — Name — 50 ml
    Clothing:   Brand — Name — Material
    """
    brand = str(row.get("Product Brand", "")).strip()
    name = str(row.get("Product Name", "")).strip()
    extra = ""

    if kind == "sun":
        vol = str(row.get("Volume (ml)", "")).strip()
        if vol and vol.lower() != "nan":
            extra = f" — {vol} ml"
    elif kind == "cloth":
        mat = str(row.get("Material", "")).strip()
        if mat and mat.lower() != "nan":
            extra = f" — {mat}"

    label = " — ".join(x for x in [brand, name] if x)
    if not label:
        # Fallback: first non-empty cell from the row
        for v in row.values:
            if str(v).strip():
                label = str(v)
                break

    return (label + extra).strip(" —")


# ----------------- NUMERIC HELPER -----------------

def to_float(value):
    """
    Safely convert spreadsheet values to float:

    - '' / 'N/A' / 'na' / 'none' -> None
    - '50+' -> 50.0
    - '12%' -> 12.0
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"na", "n/a", "none"}:
        return None
    if s.endswith("+"):
        s = s[:-1]
    if s.endswith("%"):
        s = s[:-1]
    try:
        return float(s)
    except ValueError:
        return None


# ----------------- COMPARISON TABLE BUILDERS -----------------

def build_sunscreen_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    For selected sunscreen rows, build:

      Product,
      SPF_lab (UVB),
      UVA_PF_lab,
      Blue_light_lab,
      Visible_lab,
      Price_per_ml_£
    """
    if df.empty:
        return pd.DataFrame()

    col_spf_lab = "SPF (lab)"
    col_uva_lab = "UVA Protection (Lab)"
    col_bl_lab = "Blue Light Protection (lab)"
    col_vis_lab = "Visible Protection (lab)"
    col_price = "Price (£)"
    col_vol = "Volume (ml)"

    rows = []
    for _, row in df.iterrows():
        name = make_label(row, "sun")

        spf_lab = to_float(row.get(col_spf_lab, ""))
        uva_pf = to_float(row.get(col_uva_lab, ""))
        bl = to_float(row.get(col_bl_lab, ""))
        vis = to_float(row.get(col_vis_lab, ""))
        price = to_float(row.get(col_price, ""))
        vol = to_float(row.get(col_vol, ""))

        price_per_ml = None
        if price is not None and vol not in (None, 0):
            price_per_ml = price / vol

        rows.append(
            {
                "Product": name,
                "SPF_lab (UVB)": spf_lab,
                "UVA_PF_lab": uva_pf,
                "Blue_light_lab": bl,
                "Visible_lab": vis,
                "Price_per_ml_£": price_per_ml,
            }
        )

    return pd.DataFrame(rows)


def build_clothing_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    For selected clothing rows, build:

      Product,
      SPF_lab (UVB),
      UVA_PF_lab,
      Blue_light_lab,
      Visible_lab,
      Price_£   (total price, not per ml)
    """
    if df.empty:
        return pd.DataFrame()

    col_spf_lab = "SPF (lab)"
    col_uva_lab = "UVA Protection (Lab)"
    col_bl_lab = "Blue Light Protection (lab)"
    col_vis_lab = "Visible Protection (lab)"
    col_price = "Price (£)"

    rows = []
    for _, row in df.iterrows():
        name = make_label(row, "cloth")

        spf_lab = to_float(row.get(col_spf_lab, ""))
        uva_pf = to_float(row.get(col_uva_lab, ""))
        bl = to_float(row.get(col_bl_lab, ""))
        vis = to_float(row.get(col_vis_lab, ""))
        price = to_float(row.get(col_price, ""))

        rows.append(
            {
                "Product": name,
                "SPF_lab (UVB)": spf_lab,
                "UVA_PF_lab": uva_pf,
                "Blue_light_lab": bl,
                "Visible_lab": vis,
                "Price_£": price,
            }
        )

    return pd.DataFrame(rows)


# ----------------- PLOTTING HELPERS -----------------

def plotly_bar(mdf, col, title, y_label, decimals):
    fig = px.bar(
        mdf,
        x="Product",
        y=col,
        color="Product",
        text_auto=f".{decimals}f",
        height=320,
        title=title,
    )
    fig.update_layout(
        xaxis_title="Product",
        yaxis_title=y_label,
        legend_title="Product",
        font=dict(size=17),
        title_font=dict(size=20),
    )
    return fig


def plot_metric_bars(df: pd.DataFrame, col: str, title: str,
                     y_label: str, decimals: int, target_col):
    """
    Render one grouped bar chart for a single metric column into target_col.

    Charts are sized for half-width columns (for side-by-side layout).
    """
    if col not in df.columns:
        return

    mdf = df[["Product", col]].copy().dropna(subset=[col])
    if mdf.empty:
        return

    fig = plotly_bar(mdf, col, title, y_label, decimals)
    target_col.plotly_chart(fig, use_container_width=True)


def show_sunscreen_comparison(comp: pd.DataFrame):
    """5 charts for sunscreens: 4 protections + price per ml."""
    if comp.empty or len(comp) < 2:
        return

    st.markdown("### Comparison panel")
    st.caption(
        "Comparing SPF (lab, UVB), UVA PF (lab), blue & visible lab measures, "
        "and cost per ml for selected sunscreens."
    )

    # Row 1 (two plots)
    r1c1, r1c2 = st.columns(2)
    plot_metric_bars(comp, "SPF_lab (UVB)",
                     "SPF (lab) – UVB protection", "SPF (lab)", 1, r1c1)
    plot_metric_bars(comp, "UVA_PF_lab",
                     "UVA Protection (Lab) – PF", "UVA PF (lab)", 1, r1c2)

    # Row 2 (two plots)
    r2c1, r2c2 = st.columns(2)
    plot_metric_bars(comp, "Blue_light_lab",
                     "Blue light Protection (lab)", "Value", 2, r2c1)
    plot_metric_bars(comp, "Visible_lab",
                     "Visible light Protection (lab)", "Value", 2, r2c2)

    # Row 3 (single plot spanning)
    r3c1, _ = st.columns([1, 1])
    plot_metric_bars(comp, "Price_per_ml_£",
                     "Price per ml (£)", "£ per ml", 3, r3c1)


def show_clothing_comparison(comp: pd.DataFrame):
    """5 charts for clothing: 4 protections + price (£)."""
    if comp.empty or len(comp) < 2:
        return

    st.markdown("### Comparison panel")
    st.caption(
        "Comparing SPF (lab, UVB), UVA PF (lab), blue & visible lab measures, "
        "and total price (£) for selected garments."
    )

    # Row 1
    r1c1, r1c2 = st.columns(2)
    plot_metric_bars(comp, "SPF_lab (UVB)",
                     "SPF (lab) – UVB protection", "SPF (lab)", 1, r1c1)
    plot_metric_bars(comp, "UVA_PF_lab",
                     "UVA Protection (Lab) – PF", "UVA PF (lab)", 1, r1c2)

    # Row 2
    r2c1, r2c2 = st.columns(2)
    plot_metric_bars(comp, "Blue_light_lab",
                     "Blue light Protection (lab)", "Value", 2, r2c1)
    plot_metric_bars(comp, "Visible_lab",
                     "Visible light Protection (lab)", "Value", 2, r2c2)

    # Row 3 (price only)
    r3c1, _ = st.columns([1, 1])
    plot_metric_bars(comp, "Price_£",
                     "Price (£)", "£", 2, r3c1)


# ----------------- IMAGE STRIP (WORKING VERSION) -----------------

def show_product_images(df: pd.DataFrame, kind: str):
    """
    Display small thumbnails for the selected rows, using the 'Image' column.

    - Uses st.image with local paths or URLs.
    - Works reliably for your 'images/...' paths.
    """
    if df.empty or "Image" not in df.columns:
        return

    df_img = df[df["Image"].astype(str).str.strip() != ""]
    if df_img.empty:
        return

    st.markdown("#### Product images")

    cols = st.columns(len(df_img))
    for col_widget, (_, row) in zip(cols, df_img.iterrows()):
        img_ref = str(row.get("Image", "")).strip()
        if not img_ref:
            continue

        # Resolve to URL or local file
        if img_ref.lower().startswith(("http://", "https://")):
            img_path = img_ref
        else:
            # treat as relative to app.py
            img_path = Path(__file__).parent / img_ref

        label = make_label(row, kind)
        try:
            col_widget.image(str(img_path), width=120, caption=label)
        except Exception:
            col_widget.write(label)


# ----------------- LOAD SHEETS -----------------

try:
    suns = load_sheet(DATA_XLSX, SHEET_SUN)
except Exception as e:
    suns = pd.DataFrame()
    st.error(f"Could not load sheet '{SHEET_SUN}' from {DATA_XLSX.name}: {e}")

try:
    cloth = load_sheet(DATA_XLSX, SHEET_CLO)
except Exception as e:
    cloth = pd.DataFrame()
    st.error(f"Could not load sheet '{SHEET_CLO}' from {DATA_XLSX.name}: {e}")


# ----------------- HELPER: SAFE COLUMN SELECTION -----------------

def safe_select_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Return df with only columns that actually exist."""
    present = [c for c in cols if c in df.columns]
    if not present:
        return df.iloc[:, 0:0]  # empty with same index
    return df[present].copy()


# ----------------- UI: TABS -----------------

tab1, tab2 = st.tabs(["Sunscreens", "Clothing"])


# ---- Sunscreens tab ----
with tab1:
    if suns.empty:
        st.info("No sunscreen data yet. Add rows to the 'Sunscreens' sheet.")
    else:
        labels_sun = suns.apply(lambda r: make_label(r, "sun"), axis=1)

        left, right = st.columns([2, 1])
        with left:
            chosen_sun = st.multiselect(
                "Choose up to 3 products to compare:",
                options=labels_sun.tolist(),
                max_selections=3,
                key="sun_select",
            )
        with right:
            show_all_sun = st.toggle(
                "Show all products (ignore selection)",
                value=False,
                key="sun_show_all",
            )

        if show_all_sun:
            view_sun = suns
        else:
            mask = labels_sun.isin(chosen_sun)
            view_sun = suns.loc[mask, suns.columns.tolist()]

        # Comparison plots (only when 2–3 products specifically selected)
        if not show_all_sun and 1 < len(view_sun) <= 3:
            comp_sun = build_sunscreen_comparison(view_sun)
            show_sunscreen_comparison(comp_sun)

        # Thumbnails for the selected products
        show_product_images(view_sun, kind="sun")

        # Patient-facing table
        view_sun_display = safe_select_columns(view_sun, SUN_DISPLAY_COLS)
        st.dataframe(
            view_sun_display,
            use_container_width=True,
            hide_index=True,
        )


# ---- Clothing tab ----
with tab2:
    if cloth.empty:
        st.info("No clothing data yet. Add rows to the 'Clothing' sheet.")
    else:
        labels_cloth = cloth.apply(lambda r: make_label(r, "cloth"), axis=1)

        left, right = st.columns([2, 1])
        with left:
            chosen_cloth = st.multiselect(
                "Choose up to 3 garments to compare:",
                options=labels_cloth.tolist(),
                max_selections=3,
                key="cloth_select",
            )
        with right:
            show_all_cloth = st.toggle(
                "Show all garments (ignore selection)",
                value=False,
                key="cloth_show_all",
            )

        if show_all_cloth:
            view_cloth = cloth
        else:
            mask = labels_cloth.isin(chosen_cloth)
            view_cloth = cloth.loc[mask, cloth.columns.tolist()]

        if not show_all_cloth and 1 < len(view_cloth) <= 3:
            comp_cloth = build_clothing_comparison(view_cloth)
            show_clothing_comparison(comp_cloth)

        show_product_images(view_cloth, kind="cloth")

        view_cloth_display = safe_select_columns(view_cloth, CLO_DISPLAY_COLS)
        st.dataframe(
            view_cloth_display,
            use_container_width=True,
            hide_index=True,
        )
