import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Should Cost Calculation v12", layout="wide")

# ===== Helpers =====
def dollars(x):
    try:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return "—"
        return f"${float(x):,.4f}"
    except Exception:
        return "—"

def to_float(v):
    try:
        return float(v)
    except Exception:
        return np.nan

def suggested_per_lb(price_per_unit, cf_value):
    p = to_float(price_per_unit)
    c = to_float(cf_value)
    if np.isnan(p) or np.isnan(c):
        return np.nan
    return p * c

# ===== Session Init =====
if "meta" not in st.session_state:
    st.session_state.meta = {"product": "", "analysis_date": str(date.today())}

if "margin_pct" not in st.session_state:
    st.session_state.margin_pct = 25.0

if "scenario_pct" not in st.session_state:
    st.session_state.scenario_pct = 10.0

RAW_COLS = [
    "Category","Item","Price ($/unit)","CF Unit","CF Value (unit/lb)",
    "Suggested $/lb","Override $/lb","Source Tag","Source/Notes","Attachment",
    "Low $/lb","Base $/lb","High $/lb"
]

if "raw_df" not in st.session_state:
    st.session_state.raw_df = pd.DataFrame(columns=RAW_COLS)

MFG_COLS = ["Category","Item","Value ($/lb)","Source Tag","Source/Notes","Attachment","Low $/lb","Base $/lb","High $/lb"]
if "mfg_df" not in st.session_state:
    st.session_state.mfg_df = pd.DataFrame(columns=MFG_COLS)

LOG_COLS = ["Item","Value ($/lb)","Source Tag","Source/Notes","Attachment","Low $/lb","Base $/lb","High $/lb"]
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=LOG_COLS)

SOURCE_TAGS = ["Manual Quote", "ChemAnalyst", "FRED", "Company Filing", "Other"]
CF_UNIT_OPTIONS = ["$/lb", "$/kg", "$/ton", "$/tonne", "$/MMBtu", "$/GJ", "$/kWh", "$/gal", "$/L"]

# ===== Header =====
st.title("Should Cost Calculation v12")
c1, c2 = st.columns(2)
with c1:
    st.session_state.meta["product"] = st.text_input("Product", st.session_state.meta["product"])
