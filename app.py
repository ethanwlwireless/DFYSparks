import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# =====================================================
# DFY SPARKS DLAR DASHBOARD
# Entity-restricted Streamlit dashboard
# =====================================================

st.set_page_config(
    page_title="DFY Sparks DLAR Dashboard",
    page_icon="⚡",
    layout="wide"
)

ENTITY_NAME = "DFY Sparks"

DEFAULT_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1p4oZCjqQuAW8fv0kLZ1lU2NtMQaMi6K7Z0gzZUPt1Iw"
    "/export?format=csv&gid=0"
)

SHEET_CSV_URL = st.secrets.get("SHEET_CSV_URL", DEFAULT_SHEET_CSV_URL)


# =====================================================
# HELPERS
# =====================================================

@st.cache_data(ttl=300)
def load_data(url: str) -> pd.DataFrame:
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Unable to load Google Sheet data: {e}")
        return pd.DataFrame()


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def find_col(df: pd.DataFrame, possible_names: list[str]):
    normalized_columns = {col.strip().lower(): col for col in df.columns}

    for name in possible_names:
        if name.lower() in normalized_columns:
            return normalized_columns[name.lower()]

    for col in df.columns:
        col_lower = col.lower()
        for name in possible_names:
            if name.lower() in col_lower:
                return col

    return None


