import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Should Cost Calculation v12 (Table Totals)", layout="wide")

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

# ===== Session Init =====
if "meta" not in st.session_state:
    st.session_state.meta = {"product": "", "analysis_date": str(date.today())}

if "margin_pct" not in st.session_state:
    st.session_state.margin_pct = 25.0

if "scenario_pct" not in st.session_state:
    st.session_state.scenario_pct = 10.0

RAW_COLS = [
    "Category","Item","Price ($/unit)","CF Unit","CF Value (unit/lb)",
    "Source Tag","Source/Notes","Attachment",
    "Low $/lb","Base $/lb","High $/lb"
]
if "raw_df" not in st.session_state:
    st.session_state.raw_df = pd.DataFrame(columns=RAW_COLS)

# Plant Operation (formerly Manufacturing incl. Utilities)
MFG_COLS = ["Category","Item","Value ($/lb)","Source Tag","Source/Notes","Attachment","Low $/lb","Base $/lb","High $/lb"]
if "mfg_df" not in st.session_state:
    st.session_state.mfg_df = pd.DataFrame(columns=MFG_COLS)

# Logistics (now includes Category)
LOG_COLS = ["Category","Item","Value ($/lb)","Source Tag","Source/Notes","Attachment","Low $/lb","Base $/lb","High $/lb"]
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=LOG_COLS)

SOURCE_TAGS = ["Manual Quote", "ChemAnalyst", "FRED", "Company Filing", "Other"]
CF_UNIT_OPTIONS = ["$/lb", "$/kg", "$/ton", "$/tonne", "$/MMBtu", "$/GJ", "$/kWh", "$/gal", "$/L"]

# ===== Header =====
st.title("Should Cost Calculation")
c1, c2 = st.columns(2)
with c1:
    st.session_state.meta["product"] = st.text_input("Product", st.session_state.meta["product"])
with c2:
    st.session_state.meta["analysis_date"] = st.date_input("Analysis Date", pd.to_datetime(st.session_state.meta["analysis_date"])).strftime("%Y-%m-%d")

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
            new_row = {
                "Category": raw_category, "Item": raw_item,
                "Price ($/unit)": raw_price, "CF Unit": raw_cf_unit, "CF Value (unit/lb)": raw_cf_val,
                "Source Tag": raw_source_tag, "Source/Notes": raw_source_notes, "Attachment": attach.name if attach else "",
                "Low $/lb": None, "Base $/lb": None, "High $/lb": None
            }
            st.session_state.raw_df = pd.concat([st.session_state.raw_df, pd.DataFrame([new_row])], ignore_index=True)
    raw_edit = st.data_editor(st.session_state.raw_df, num_rows="dynamic", key="raw_editor", use_container_width=True)
    st.session_state.raw_df = raw_edit

# ===== 2.0 Plant Operation =====
with st.expander("2.0 Plant Operation", expanded=True):
    with st.form("add_mfg_form", clear_on_submit=True):
        mc0, mc1, mc2 = st.columns([1,2,1])
        with mc0:
            mfg_category = st.selectbox("Category", ["Utilities", "Manufacturing (process, labor, conversion)"], index=0)
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
                "Category": mfg_category, "Item": mfg_item,
                "Value ($/lb)": mfg_value,
                "Source Tag": mfg_source_tag, "Source/Notes": mfg_source_notes, "Attachment": attach.name if attach else "",
                "Low $/lb": None, "Base $/lb": None, "High $/lb": None
            }
            st.session_state.mfg_df = pd.concat([st.session_state.mfg_df, pd.DataFrame([new_m])], ignore_index=True)
    mfg_edit = st.data_editor(st.session_state.mfg_df, num_rows="dynamic", key="mfg_editor", use_container_width=True)
    st.session_state.mfg_df = mfg_edit

# ===== 3.0 Logistics =====
with st.expander("3.0 Logistics", expanded=True):
    with st.form("add_log_form", clear_on_submit=True):
        lc0, lc1, lc2 = st.columns([1,2,1])
        with lc0:
            log_category = st.selectbox("Category", ["Transportation", "Fuel Surcharge", "Handling & Storage"], index=0)
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
                "Category": log_category,
                "Item": log_item, "Value ($/lb)": log_value,
                "Source Tag": log_source_tag, "Source/Notes": log_source_notes, "Attachment": attach.name if attach else "",
                "Low $/lb": None, "Base $/lb": None, "High $/lb": None
            }
            st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([new_l])], ignore_index=True)
    log_edit = st.data_editor(st.session_state.log_df, num_rows="dynamic", key="log_editor", use_container_width=True)
    st.session_state.log_df = log_edit

