
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Should Cost Calculation v9", layout="wide")

# -------- Helpers --------
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
    """Suggested $/lb = Price ($ per CF Unit) × CF (CF Unit per lb product)."""
    p = to_float(price_per_unit)
    c = to_float(cf_value)
    if np.isnan(p) or np.isnan(c):
        return np.nan
    return p * c

# -------- Session Init --------
if "meta" not in st.session_state:
    st.session_state.meta = {"product": "", "analysis_date": str(date.today())}

RAW_COLS = [
    "Category","Item","Price ($/unit)","CF Unit","CF Value (unit/lb)",
    "Suggested $/lb","Override $/lb",
    "Source Tag","Source/Notes",
    "Low $/lb","Base $/lb","High $/lb",
    "Delete?"
]
if "raw_df" not in st.session_state:
    st.session_state.raw_df = pd.DataFrame(columns=RAW_COLS)

DIRECT_COLS = ["Item","Value ($/lb)","Source Tag","Source/Notes","Low $/lb","Base $/lb","High $/lb","Delete?"]
if "direct_df" not in st.session_state:
    st.session_state.direct_df = pd.DataFrame([
        {"Item":"Conversion costs","Value ($/lb)":None,"Source Tag":"Manual Quote","Source/Notes":"","Low $/lb":None,"Base $/lb":None,"High $/lb":None,"Delete?":False},
        {"Item":"Maintenance & Ops","Value ($/lb)":None,"Source Tag":"Manual Quote","Source/Notes":"","Low $/lb":None,"Base $/lb":None,"High $/lb":None,"Delete?":False},
        {"Item":"Overhead/Dep/Insurance","Value ($/lb)":None,"Source Tag":"Manual Quote","Source/Notes":"","Low $/lb":None,"Base $/lb":None,"High $/lb":None,"Delete?":False},
    ], columns=DIRECT_COLS)

if "margin_pct" not in st.session_state:
    st.session_state.margin_pct = 25.0

if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame([
        {"Item":"Transportation","Value ($/lb)":None,"Source Tag":"Manual Quote","Source/Notes":"","Low $/lb":None,"Base $/lb":None,"High $/lb":None,"Delete?":False},
        {"Item":"Fuel Surcharge","Value ($/lb)":None,"Source Tag":"Manual Quote","Source/Notes":"","Low $/lb":None,"Base $/lb":None,"High $/lb":None,"Delete?":False},
        {"Item":"Packaging","Value ($/lb)":None,"Source Tag":"Manual Quote","Source/Notes":"","Low $/lb":None,"Base $/lb":None,"High $/lb":None,"Delete?":False},
        {"Item":"Handling & Storage","Value ($/lb)":None,"Source Tag":"Manual Quote","Source/Notes":"","Low $/lb":None,"Base $/lb":None,"High $/lb":None,"Delete?":False},
    ], columns=DIRECT_COLS)

# -------- Header --------
st.title("Should Cost Calculation — v9")

c1, c2, c3 = st.columns([2,2,1])
with c1:
    st.session_state.meta["product"] = st.text_input("Product", st.session_state.meta["product"])
with c2:
    st.session_state.meta["analysis_date"] = st.date_input("Analysis Date", pd.to_datetime(st.session_state.meta["analysis_date"])).strftime("%Y-%m-%d")
with c3:
    if st.button("Reset Tables"):
        st.session_state.raw_df = pd.DataFrame(columns=RAW_COLS)
        st.session_state.direct_df = pd.DataFrame(columns=DIRECT_COLS)
        st.session_state.log_df = pd.DataFrame(columns=DIRECT_COLS)
        st.experimental_rerun()

st.divider()

# -------- Raw Materials & Utilities --------
st.subheader("Raw Materials & Utilities")
st.caption("Enter **Price ($ per CF Unit)** and **CF (CF Unit per lb of product)**. Suggested = Price × CF. Base uses: Base $/lb → Override → Suggested.")

