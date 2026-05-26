import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# =====================================================
# DFY SPARKS DLAR DASHBOARD V2
# Finds DFY Sparks stores across multiple possible columns
# =====================================================

st.set_page_config(
    page_title="DFY Sparks DLAR Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Google Sheet CSV export URL
DEFAULT_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1p4oZCjqQuAW8fv0kLZ1lU2NtMQaMi6K7Z0gzZUPt1Iw"
    "/export?format=csv&gid=0"
)

SHEET_CSV_URL = st.secrets.get("SHEET_CSV_URL", DEFAULT_SHEET_CSV_URL)

# Exact/partial entity keywords we want to include
# This covers:
# DFY Sparks
# DFY-Sparks Inc
# DFY Sparks 101
DFY_KEYWORDS = [
    "dfy sparks",
    "dfy-sparks",
    "dfy sparks 101",
]


# =====================================================
# HELPER FUNCTIONS
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
    """
    Finds a column by exact match first, then partial match.
    """
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
        .replace(["", "nan", "None", "NaN"], "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def format_percent(value):
    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "0.0%"


def build_dfy_mask(df: pd.DataFrame, candidate_cols: list[str]) -> pd.Series:
    """
    Creates a TRUE/FALSE mask for rows related to DFY Sparks.
    It searches multiple columns instead of relying on only Sub-Agent Name.
    """
    mask = pd.Series(False, index=df.index)

    for col in candidate_cols:
        if col and col in df.columns:
            values = normalize_series(df[col])

            for keyword in DFY_KEYWORDS:
                mask = mask | values.str.contains(keyword, na=False, regex=False)

    return mask


# =====================================================
# LOAD DATA
# =====================================================

st.title("⚡ DFY Sparks DLAR Dashboard")
st.caption("Restricted view for DFY Sparks / DFY-Sparks Inc / DFY Sparks 101")

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
    "Pacing Acts",
    "Pacing %",
    "Activation % to Target",
    "Activation Percentage to Target",
    "Pacing",
    "Act % to Target",
])

retention_col = find_col(df, [
    "Current TWP 3MR Acts",
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
store_phone_col = find_col(df, ["Store Phone Number", "Phone Number", "Store Phone"])


# =====================================================
# DFY SPARKS FILTER
# =====================================================

candidate_entity_cols = [
    sub_agent_col,
    entity_col,
    master_agent_col,
]

# Remove None and duplicates
candidate_entity_cols = list(dict.fromkeys([c for c in candidate_entity_cols if c]))

if not candidate_entity_cols:
    st.error("Could not find any entity-related column such as Sub-Agent Name, Entity, or Master Agent.")
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

if acts_col:
    df_entity[acts_col] = to_number(df_entity[acts_col])

if pacing_col:
    df_entity[pacing_col] = to_number(df_entity[pacing_col])

if retention_col:
    df_entity[retention_col] = to_number(df_entity[retention_col])


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

search_term = st.sidebar.text_input("Search store / address / city")

if search_term:
    search_columns = [c for c in [store_col, address_col, city_col, state_col, zip_col, store_phone_col] if c]
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
avg_retention = filtered[retention_col].mean() if retention_col else 0

k1, k2, k3, k4 = st.columns(4)

k1.metric("Stores", f"{total_stores:,.0f}")
k2.metric("Current Acts", f"{total_acts:,.0f}")
k3.metric("Avg Pacing", format_percent(avg_pacing))
k4.metric("Avg Retention / 3MR", format_percent(avg_retention))


# =====================================================
# ENTITY NAME BREAKDOWN
# =====================================================

st.divider()
st.subheader("DFY Sparks Entity Breakdown")

breakdown_cols = [c for c in candidate_entity_cols if c in filtered.columns]

if breakdown_cols:
    breakdown_data = []
    for col in breakdown_cols:
        temp = (
            filtered.groupby(col, dropna=False)
            .agg(
                Stores=(store_col, "nunique") if store_col else (col, "count"),
                Rows=(col, "count"),
                Current_Acts=(acts_col, "sum") if acts_col else (col, "count"),
            )
            .reset_index()
        )
        temp.insert(0, "Source Column", col)
        temp = temp.rename(columns={col: "Entity Value"})
        breakdown_data.append(temp)

    entity_breakdown = pd.concat(breakdown_data, ignore_index=True)
    st.dataframe(entity_breakdown, use_container_width=True, hide_index=True)


# =====================================================
# EXECUTIVE SUMMARY
# =====================================================

st.divider()
st.subheader("Executive Summary")

left, right = st.columns([2, 1])

with left:
    st.write(
        f"""
        **DFY Sparks group** currently shows **{total_stores:,.0f} store(s)** in this dashboard, 
        with **{total_acts:,.0f} current activation(s)**.

        Average pacing is **{avg_pacing:.1f}%** and average retention / 3MR metric is **{avg_retention:.1f}%**.
        """
    )

with right:
    st.info(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")


# =====================================================
# PERFORMANCE CHARTS
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
        title="Average Pacing by Store"
    )
    fig2.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig2.update_layout(xaxis_title="Store", yaxis_title="Pacing")
    st.plotly_chart(fig2, use_container_width=True)

if store_col and retention_col:
    retention_df = (
        filtered.groupby(store_col, as_index=False)[retention_col]
        .mean()
        .sort_values(retention_col, ascending=False)
    )

    fig3 = px.bar(
        retention_df,
        x=store_col,
        y=retention_col,
        text=retention_col,
        title="Average Retention / 3MR by Store"
    )
    fig3.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig3.update_layout(xaxis_title="Store", yaxis_title="Retention / 3MR")
    st.plotly_chart(fig3, use_container_width=True)


# =====================================================
# STORE DETAIL TABLE
# =====================================================

st.divider()
st.subheader("DFY Sparks Store Detail")

preferred_cols = [
    store_col,
    sub_agent_col,
    entity_col,
    master_agent_col,
    address_col,
    city_col,
    state_col,
    zip_col,
    status_col,
    market_col,
    region_col,
    rep_col,
    store_phone_col,
    acts_col,
    pacing_col,
    retention_col,
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
    st.write("Candidate entity columns searched:")
    st.write(candidate_entity_cols)

    st.write("Column mapping:")
    st.json({
        "sub_agent_col": sub_agent_col,
        "entity_col": entity_col,
        "master_agent_col": master_agent_col,
        "store_col": store_col,
        "acts_col": acts_col,
        "pacing_col": pacing_col,
        "retention_col": retention_col,
        "address_col": address_col,
        "city_col": city_col,
        "state_col": state_col,
        "zip_col": zip_col,
        "status_col": status_col,
        "market_col": market_col,
        "region_col": region_col,
        "rep_col": rep_col,
        "store_phone_col": store_phone_col,
    })

    st.write("Unique values from searched entity columns:")
    for col in candidate_entity_cols:
        st.write(f"### {col}")
        st.write(sorted(df[col].dropna().astype(str).unique()))

    st.write("All detected columns:")
    st.write(list(df.columns))