def to_number(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
        .replace(["", "nan", "None"], "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def format_percent(value):
    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "0.0%"


# =====================================================
# LOAD DATA
# =====================================================

st.title("⚡ DFY Sparks DLAR Dashboard")
st.caption("Restricted view: DFY Sparks entity only")

df = load_data(SHEET_CSV_URL)

if df.empty:
    st.warning("No data loaded. Please confirm the Google Sheet is shared as 'Anyone with the link can view'.")
    st.stop()

df = clean_columns(df)


# =====================================================
# COLUMN DETECTION
# =====================================================

entity_col = find_col(df, [
    "Entity",
    "Sub-Agent Name",
    "Sub Agent Name",
    "Dealer Entity",
    "Owner Entity",
    "Master Agent",
])

store_col = find_col(df, [
    "Store ID",
    "Door TSP",
    "TSP ID",
    "Door ID",
    "Store",
])

acts_col = find_col(df, [
    "Current Acts",
    "Current Activations",
    "Activation",
    "Activations",
    "Acts",
])

pacing_col = find_col(df, [
    "Pacing %",
    "Activation % to Target",
    "Activation Percentage to Target",
    "Pacing",
    "Act % to Target",
])

mr_col = find_col(df, [
    "4MR %",
    "4MR",
    "4 Month Retention",
    "4 Month Retention %",
    "Retention %",
    "3MR %",
    "3MR",
])

address_col = find_col(df, ["Address", "Store Address"])
city_col = find_col(df, ["City"])
state_col = find_col(df, ["State"])
zip_col = find_col(df, ["Zip Code", "Zip"])
status_col = find_col(df, ["Status"])
market_col = find_col(df, ["Market"])
region_col = find_col(df, ["Region"])
rep_col = find_col(df, ["MA Field Rep", "Field Rep", "Rep", "DM"])


if not entity_col:
    st.error("Entity column not found. Please make sure the sheet has an Entity or Sub-Agent Name column.")
    with st.expander("Detected columns"):
        st.write(list(df.columns))
    st.stop()


# =====================================================
# DFY SPARKS ONLY FILTER
# =====================================================

df_entity = df[
    df[entity_col].astype(str).str.strip().str.lower() == ENTITY_NAME.lower()
].copy()

if df_entity.empty:
    st.warning(f"No records found for entity: {ENTITY_NAME}")
    with st.expander("Entity values found in the sheet"):
        st.write(sorted(df[entity_col].dropna().astype(str).unique()))
    st.stop()


# =====================================================
# NUMERIC CLEANING
# =====================================================

if acts_col:
    df_entity[acts_col] = to_number(df_entity[acts_col])

if pacing_col:
    df_entity[pacing_col] = to_number(df_entity[pacing_col])

if mr_col:
    df_entity[mr_col] = to_number(df_entity[mr_col])


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Dashboard Filters")
st.sidebar.caption("This app is locked to DFY Sparks only.")

filtered = df_entity.copy()

if status_col:
    status_options = sorted(filtered[status_col].dropna().astype(str).unique())
    selected_status = st.sidebar.multiselect("Status", status_options, default=status_options)
    if selected_status:
        filtered = filtered[filtered[status_col].astype(str).isin(selected_status)]

if city_col:
    city_options = sorted(filtered[city_col].dropna().astype(str).unique())
    selected_city = st.sidebar.multiselect("City", city_options, default=city_options)
    if selected_city:
        filtered = filtered[filtered[city_col].astype(str).isin(selected_city)]

if market_col:
    market_options = sorted(filtered[market_col].dropna().astype(str).unique())
    selected_market = st.sidebar.multiselect("Market", market_options, default=market_options)
    if selected_market:
        filtered = filtered[filtered[market_col].astype(str).isin(selected_market)]

search_term = st.sidebar.text_input("Search store / address / city")

if search_term:
    search_columns = [c for c in [store_col, address_col, city_col, state_col, zip_col] if c]
    if search_columns:
        mask = pd.Series(False, index=filtered.index)
        for c in search_columns:
            mask = mask | filtered[c].astype(str).str.contains(search_term, case=False, na=False)
        filtered = filtered[mask]


# =====================================================
# KPI SUMMARY
# =====================================================

total_rows = len(filtered)
total_stores = filtered[store_col].nunique() if store_col else total_rows
total_acts = filtered[acts_col].sum() if acts_col else 0
avg_pacing = filtered[pacing_col].mean() if pacing_col else 0
avg_retention = filtered[mr_col].mean() if mr_col else 0

k1, k2, k3, k4 = st.columns(4)

k1.metric("Stores", f"{total_stores:,.0f}")
k2.metric("Current Acts", f"{total_acts:,.0f}")
k3.metric("Avg Pacing", format_percent(avg_pacing))
k4.metric("Avg Retention", format_percent(avg_retention))


# =====================================================
# EXECUTIVE SUMMARY
# =====================================================

st.divider()
st.subheader("Executive Summary")

summary_left, summary_right = st.columns([2, 1])

with summary_left:
    st.write(
        f"""
        **DFY Sparks** currently has **{total_stores:,.0f} store(s)** in this filtered view, 
        with **{total_acts:,.0f} current activation(s)**.

        Average pacing is **{avg_pacing:.1f}%** and average retention is **{avg_retention:.1f}%**.
        """
    )

with summary_right:
    st.info(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")


# =====================================================
# CHARTS
# =====================================================

st.divider()
st.subheader("Performance Charts")

if store_col and acts_col:
    chart_df = (
        filtered.groupby(store_col, as_index=False)[acts_col]
        .sum()
        .sort_values(acts_col, ascending=False)
    )

    fig = px.bar(
        chart_df,
        x=store_col,
        y=acts_col,
        text=acts_col,
        title="Current Acts by Store"
    )
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig.update_layout(xaxis_title="Store", yaxis_title="Current Acts")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Current Acts chart unavailable because Store ID or Current Acts column was not found.")

if store_col and pacing_col:
    pacing_df = (
        filtered.groupby(store_col, as_index=False)[pacing_col]
        .mean()
        .sort_values(pacing_col, ascending=False)
    )

    fig2 = px.bar(
        pacing_df,
        x=store_col,
        y=pacing_col,
        text=pacing_col,
        title="Average Pacing % by Store"
    )
    fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig2.update_layout(xaxis_title="Store", yaxis_title="Pacing %")
    st.plotly_chart(fig2, use_container_width=True)

if store_col and mr_col:
    mr_df = (
        filtered.groupby(store_col, as_index=False)[mr_col]
        .mean()
        .sort_values(mr_col, ascending=False)
    )

    fig3 = px.bar(
        mr_df,
        x=store_col,
        y=mr_col,
        text=mr_col,
        title="Average Retention % by Store"
    )
    fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig3.update_layout(xaxis_title="Store", yaxis_title="Retention %")
    st.plotly_chart(fig3, use_container_width=True)


# =====================================================
# STORE TABLE
# =====================================================

st.divider()
st.subheader("DFY Sparks Store Detail")

preferred_cols = [
    store_col,
    entity_col,
    address_col,
    city_col,
    state_col,
    zip_col,
    status_col,
    market_col,
    region_col,
    rep_col,
    acts_col,
    pacing_col,
    mr_col,
]

display_cols = []
for col in preferred_cols:
    if col and col in filtered.columns and col not in display_cols:
        display_cols.append(col)

if display_cols:
    st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)
else:
    st.dataframe(filtered, use_container_width=True, hide_index=True)


# =====================================================
# DOWNLOAD
# =====================================================

st.download_button(
    label="Download DFY Sparks CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="dfy_sparks_dlar_filtered.csv",
    mime="text/csv"
)


# =====================================================
# DEBUG PANEL
# =====================================================

with st.expander("Debug / Column Mapping"):
    st.write({
        "entity_col": entity_col,
        "store_col": store_col,
        "acts_col": acts_col,
        "pacing_col": pacing_col,
        "retention_col": mr_col,
        "address_col": address_col,
        "city_col": city_col,
        "state_col": state_col,
        "status_col": status_col,
        "market_col": market_col,
        "region_col": region_col,
        "rep_col": rep_col,
    })
    st.write("All detected columns:")
    st.write(list(df.columns))