rc1, rc2, rc3 = st.columns([1,1,3])
with rc1:
    if st.button("➕ Add raw row"):
        new_row = {
            "Category":"Primary","Item":"",
            "Price ($/unit)":None,"CF Unit":"lb","CF Value (unit/lb)":None,
            "Suggested $/lb":None,"Override $/lb":None,
            "Source Tag":"Manual Quote","Source/Notes":"",
            "Low $/lb":None,"Base $/lb":None,"High $/lb":None,
            "Delete?":False
        }
        st.session_state.raw_df = pd.concat([st.session_state.raw_df, pd.DataFrame([new_row])], ignore_index=True)
with rc2:
    if st.button("🗑️ Delete checked"):
        df = st.session_state.raw_df
        st.session_state.raw_df = df[~df["Delete?"].fillna(False)].reset_index(drop=True)

raw_editor = st.data_editor(
    st.session_state.raw_df,
    num_rows="dynamic",
    use_container_width=True,
    key="raw_editor"
)
raw = raw_editor.copy()

# compute Suggested
if not raw.empty:
    raw["Suggested $/lb"] = raw.apply(lambda r: suggested_per_lb(r.get("Price ($/unit)"), r.get("CF Value (unit/lb)")), axis=1)

st.session_state.raw_df = raw

st.divider()

# -------- Manufacturing Operations (Direct) --------
st.subheader("Manufacturing Operations (Direct items, $/lb)")
dc1, dc2 = st.columns([1,1])
with dc1:
    if st.button("➕ Add direct row"):
        newd = {"Item":"", "Value ($/lb)":None, "Source Tag":"Manual Quote", "Source/Notes":"", "Low $/lb":None, "Base $/lb":None, "High $/lb":None, "Delete?":False}
        st.session_state.direct_df = pd.concat([st.session_state.direct_df, pd.DataFrame([newd])], ignore_index=True)
with dc2:
    if st.button("🗑️ Delete checked direct"):
        df = st.session_state.direct_df
        st.session_state.direct_df = df[~df["Delete?"].fillna(False)].reset_index(drop=True)

direct_editor = st.data_editor(
    st.session_state.direct_df,
    num_rows="dynamic",
    use_container_width=True,
    key="direct_editor"
)
st.session_state.direct_df = direct_editor

st.divider()

# -------- Business Components (Margin) --------
st.subheader("Business Components")
st.session_state.margin_pct = st.number_input("Gross Margin (%)", min_value=0.0, max_value=99.9, value=st.session_state.margin_pct, step=0.1, format="%.1f")

st.divider()

# -------- Logistics & Distribution --------
st.subheader("Logistics & Distribution (Direct items, $/lb)")
lc1, lc2 = st.columns([1,1])
with lc1:
    if st.button("➕ Add logistics row"):
        newl = {"Item":"", "Value ($/lb)":None, "Source Tag":"Manual Quote", "Source/Notes":"", "Low $/lb":None, "Base $/lb":None, "High $/lb":None, "Delete?":False}
        st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([newl])], ignore_index=True)
with lc2:
    if st.button("🗑️ Delete checked logistics"):
        df = st.session_state.log_df
        st.session_state.log_df = df[~df["Delete?"].fillna(False)].reset_index(drop=True)

log_editor = st.data_editor(
    st.session_state.log_df,
    num_rows="dynamic",
    use_container_width=True,
    key="log_editor"
)
st.session_state.log_df = log_editor

st.divider()

# -------- Totals (Low / Base / High) --------
def val_or(series, default=0.0):
    v = to_float(series)
    return default if np.isnan(v) else v

def row_base_raw(row):
    # Base $/lb if set -> Override -> Suggested -> 0
    b = to_float(row.get("Base $/lb"))
    if not np.isnan(b): return b
    o = to_float(row.get("Override $/lb"))
    if not np.isnan(o): return o
    s = to_float(row.get("Suggested $/lb"))
    if not np.isnan(s): return s
    return 0.0

