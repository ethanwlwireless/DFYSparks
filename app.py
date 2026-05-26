import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# =====================================================
# DFY SPARKS DLAR DASHBOARD V3
# Clean operating dashboard for DFY Sparks only
# =====================================================

st.set_page_config(
    page_title="DFY Sparks DLAR Dashboard",
    page_icon="⚡",
    layout="wide"
)

DEFAULT_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1p4oZCjqQuAW8fv0kLZ1lU2NtMQaMi6K7Z0gzZUPt1Iw"
    "/export?format=csv&gid=0"
)

SHEET_CSV_URL = st.secrets.get("SHEET_CSV_URL", DEFAULT_SHEET_CSV_URL)

DFY_KEYWORDS = [
    "dfy sparks",
    "dfy-sparks",
    "dfy sparks 101",
]


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


def normalize_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )


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
        .replace(["", "nan", "None", "NaN", "-"], "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def pct_text(value):
    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "0.0%"


def build_dfy_mask(df: pd.DataFrame, candidate_cols: list[str]) -> pd.Series:
    mask = pd.Series(False, index=df.index)

    for col in candidate_cols:
        if col and col in df.columns:
            values = normalize_series(df[col])
            for keyword in DFY_KEYWORDS:
                mask = mask | values.str.contains(keyword, na=False, regex=False)

    return mask


def add_percent_column(df: pd.DataFrame, source_col: str, new_col: str) -> pd.DataFrame:
    """
    Creates display-friendly percentage text column.
    If source values are already 0-100, keeps them.
    If source values look like decimals 0-1, converts to 0-100.
    """
    if not source_col or source_col not in df.columns:
        return df

    numeric = to_number(df[source_col])

    # If most values are between 0 and 1, treat as decimal percentage.
    nonzero = numeric[numeric != 0]
    if len(nonzero) > 0 and nonzero.abs().max() <= 1:
        numeric = numeric * 100

    df[new_col] = numeric.map(lambda x: f"{x:.1f}%")
    return df


# =====================================================
# LOAD DATA
# =====================================================

st.title("⚡ DFY Sparks DLAR Dashboard")
st.caption("Restricted dashboard for DFY Sparks / DFY-Sparks Inc / DFY Sparks 101")

df = load_data(SHEET_CSV_URL)

if df.empty:
    st.warning("No data loaded. Check if Google Sheet sharing is set to: Anyone with the link → Viewer.")
    st.stop()

df = clean_columns(df)


# =====================================================
# COLUMN DETECTION
# =====================================================

sub_agent_col = find_col(df, [
    "Sub-Agent Name",
    "Sub Agent Name",
    "Sub-Agent",
    "Sub Agent",
])

entity_col = find_col(df, [
    "Entity",
    "Dealer Entity",
    "Owner Entity",
    "Ownership Entity",
    "Entity Name",
])

master_agent_col = find_col(df, [
    "Master Agent",
    "Master Agent Name",
])

door_tsp_col = find_col(df, [
    "Door TSP",
    "Store ID",
    "TSP ID",
    "Door ID",
    "Store",
])

address_col = find_col(df, [
    "Address",
    "Store Address",
])

status_col = find_col(df, ["Status"])
city_col = find_col(df, ["City"])
market_col = find_col(df, ["Market"])

current_acts_col = find_col(df, [
    "Current Acts",
    "Current Activations",
    "Current Activation",
    "Activations",
    "Acts",
])

pacing_acts_col = find_col(df, [
    "Pacing Acts",
    "Pacing Act",
    "Pacing Activations",
])

pacing_pct_col = find_col(df, [
    "Pacing % to Quota",
    "Pacing % to quota",
    "Pacing % To Quota",
    "Pacing %",
    "Activation % to Target",
    "Activation Percentage to Target",
    "Act % to Target",
])

current_4mr_pct_col = find_col(df, [
    "Current 4MR%",
    "Current 4MR %",
    "4MR %",
    "4MR%",
    "Current TWP 4MR %",
    "Current TWP 3MR Acts",
    "3MR %",
    "Current 3MR %",
])

current_topups_col = find_col(df, [
    "Current Topups",
    "Current Top Ups",
    "Current Top-Ups",
    "Topups",
    "Top Ups",
    "Top-Ups",
])

edge_apply_col = find_col(df, [
    "Current Edge Apply",
    "Edge Apply",
    "Current Edge Applies",
    "Edge Applies",
])

edge_approve_col = find_col(df, [
    "Current Edge Approve",
    "Edge Approve",
    "Current Edge Approved",
    "Edge Approved",
    "Edge Approvals",
])

edge_acts_col = find_col(df, [
    "Current Edge Acts",
    "Edge Acts",
    "Current Edge Activations",
    "Edge Activations",
])


# =====================================================
# DFY SPARKS FILTER
# =====================================================

candidate_entity_cols = [
    sub_agent_col,
    entity_col,
    master_agent_col,
]

candidate_entity_cols = list(dict.fromkeys([c for c in candidate_entity_cols if c]))

if not candidate_entity_cols:
    st.error("Could not find Sub-Agent Name, Entity, or Master Agent column.")
    with st.expander("Detected columns"):
        st.write(list(df.columns))
    st.stop()

dfy_mask = build_dfy_mask(df, candidate_entity_cols)
df_entity = df[dfy_mask].copy()

if df_entity.empty:
    st.warning("No DFY Sparks records found.")
    with st.expander("Entity search columns checked"):
        st.write(candidate_entity_cols)
    with st.expander("Detected columns"):
        st.write(list(df.columns))
    st.stop()


# =====================================================
# NUMERIC CLEANING
# =====================================================

numeric_cols = [
    current_acts_col,
    pacing_acts_col,
    pacing_pct_col,
    current_4mr_pct_col,
    current_topups_col,
    edge_apply_col,
    edge_approve_col,
    edge_acts_col,
]

for col in numeric_cols:
    if col and col in df_entity.columns:
        df_entity[col] = to_number(df_entity[col])


# =====================================================
# SIDEBAR FILTERS
# =====================================================

st.sidebar.header("Dashboard Filters")
st.sidebar.caption("Locked to DFY Sparks-related entities only.")

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

search_term = st.sidebar.text_input("Search door / address")

if search_term:
    search_columns = [c for c in [door_tsp_col, address_col] if c]
    if search_columns:
        mask = pd.Series(False, index=filtered.index)
        for c in search_columns:
            mask = mask | filtered[c].astype(str).str.contains(search_term, case=False, na=False)
        filtered = filtered[mask]


# =====================================================
# DIRECT CALCULATIONS
# =====================================================

total_stores = filtered[door_tsp_col].nunique() if door_tsp_col else len(filtered)
total_current_acts = filtered[current_acts_col].sum() if current_acts_col else 0

# Direct calculation for Avg Pacing:
# Total Current Acts / Total Pacing Acts * 100
if current_acts_col and pacing_acts_col and filtered[pacing_acts_col].sum() != 0:
    avg_pacing = (filtered[current_acts_col].sum() / filtered[pacing_acts_col].sum()) * 100
elif pacing_pct_col:
    avg_pacing = filtered[pacing_pct_col].mean()
else:
    avg_pacing = 0

# Direct calculation for Average 4MR %
# Uses average of detected Current 4MR% column.
# If values are decimal-style, converts to percent.
if current_4mr_pct_col:
    four_mr_values = filtered[current_4mr_pct_col].copy()
    nonzero_4mr = four_mr_values[four_mr_values != 0]
    if len(nonzero_4mr) > 0 and nonzero_4mr.abs().max() <= 1:
        four_mr_values = four_mr_values * 100
    avg_4mr = four_mr_values.mean()
else:
    avg_4mr = 0


# =====================================================
# KPI CARDS
# =====================================================

k1, k2, k3, k4 = st.columns(4)

k1.metric("Stores", f"{total_stores:,.0f}")
k2.metric("Current Acts", f"{total_current_acts:,.0f}")
k3.metric("Avg Pacing", pct_text(avg_pacing))
k4.metric("Average 4MR %", pct_text(avg_4mr))


# =====================================================
# EXECUTIVE SUMMARY
# =====================================================

st.divider()
st.subheader("Executive Summary")

left, right = st.columns([2, 1])

with left:
    st.write(
        f"""
        **DFY Sparks** currently shows **{total_stores:,.0f} store(s)** with 
        **{total_current_acts:,.0f} current activation(s)**.

        Average pacing is calculated directly as **Current Acts ÷ Pacing Acts**, showing **{avg_pacing:.1f}%**.
        Average 4MR is calculated from the store-level 4MR values, showing **{avg_4mr:.1f}%**.
        """
    )

with right:
    st.info(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")


# =====================================================
# PERFORMANCE CHARTS
# =====================================================

st.divider()
st.subheader("Performance Charts")

if door_tsp_col and current_acts_col:
    acts_chart = (
        filtered.groupby(door_tsp_col, as_index=False)[current_acts_col]
        .sum()
        .sort_values(current_acts_col, ascending=False)
    )

    fig = px.bar(
        acts_chart,
        x=door_tsp_col,
        y=current_acts_col,
        text=current_acts_col,
        title="Current Acts by Store"
    )
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig.update_layout(xaxis_title="Door TSP", yaxis_title="Current Acts")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Current Acts by Store chart unavailable. Door TSP or Current Acts column was not found.")

if door_tsp_col and current_4mr_pct_col:
    mr_chart = filtered.copy()

    # Normalize 4MR for chart display
    mr_chart["_4MR_PERCENT_FOR_CHART"] = mr_chart[current_4mr_pct_col]
    nonzero_chart = mr_chart["_4MR_PERCENT_FOR_CHART"][mr_chart["_4MR_PERCENT_FOR_CHART"] != 0]
    if len(nonzero_chart) > 0 and nonzero_chart.abs().max() <= 1:
        mr_chart["_4MR_PERCENT_FOR_CHART"] = mr_chart["_4MR_PERCENT_FOR_CHART"] * 100

    mr_chart = (
        mr_chart.groupby(door_tsp_col, as_index=False)["_4MR_PERCENT_FOR_CHART"]
        .mean()
        .sort_values("_4MR_PERCENT_FOR_CHART", ascending=False)
    )

    fig2 = px.bar(
        mr_chart,
        x=door_tsp_col,
        y="_4MR_PERCENT_FOR_CHART",
        text="_4MR_PERCENT_FOR_CHART",
        title="4MR % by Store"
    )
    fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig2.update_layout(xaxis_title="Door TSP", yaxis_title="4MR %")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("4MR % by Store chart unavailable. Door TSP or Current 4MR% column was not found.")


# =====================================================
# STORE DETAIL TABLE
# =====================================================

st.divider()
st.subheader("DFY Sparks Store Detail")

table = filtered.copy()

# Add display percent columns
if pacing_pct_col:
    table = add_percent_column(table, pacing_pct_col, "Pacing % to Quota")
elif current_acts_col and pacing_acts_col:
    denom = table[pacing_acts_col].replace(0, pd.NA)
    table["Pacing % to Quota"] = ((table[current_acts_col] / denom) * 100).fillna(0).map(lambda x: f"{x:.1f}%")

if current_4mr_pct_col:
    table = add_percent_column(table, current_4mr_pct_col, "Current 4MR %")

# Create clean display columns
display_map = []

if door_tsp_col:
    display_map.append((door_tsp_col, "Door TSP"))
if address_col:
    display_map.append((address_col, "Address"))
if current_acts_col:
    display_map.append((current_acts_col, "Current Acts"))
if pacing_acts_col:
    display_map.append((pacing_acts_col, "Pacing Acts"))

display_map.append(("Pacing % to Quota", "Pacing % to Quota"))

display_map.append(("Current 4MR %", "Current 4MR %"))

if current_topups_col:
    display_map.append((current_topups_col, "Current Topups"))
if edge_apply_col:
    display_map.append((edge_apply_col, "Current Edge Apply"))
if edge_approve_col:
    display_map.append((edge_approve_col, "Current Edge Approve"))
if edge_acts_col:
    display_map.append((edge_acts_col, "Current Edge Acts"))

final_cols = {}
for source, label in display_map:
    if source in table.columns:
        final_cols[source] = label

if final_cols:
    detail_df = table[list(final_cols.keys())].rename(columns=final_cols)

    # Sort by Current Acts if present
    if "Current Acts" in detail_df.columns:
        detail_df = detail_df.sort_values("Current Acts", ascending=False)

    st.dataframe(detail_df, use_container_width=True, hide_index=True)
else:
    st.warning("Could not build the requested store detail table because matching columns were not found.")


# =====================================================
# DOWNLOAD
# =====================================================

if final_cols:
    st.download_button(
        label="Download DFY Sparks Store Detail CSV",
        data=detail_df.to_csv(index=False).encode("utf-8"),
        file_name="dfy_sparks_store_detail.csv",
        mime="text/csv"
    )


# =====================================================
# DEBUG PANEL
# =====================================================

with st.expander("Debug / Column Mapping"):
    st.write("Entity columns searched:")
    st.write(candidate_entity_cols)

    st.write("Column mapping:")
    st.json({
        "sub_agent_col": sub_agent_col,
        "entity_col": entity_col,
        "master_agent_col": master_agent_col,
        "door_tsp_col": door_tsp_col,
        "address_col": address_col,
        "current_acts_col": current_acts_col,
        "pacing_acts_col": pacing_acts_col,
        "pacing_pct_col": pacing_pct_col,
        "current_4mr_pct_col": current_4mr_pct_col,
        "current_topups_col": current_topups_col,
        "edge_apply_col": edge_apply_col,
        "edge_approve_col": edge_approve_col,
        "edge_acts_col": edge_acts_col,
        "status_col": status_col,
        "city_col": city_col,
        "market_col": market_col,
    })

    st.write("All detected columns:")
    st.write(list(df.columns))