# ===== 4.0 Margin & Totals =====
with st.expander("4.0 Margin & Totals", expanded=True):
    st.session_state.margin_pct = st.number_input("Gross Margin (%)", min_value=0.0, max_value=99.9, value=st.session_state.margin_pct, step=0.1, format="%.1f")
    st.session_state.scenario_pct = st.slider("Scenario ±%", 0, 100, int(st.session_state.scenario_pct), step=1)

    # Apply scenarios to Base $/lb only
    if st.button("Apply Scenarios"):
        def apply_scenarios_base(df):
            for i in df.index:
                base = to_float(df.at[i, "Base $/lb"]) if "Base $/lb" in df.columns else np.nan
                if not np.isnan(base):
                    df.at[i, "Low $/lb"]  = base * (1 - st.session_state.scenario_pct/100)
                    df.at[i, "High $/lb"] = base * (1 + st.session_state.scenario_pct/100)
            return df

        st.session_state.raw_df = apply_scenarios_base(st.session_state.raw_df)
        st.session_state.mfg_df = apply_scenarios_base(st.session_state.mfg_df)
        st.session_state.log_df = apply_scenarios_base(st.session_state.log_df)

    # ---- Compute totals
    def row_base_raw(row):
        b = to_float(row.get("Base $/lb"))
        return b if not np.isnan(b) else 0.0

    def row_base_direct(r):
        b = to_float(r.get("Base $/lb"))
        v = to_float(r.get("Value ($/lb)"))
        if not np.isnan(b): return b
        if not np.isnan(v): return v
        return 0.0

    # Raw totals
    raw_low = raw_base = raw_high = 0.0
    for _, r in st.session_state.raw_df.iterrows():
        b = row_base_raw(r)
        raw_base += b
        l = to_float(r.get("Low $/lb")); h = to_float(r.get("High $/lb"))
        raw_low  += b if np.isnan(l) else l
        raw_high += b if np.isnan(h) else h

    # Plant Operation totals
    mfg_low = mfg_base = mfg_high = 0.0
    for _, r in st.session_state.mfg_df.iterrows():
        b = row_base_direct(r)
        mfg_base += b
        l = to_float(r.get("Low $/lb")); h = to_float(r.get("High $/lb"))
        mfg_low  += b if np.isnan(l) else l
        mfg_high += b if np.isnan(h) else h

    # Manufacturing Subtotal = Raw + Plant Operation
    ms_low  = raw_low  + mfg_low
    ms_base = raw_base + mfg_base
    ms_high = raw_high + mfg_high

    def with_margin(x, margin_pct):
        m = margin_pct / 100.0
        return (x / (1 - m)) if (1 - m) > 0 else np.nan

    # Apply margin to manufacturing subtotal only
    wm_low  = with_margin(ms_low,  st.session_state.margin_pct)
    wm_base = with_margin(ms_base, st.session_state.margin_pct)
    wm_high = with_margin(ms_high, st.session_state.margin_pct)

    # Logistics totals
    log_low = log_base = log_high = 0.0
    for _, r in st.session_state.log_df.iterrows():
        b = row_base_direct(r)
        log_base += b
        l = to_float(r.get("Low $/lb")); h = to_float(r.get("High $/lb"))
        log_low  += b if np.isnan(l) else l
        log_high += b if np.isnan(h) else h

    # Final totals (logistics added after margin)
    tec_low  = (0 if np.isnan(wm_low)  else float(wm_low))  + log_low
    tec_base = (0 if np.isnan(wm_base) else float(wm_base)) + log_base
    tec_high = (0 if np.isnan(wm_high) else float(wm_high)) + log_high

    # ===== Summary Table =====
    summary_df = pd.DataFrame(
        {
            "Manufacturing Subtotal": [ms_low, ms_base, ms_high],
            "Subtotal with Margin":  [wm_low, wm_base, wm_high],
            "Logistics Subtotal":    [log_low, log_base, log_high],
            "TOTAL ESTIMATED COST":  [tec_low, tec_base, tec_high],
        },
        index=["Low","Base","High"]
    ).T

    summary_df = summary_df.applymap(lambda x: 0 if x is None or np.isnan(x) else float(x))

    st.subheader("Cost Summary")
    st.dataframe(
        summary_df.style.format("${:,.4f}"),
        use_container_width=True
    )