with c2:
    st.session_state.meta["analysis_date"] = st.date_input(
        "Analysis Date", pd.to_datetime(st.session_state.meta["analysis_date"])
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
            sug = suggested_per_lb(raw_price, raw_cf_val)
            new_row = {
                "Category": raw_category, "Item": raw_item,
                "Price ($/unit)": raw_price, "CF Unit": raw_cf_unit, "CF Value (unit/lb)": raw_cf_val,
                "Suggested $/lb": None if np.isnan(sug) else float(sug),
                "Override $/lb": None,
                "Source Tag": raw_source_tag, "Source/Notes": raw_source_notes, "Attachment": attach.name if attach else "",
                "Low $/lb": None, "Base $/lb": None, "High $/lb": None
            }
            st.session_state.raw_df = pd.concat([st.session_state.raw_df, pd.DataFrame([new_row])], ignore_index=True)
    raw_edit = st.data_editor(st.session_state.raw_df, num_rows="dynamic", key="raw_editor", use_container_width=True)
    # Always update Suggested $/lb (in case edits happened)
    if not raw_edit.empty:
        raw_edit["Suggested $/lb"] = raw_edit.apply(
            lambda r: suggested_per_lb(r.get("Price ($/unit)"), r.get("CF Value (unit/lb)")), axis=1
        )
    # Always update Base $/lb: user uses override, else use suggested
    raw_edit["Base $/lb"] = raw_edit.apply(
        lambda r: to_float(r.get("Override $/lb"))
        if not pd.isna(r.get("Override $/lb")) and to_float(r.get("Override $/lb")) != 0.0
        else to_float(r.get("Suggested $/lb")), axis=1
    )
    st.session_state.raw_df = raw_edit

# ===== 2.0 Manufacturing (Utilities) =====
with st.expander("2.0 Manufacturing (includes Utilities)", expanded=True):
    with st.form("add_mfg_form", clear_on_submit=True):
        mc1, mc2 = st.columns([2,1])
        with mc1:
            mfg_item = st.text_input("Item ", key="mfg_item")
        with mc2:
            mfg_value = st.number_input("Value ($/lb)", min_value=0.0, value=0.0, step=0.0001, format="%.6f")
        md1, md2 = st.columns([1,2])
        with md1:
            mfg_source_tag = st.selectbox("Source Tag ", SOURCE_TAGS, index=0, key="mfg_source_tag")
        with md2:
            mfg_source_notes = st.text_input("Source/Notes ", key="mfg_source_notes", placeholder="e.g., plant calc, 2025 plan")
        attach = st.file_uploader("Attachment (optional)", type=["pdf","png","jpg"], key="mfg_attach")
        submitted_m = st.form_submit_button("Add row")
        if submitted_m:
            new_m = {
                "Category":"", "Item": mfg_item,
                "Value ($/lb)": mfg_value,
                "Source Tag": mfg_source_tag, "Source/Notes": mfg_source_notes, "Attachment": attach.name if attach else "",
                "Low $/lb": None, "Base $/lb": mfg_value, "High $/lb": None
            }
            st.session_state.mfg_df = pd.concat([st.session_state.mfg_df, pd.DataFrame([new_m])], ignore_index=True)
    mfg_edit = st.data_editor(st.session_state.mfg_df, num_rows="dynamic", key="mfg_editor", use_container_width=True)
    # Always update Base $/lb
    mfg_edit["Base $/lb"] = mfg_edit.apply(
        lambda r: to_float(r.get("Override $/lb"))
        if "Override $/lb" in r and not pd.isna(r.get("Override $/lb")) and to_float(r.get("Override $/lb")) != 0.0
        else to_float(r.get("Value ($/lb)")), axis=1
    ) if 'Override $/lb' in mfg_edit else mfg_edit["Value ($/lb)"]
    st.session_state.mfg_df = mfg_edit

# ===== 3.0 Logistics =====
with st.expander("3.0 Logistics", expanded=True):
    with st.form("add_log_form", clear_on_submit=True):
        lc1, lc2 = st.columns([2,1])
        with lc1:
            log_item = st.text_input("Item", key="log_item")
        with lc2:
            log_value = st.number_input("Value ($/lb)", min_value=0.0, value=0.0, step=0.0001, format="%.6f")
        ld1, ld2 = st.columns([1,2])
        with ld1:
            log_source_tag = st.selectbox("Source Tag", SOURCE_TAGS, index=0, key="log_source_tag")
        with ld2:
            log_source_notes = st.text_input("Source/Notes", key="log_source_notes", placeholder="e.g., lane calc, carrier quote")
        attach = st.file_uploader("Attachment (optional)", type=["pdf","png","jpg"], key="log_attach")
        submitted_l = st.form_submit_button("Add row")
        if submitted_l:
            new_l = {
                "Item": log_item, "Value ($/lb)": log_value,
                "Source Tag": log_source_tag, "Source/Notes": log_source_notes, "Attachment": attach.name if attach else "",
                "Low $/lb": None, "Base $/lb": log_value, "High $/lb": None
            }
            st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([new_l])], ignore_index=True)
    log_edit = st.data_editor(st.session_state.log_df, num_rows="dynamic", key="log_editor", use_container_width=True)
    # Always update Base $/lb
    log_edit["Base $/lb"] = log_edit["Value ($/lb)"]
    st.session_state.log_df = log_edit