# RAW totals
raw_low = raw_base = raw_high = 0.0
for _, r in st.session_state.raw_df.iterrows():
    base_eff = row_base_raw(r)
    raw_base += base_eff
    low = to_float(r.get("Low $/lb"));  high = to_float(r.get("High $/lb"))
    raw_low  += base_eff if np.isnan(low)  else low
    raw_high += base_eff if np.isnan(high) else high

# DIRECT totals
def row_base_direct(r):
    b = to_float(r.get("Base $/lb"))
    v = to_float(r.get("Value ($/lb)"))
    if not np.isnan(b): return b
    if not np.isnan(v): return v
    return 0.0

direct_low = direct_base = direct_high = 0.0
for _, r in st.session_state.direct_df.iterrows():
    b = row_base_direct(r)
    direct_base += b
    l = to_float(r.get("Low $/lb")); h = to_float(r.get("High $/lb"))
    direct_low  += b if np.isnan(l) else l
    direct_high += b if np.isnan(h) else h

# Manufacturing Subtotal & TMC
mfg_low  = raw_low  + direct_low
mfg_base = raw_base + direct_base
mfg_high = raw_high + direct_high

c1, c2, c3 = st.columns(3)
c1.metric("Manufacturing Subtotal (Low)",  f"{dollars(mfg_low)} / lb")
c2.metric("Manufacturing Subtotal (Base)", f"{dollars(mfg_base)} / lb")
c3.metric("Manufacturing Subtotal (High)", f"{dollars(mfg_high)} / lb")

tmc_low, tmc_base, tmc_high = mfg_low, mfg_base, mfg_high

# Apply Margin
def with_margin(x, margin_pct):
    m = margin_pct / 100.0
    return (x / (1 - m)) if (1 - m) > 0 else np.nan

wm_low  = with_margin(tmc_low,  st.session_state.margin_pct)
wm_base = with_margin(tmc_base, st.session_state.margin_pct)
wm_high = with_margin(tmc_high, st.session_state.margin_pct)

c1, c2, c3 = st.columns(3)
c1.metric("Subtotal with Margin (Low)",  f"{dollars(wm_low)} / lb")
c2.metric("Subtotal with Margin (Base)", f"{dollars(wm_base)} / lb")
c3.metric("Subtotal with Margin (High)", f"{dollars(wm_high)} / lb")

# LOGISTICS totals
log_low = log_base = log_high = 0.0
for _, r in st.session_state.log_df.iterrows():
    b = row_base_direct(r)  # same structure
    log_base += b
    l = to_float(r.get("Low $/lb")); h = to_float(r.get("High $/lb"))
    log_low  += b if np.isnan(l) else l
    log_high += b if np.isnan(h) else h

c1, c2, c3 = st.columns(3)
c1.metric("Logistics Subtotal (Low)",  f"{dollars(log_low)} / lb")
c2.metric("Logistics Subtotal (Base)", f"{dollars(log_base)} / lb")
c3.metric("Logistics Subtotal (High)", f"{dollars(log_high)} / lb")

# TOTAL ESTIMATED COST
tec_low  = (0 if np.isnan(wm_low)  else float(wm_low))  + log_low
tec_base = (0 if np.isnan(wm_base) else float(wm_base)) + log_base
tec_high = (0 if np.isnan(wm_high) else float(wm_high)) + log_high

st.header("TOTAL ESTIMATED COST")
c1, c2, c3 = st.columns(3)
c1.metric("Low",  f"{dollars(tec_low)} / lb")
c2.metric("Base", f"{dollars(tec_base)} / lb")
c3.metric("High", f"{dollars(tec_high)} / lb")
st.caption(f"Per short ton (2,000 lb): Low {dollars(tec_low*2000)}, Base {dollars(tec_base*2000)}, High {dollars(tec_high*2000)}.")

st.divider()
st.caption("Per-line Source Tag & Notes for auditability. Low/Base/High optional. Suggested = Price × CF; Base uses Base→Override→Suggested. No external APIs in v9.")
