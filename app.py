import streamlit as st
import pandas as pd
from datetime import datetime

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


@st.cache_data(ttl=300)
def load_data(url: str):
    try:
        raw = pd.read_csv(url, header=None, dtype=str)

        avg_row = raw.iloc[3].copy()
        headers = raw.iloc[4].astype(str).str.strip()

        df = raw.iloc[5:].copy()
        df.columns = headers
        df.columns = df.columns.astype(str).str.strip()

        avg_df = pd.DataFrame([avg_row.values], columns=headers)
        avg_df.columns = avg_df.columns.astype(str).str.strip()

        return df, avg_df

    except Exception as e:
        st.error(f"Unable to load Google Sheet data: {e}")
        return pd.DataFrame(), pd.DataFrame()


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
        .replace(["", "nan", "None", "NaN", "-", "#DIV/0!"], "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def get_avg_value(avg_df: pd.DataFrame, col_name):
    if not col_name or avg_df.empty or col_name not in avg_df.columns:
        return 0

    value = to_number(avg_df[col_name]).iloc[0]

    if abs(value) <= 1 and value != 0:
        value = value * 100

    return value


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
    if not source_col or source_col not in df.columns:
        return df

    numeric = to_number(df[source_col])

    if len(numeric[numeric != 0]) > 0 and numeric[numeric != 0].abs().max() <= 1:
        numeric = numeric * 100

    df[new_col] = numeric.map(lambda x: f"{x:.1f}%")
    return df


st.title("⚡ DFY Sparks DLAR Dashboard")
st.caption("Restricted dashboard for DFY Sparks / DFY-Sparks Inc / DFY Sparks 101")

df, avg_df = load_data(SHEET_CSV_URL)

if df.empty:
    st.warning("No data loaded. Check Google Sheet sharing: Anyone with the link → Viewer.")
    st.stop()


sub_agent_col = find_col(df, ["Sub-Agent Name", "Sub Agent Name", "Sub-Agent", "Sub Agent"])
entity_col = find_col(df, ["Entity", "Dealer Entity", "Owner Entity", "Ownership Entity", "Entity Name"])
master_agent_col = find_col(df, ["Master Agent", "Master Agent Name"])

door_tsp_col = find_col(df, ["Door TSP", "Store ID", "TSP ID", "Door ID", "Store"])
address_col = find_col(df, ["Address", "Store Address"])
status_col = find_col(df, ["Status"])
city_col = find_col(df, ["City"])
market_col = find_col(df, ["Market"])
region_col = find_col(df, ["Region"])
state_col = find_col(df, ["State"])
zip_col = find_col(df, ["Zip Code", "Zip"])
rep_col = find_col(df, ["MA Field Rep", "Field Rep", "Rep", "DM"])

current_acts_col = find_col(df, ["Current Acts", "Current Activations", "Current Activation", "Activations", "Acts"])
pacing_acts_col = find_col(df, ["Pacing Acts", "Pacing Act", "Pacing Activations"])
pacing_pct_col = find_col(df, ["Pacing % to Quota", "Pacing %", "Activation % to Target", "Act % to Target"])

current_4mr_pct_col = find_col(df, ["Current 4MR%", "Current 4MR %", "4MR %", "4MR%"])

current_topups_col = find_col(df, ["Current Topups", "Current Top Ups", "Current Top-Ups", "Topups", "Top Ups"])
edge_apply_col = find_col(df, ["Current Edge Apply", "Edge Apply", "Current Edge Applies", "Edge Applies"])
edge_approve_col = find_col(df, ["Current Edge Approve", "Edge Approve", "Current Edge Approved", "Edge Approved", "Edge Approvals"])
edge_acts_col = find_col(df, ["Current Edge Acts", "Edge Acts", "Current Edge Activations", "Edge Activations"])


candidate_entity_cols = list(dict.fromkeys([
    c for c in [sub_agent_col, entity_col, master_agent_col] if c
]))

if not candidate_entity_cols:
    st.error("Could not find Sub-Agent Name, Entity, or Master Agent column.")
    st.stop()

df_entity = df[build_dfy_mask(df, candidate_entity_cols)].copy()

if df_entity.empty:
    st.warning("No DFY Sparks records found.")
    st.stop()


for col in [
    current_acts_col,
    pacing_acts_col,
    pacing_pct_col,
    current_4mr_pct_col,
    current_topups_col,
    edge_apply_col,
    edge_approve_col,
    edge_acts_col,
]:
    if col and col in df_entity.columns:
        df_entity[col] = to_number(df_entity[col])


filtered = df_entity.copy()

st.sidebar.header("Search")
st.sidebar.caption("DFY Sparks only")

search_term = st.sidebar.text_input(
    "Search Store / Address / City / Rep",
    placeholder="Search..."
)

if search_term:
    search_columns = [
        c for c in [
            door_tsp_col,
            address_col,
            city_col,
            market_col,
            rep_col,
            status_col,
        ]
        if c
    ]

    mask = pd.Series(False, index=filtered.index)

    for c in search_columns:
        mask = mask | filtered[c].astype(str).str.contains(
            search_term,
            case=False,
            na=False
        )

    filtered = filtered[mask]


total_stores = filtered[door_tsp_col].nunique() if door_tsp_col else len(filtered)
total_current_acts = filtered[current_acts_col].sum() if current_acts_col else 0

avg_pacing = get_avg_value(avg_df, pacing_pct_col)
avg_4mr = get_avg_value(avg_df, current_4mr_pct_col)


k1, k2, k3, k4 = st.columns(4)

k1.metric("Stores", f"{total_stores:,.0f}")
k2.metric("Current Acts", f"{total_current_acts:,.0f}")
k3.metric("Avg Pacing", pct_text(avg_pacing))
k4.metric("Average 4MR %", pct_text(avg_4mr))


st.divider()
st.subheader("DFY Sparks Store Detail")

table = filtered.copy()

if pacing_pct_col:
    table = add_percent_column(table, pacing_pct_col, "Pacing % to Quota")
elif current_acts_col and pacing_acts_col:
    denom = table[pacing_acts_col].replace(0, pd.NA)
    table["Pacing % to Quota"] = (
        (table[current_acts_col] / denom) * 100
    ).fillna(0).map(lambda x: f"{x:.1f}%")

if current_4mr_pct_col:
    table = add_percent_column(table, current_4mr_pct_col, "Current 4MR %")


base_display_map = []

if door_tsp_col:
    base_display_map.append((door_tsp_col, "Door TSP"))
if address_col:
    base_display_map.append((address_col, "Address"))
if current_acts_col:
    base_display_map.append((current_acts_col, "Current Acts"))
if pacing_acts_col:
    base_display_map.append((pacing_acts_col, "Pacing Acts"))

base_display_map.append(("Pacing % to Quota", "Pacing % to Quota"))
base_display_map.append(("Current 4MR %", "Current 4MR %"))

if current_topups_col:
    base_display_map.append((current_topups_col, "Current Topups"))
if edge_apply_col:
    base_display_map.append((edge_apply_col, "Current Edge Apply"))
if edge_approve_col:
    base_display_map.append((edge_approve_col, "Current Edge Approve"))
if edge_acts_col:
    base_display_map.append((edge_acts_col, "Current Edge Acts"))


base_cols = []
rename_map = {}

for source, label in base_display_map:
    if source in table.columns and source not in base_cols:
        base_cols.append(source)
        rename_map[source] = label


st.sidebar.divider()
st.sidebar.header("Additional Columns")

all_extra_cols = [
    col for col in table.columns
    if col not in base_cols
]

extra_cols = st.sidebar.multiselect(
    "Show more columns",
    options=all_extra_cols,
    default=[],
)

final_selected_cols = base_cols + extra_cols

if final_selected_cols:
    detail_df = table[final_selected_cols].rename(columns=rename_map)

    if "Current Acts" in detail_df.columns:
        detail_df = detail_df.sort_values("Current Acts", ascending=False)

    row_count = len(detail_df)
    table_height = max(420, row_count * 38 + 45)

    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True,
        height=table_height
    )

    st.download_button(
        label="Download DFY Sparks Store Detail CSV",
        data=detail_df.to_csv(index=False).encode("utf-8"),
        file_name="dfy_sparks_store_detail.csv",
        mime="text/csv"
    )
else:
    st.warning("Could not build the requested store detail table.")

st.caption(f"DLAR updated: {datetime.now().strftime('%Y-%m-%d')}")