# ===== 4.0 Margin & Totals =====
with st.expander("4.0 Margin & Totals", expanded=True):
    st.session_state.margin_pct = st.number_input("Gross Margin (%)", min_value=0.0, max_value=99.9, value=st.session_state.margin_pct, step=0.1, format="%.1f")
    st.session_state.scenario_pct = st.slider("Scenario ±%", 0, 100, int(st.session_state.scenario_pct), step=1)

    def apply_scenarios(df):
        # Always apply to 'Base $/lb' only
        for i in df.index:
            base = to_float(df.at[i,"Base $/lb"]) if "Base $/lb" in df.columns else np.nan
            if not np.isnan(base):
                df.at[i,"Low $/lb"] = base * (1 - st.session_state.scenario_pct/100)
                df.at[i,"High $/lb"] = base * (1 + st.session_state.scenario_pct/100)
        return df

    if st.button("Apply Scenarios"):
        st.session_state.raw_df = apply_scenarios(st.session_state.raw_df)
        st.session_state.mfg_df = apply_scenarios(st.session_state.mfg_df)
        st.session_state.log_df = apply_scenarios(st.session_state.log_df)

    def base_sum(df, col):
        return np.nansum([to_float(r[col]) for _, r in df.iterrows()])

    raw_low = base_sum(st.session_state.raw_df, "Low $/lb")
    raw_base = base_sum(st.session_state.raw_df, "Base $/lb")
    raw_high = base_sum(st.session_state.raw_df, "High $/lb")

    mfg_low = base_sum(st.session_state.mfg_df, "Low $/lb")
    mfg_base = base_sum(st.session_state.mfg_df, "Base $/lb")
    mfg_high = base_sum(st.session_state.mfg_df, "High $/lb")

    ms_low = raw_low + mfg_low
    ms_base = raw_base + mfg_base
    ms_high = raw_high + mfg_high

    c1, c2, c3 = st.columns(3)
    c1.metric("Manufacturing Subtotal (Low)", f"{dollars(ms_low)} / lb")
    c2.metric("Manufacturing Subtotal (Base)", f"{dollars(ms_base)} / lb")
    c3.metric("Manufacturing Subtotal (High)", f"{dollars(ms_high)} / lb")

    def with_margin(x, margin_pct):
        m = margin_pct / 100.0
        return (x / (1 - m)) if (1 - m) > 0 else np.nan

    wm_low = with_margin(ms_low, st.session_state.margin_pct)
    wm_base = with_margin(ms_base, st.session_state.margin_pct)
    wm_high = with_margin(ms_high, st.session_state.margin_pct)

    c1, c2, c3 = st.columns(3)
    c1.metric("Subtotal with Margin (Low)", f"{dollars(wm_low)} / lb")
    c2.metric("Subtotal with Margin (Base)", f"{dollars(wm_base)} / lb")
    c3.metric("Subtotal with Margin (High)", f"{dollars(wm_high)} / lb")

    log_low = base_sum(st.session_state.log_df, "Low $/lb")
    log_base = base_sum(st.session_state.log_df, "Base $/lb")
    log_high = base_sum(st.session_state.log_df, "High $/lb")

    c1, c2, c3 = st.columns(3)
    c1.metric("Logistics Subtotal (Low)", f"{dollars(log_low)} / lb")
    c2.metric("Logistics Subtotal (Base)", f"{dollars(log_base)} / lb")
    c3.metric("Logistics Subtotal (High)", f"{dollars(log_high)} / lb")

    tec_low = (0 if np.isnan(wm_low) else float(wm_low)) + log_low
    tec_base = (0 if np.isnan(wm_base) else float(wm_base)) + log_base
    tec_high = (0 if np.isnan(wm_high) else float(wm_high)) + log_high

    st.header("TOTAL ESTIMATED COST")
    c1, c2, c3 = st.columns(3)
    c1.metric("Low", f"{dollars(tec_low)} / lb")
    c2.metric("Base", f"{dollars(tec_base)} / lb")
    c3.metric("High", f"{dollars(tec_high)} / lb")
