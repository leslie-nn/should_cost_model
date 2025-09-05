import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Should Cost Calculation v13 (Summary Scenarios Only)", layout="wide")

# ===== Helpers =====
def to_float(v):
    try:
        return float(v)
    except Exception:
        return np.nan

def dollars(x):
    try:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return "—"
        return f"${float(x):,.4f}"
    except Exception:
        return "—"

def recompute_base_per_lb(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure Base $/lb = Price ($/unit) × CF Value (unit/lb) for every row."""
    if df is None or df.empty:
        return df
    price = df.get("Price ($/unit)", pd.Series(dtype=float)).apply(to_float)
    cfval = df.get("CF Value (unit/lb)", pd.Series(dtype=float)).apply(to_float)
    df["Base $/lb"] = (price * cfval).astype(float)
    return df

def with_margin(x, margin_pct):
    m = margin_pct / 100.0
    return (x / (1 - m)) if (1 - m) > 0 else np.nan

# ===== Session Init =====
if "meta" not in st.session_state:
    st.session_state.meta = {"product": "", "analysis_date": str(date.today())}

if "margin_pct" not in st.session_state:
    st.session_state.margin_pct = 25.0

if "scenario_pct" not in st.session_state:
    st.session_state.scenario_pct = 10.0

SOURCE_TAGS = ["Manual Quote", "ChemAnalyst", "FRED", "Company Filing", "Other"]
CF_UNIT_OPTIONS = ["$/lb", "$/kg", "$/ton", "$/tonne", "$/MMBtu", "$/GJ", "$/kWh", "$/gal", "$/L"]

# Common columns (each section computes Base $/lb from Price and CF Value)
COMMON_COLS = [
    "Category","Item",
    "Price ($/unit)","CF Unit","CF Value (unit/lb)",
    "Base $/lb",
    "Source Tag","Source/Notes","Attachment"
]

if "raw_df" not in st.session_state:
    st.session_state.raw_df = pd.DataFrame(columns=COMMON_COLS)

if "mfg_df" not in st.session_state:
    st.session_state.mfg_df = pd.DataFrame(columns=COMMON_COLS)

if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=COMMON_COLS)

# ===== Header =====
st.title("Should Cost Calculation")
c1, c2 = st.columns(2)
with c1:
    st.session_state.meta["product"] = st.text_input("Product", st.session_state.meta["product"])
with c2:
    st.session_state.meta["analysis_date"] = st.date_input(
        "Analysis Date",
        pd.to_datetime(st.session_state.meta["analysis_date"])
    ).strftime("%Y-%m-%d")

# ===== 1.0 Raw Materials =====
with st.expander("1.0 Raw Materials", expanded=True):
    with st.form("add_raw_form", clear_on_submit=True):
        cr1, cr2, cr3 = st.columns([1,2,1])
        with cr1:
            raw_category = st.selectbox("Category", ["Primary","Secondary","Catalyst"], index=0)
        with cr2:
            raw_item = st.text_input("Item")
        with cr3:
            raw_cf_unit = st.selectbox("CF Unit", CF_UNIT_OPTIONS, index=0)

        cc1, cc2, cc3, cc4 = st.columns([1,1,1,1])
        with cc1:
            raw_price = st.number_input("Price ($/unit)", min_value=0.0, value=0.0, step=0.0001, format="%.6f")
        with cc2:
            raw_cf_val = st.number_input("CF Value (unit/lb)", min_value=0.0, value=0.0, step=0.00000001, format="%.8f")
        with cc3:
            raw_source_tag = st.selectbox("Source Tag", SOURCE_TAGS, index=0)
        with cc4:
            raw_source_notes = st.text_input("Source/Notes", placeholder="e.g., ChemAnalyst, Sep 2025")

        attach = st.file_uploader("Attachment (optional)", type=["pdf","png","jpg"], key="raw_attach")
        submitted = st.form_submit_button("Add row")

        if submitted:
            base = to_float(raw_price) * to_float(raw_cf_val)
            new_row = {
                "Category": raw_category, "Item": raw_item,
                "Price ($/unit)": raw_price, "CF Unit": raw_cf_unit, "CF Value (unit/lb)": raw_cf_val,
                "Base $/lb": base,
                "Source Tag": raw_source_tag, "Source/Notes": raw_source_notes,
                "Attachment": attach.name if attach else ""
            }
            st.session_state.raw_df = pd.concat([st.session_state.raw_df, pd.DataFrame([new_row])], ignore_index=True)

    # Editable table; Base $/lb is auto-recomputed after edits
    raw_edit = st.data_editor(
        st.session_state.raw_df,
        num_rows="dynamic",
        key="raw_editor",
        use_container_width=True,
        column_config={
            "Base $/lb": st.column_config.NumberColumn("Base $/lb", help="Auto: Price × CF Value", format="%.6f", disabled=True)
        },
        disabled=["Base $/lb"]  # disable direct edits on computed column
    )
    st.session_state.raw_df = recompute_base_per_lb(raw_edit)

# ===== 2.0 Plant Operation (formerly Manufacturing incl. Utilities) =====
with st.expander("2.0 Plant Operation", expanded=True):
    with st.form("add_mfg_form", clear_on_submit=True):
        mc0, mc1, mc2 = st.columns([1,2,1])
        with mc0:
            mfg_category = st.selectbox("Category", ["Utilities", "Manufacturing (process, labor, conversion)"], index=0)
        with mc1:
            mfg_item = st.text_input("Item ", key="mfg_item")
        with mc2:
            mfg_cf_unit = st.selectbox("CF Unit ", CF_UNIT_OPTIONS, index=0, key="mfg_cf_unit")

        md1, md2, md3, md4 = st.columns([1,1,1,2])
        with md1:
            mfg_price = st.number_input("Price ($/unit)", min_value=0.0, value=0.0, step=0.0001, format="%.6f")
        with md2:
            mfg_cf_val = st.number_input("CF Value (unit/lb)", min_value=0.0, value=0.0, step=0.00000001, format="%.8f")
        with md3:
            mfg_source_tag = st.selectbox("Source Tag ", SOURCE_TAGS, index=0, key="mfg_source_tag")
        with md4:
            mfg_source_notes = st.text_input("Source/Notes ", key="mfg_source_notes", placeholder="e.g., plant calc, 2025 plan")

        attach = st.file_uploader("Attachment (optional)", type=["pdf","png","jpg"], key="mfg_attach")
        submitted_m = st.form_submit_button("Add row")

        if submitted_m:
            base = to_float(mfg_price) * to_float(mfg_cf_val)
            new_m = {
                "Category": mfg_category, "Item": mfg_item,
                "Price ($/unit)": mfg_price, "CF Unit": mfg_cf_unit, "CF Value (unit/lb)": mfg_cf_val,
                "Base $/lb": base,
                "Source Tag": mfg_source_tag, "Source/Notes": mfg_source_notes,
                "Attachment": attach.name if attach else ""
            }
            st.session_state.mfg_df = pd.concat([st.session_state.mfg_df, pd.DataFrame([new_m])], ignore_index=True)

    mfg_edit = st.data_editor(
        st.session_state.mfg_df,
        num_rows="dynamic",
        key="mfg_editor",
        use_container_width=True,
        column_config={
            "Base $/lb": st.column_config.NumberColumn("Base $/lb", help="Auto: Price × CF Value", format="%.6f", disabled=True)
        },
        disabled=["Base $/lb"]
    )
    st.session_state.mfg_df = recompute_base_per_lb(mfg_edit)

# ===== 3.0 Logistics =====
with st.expander("3.0 Logistics", expanded=True):
    with st.form("add_log_form", clear_on_submit=True):
        lc0, lc1, lc2 = st.columns([1,2,1])
        with lc0:
            log_category = st.selectbox("Category", ["Transportation", "Fuel Surcharge", "Handling & Storage"], index=0)
        with lc1:
            log_item = st.text_input("Item", key="log_item")
        with lc2:
            log_cf_unit = st.selectbox("CF Unit", CF_UNIT_OPTIONS, index=0, key="log_cf_unit")

        ld1, ld2, ld3, ld4 = st.columns([1,1,1,2])
        with ld1:
            log_price = st.number_input("Price ($/unit)", min_value=0.0, value=0.0, step=0.0001, format="%.6f")
        with ld2:
            log_cf_val = st.number_input("CF Value (unit/lb)", min_value=0.0, value=0.0, step=0.00000001, format="%.8f")
        with ld3:
            log_source_tag = st.selectbox("Source Tag", SOURCE_TAGS, index=0, key="log_source_tag")
        with ld4:
            log_source_notes = st.text_input("Source/Notes", key="log_source_notes", placeholder="e.g., lane calc, carrier quote")

        attach = st.file_uploader("Attachment (optional)", type=["pdf","png","jpg"], key="log_attach")
        submitted_l = st.form_submit_button("Add row")

        if submitted_l:
            base = to_float(log_price) * to_float(log_cf_val)
            new_l = {
                "Category": log_category, "Item": log_item,
                "Price ($/unit)": log_price, "CF Unit": log_cf_unit, "CF Value (unit/lb)": log_cf_val,
                "Base $/lb": base,
                "Source Tag": log_source_tag, "Source/Notes": log_source_notes,
                "Attachment": attach.name if attach else ""
            }
            st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([new_l])], ignore_index=True)

    log_edit = st.data_editor(
        st.session_state.log_df,
        num_rows="dynamic",
        key="log_editor",
        use_container_width=True,
        column_config={
            "Base $/lb": st.column_config.NumberColumn("Base $/lb", help="Auto: Price × CF Value", format="%.6f", disabled=True)
        },
        disabled=["Base $/lb"]
    )
    st.session_state.log_df = recompute_base_per_lb(log_edit)

# ===== 4.0 Margin & Totals =====
with st.expander("4.0 Margin & Totals", expanded=True):
    st.session_state.margin_pct = st.number_input(
        "Gross Margin (%)",
        min_value=0.0, max_value=99.9,
        value=st.session_state.margin_pct, step=0.1, format="%.1f"
    )
    st.session_state.scenario_pct = st.slider("Scenario ±%", 0, 100, int(st.session_state.scenario_pct), step=1)

    # ---- Compute base subtotals (no per-row scenarios)
    def sum_base(df):
        if df is None or df.empty:
            return 0.0
        vals = pd.to_numeric(df.get("Base $/lb", pd.Series(dtype=float)), errors="coerce")
        return float(np.nansum(vals))

    raw_base = sum_base(st.session_state.raw_df)
    mfg_base = sum_base(st.session_state.mfg_df)
    log_base = sum_base(st.session_state.log_df)

    # Manufacturing Subtotal = Raw + Plant Operation
    ms_base = raw_base + mfg_base

    # Apply margin to manufacturing subtotal only
    wm_base = with_margin(ms_base, st.session_state.margin_pct)

    # Final totals (logistics added after margin)
    tec_base = (0 if np.isnan(wm_base) else float(wm_base)) + log_base

    # ---- Scenario application at REPORT LEVEL ONLY
    s = st.session_state.scenario_pct / 100.0
    def low_high(x):
        return (x * (1 - s), x, x * (1 + s)) if x is not None and not np.isnan(x) else (0.0, 0.0, 0.0)

    ms_low,  ms_base_v,  ms_high  = low_high(ms_base)
    wm_low,  wm_base_v,  wm_high  = low_high(wm_base)
    log_low, log_base_v, log_high = low_high(log_base)
    tec_low, tec_base_v, tec_high = low_high(tec_base)

    # ===== Summary Table =====
    summary_df = pd.DataFrame(
        {
            "Manufacturing Subtotal": [ms_low, ms_base_v, ms_high],
            "Subtotal with Margin":   [wm_low, wm_base_v, wm_high],
            "Logistics Subtotal":     [log_low, log_base_v, log_high],
            "TOTAL ESTIMATED COST":   [tec_low, tec_base_v, tec_high],
        },
        index=["Low","Base","High"]
    ).T

    summary_df = summary_df.applymap(lambda x: 0 if x is None or np.isnan(x) else float(x))

    st.subheader("Cost Summary")
    st.dataframe(
        summary_df.style.format("${:,.4f}"),
        use_container_width=True
    )
