import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Workflow Builder")

st.title("pyH2A Workflow Builder")

WORKFLOW_COLUMNS = ["Name", "Type", "Description", "Position"]

if "workflow_table" not in st.session_state:
    st.session_state.workflow_table = pd.DataFrame(columns=WORKFLOW_COLUMNS)

if "display_tables" not in st.session_state:
    st.session_state.display_tables = []

if "validation_errors" not in st.session_state:
    st.session_state.validation_errors = {}

# -----------------------------
# BOUNDS CONFIG per table index
# e.g. {0: {"min": 1, "max": 1000}}
# -----------------------------
if "table_bounds" not in st.session_state:
    st.session_state.table_bounds = {}

def is_valid(v):
    try:
        return not pd.isna(v) and v != ""
    except (TypeError, ValueError):
        return v is not None and v != ""

def is_number(v):
    try:
        float(v)
        return True
    except (ValueError, TypeError):
        return False

def validate_bounds(df, bounds, table_key):
    errors = []
    if not bounds:
        return errors
    mn = bounds.get("min")
    mx = bounds.get("max")
    if "Value" not in df.columns:
        return errors
    for idx, row in df.iterrows():
        val = row.get("Value", None)
        if val is None or val == "" or not is_number(val):
            continue
        num = float(val)
        if mn is not None and num < mn:
            errors.append(f"Row {idx + 1}: Value {num} is below minimum ({mn})")
        if mx is not None and num > mx:
            errors.append(f"Row {idx + 1}: Value {num} exceeds maximum ({mx})")
    return errors

def apply_delta(df, state, cols):
    for idx, changes in state.get("edited_rows", {}).items():
        idx = int(idx)
        if idx < len(df):
            for col, val in changes.items():
                df.at[idx, col] = val
    for row in state.get("added_rows", []):
        if any(is_valid(v) for v in row.values()):
            new_row = {col: row.get(col, None) for col in cols}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    deleted = state.get("deleted_rows", [])
    if deleted:
        df = df.drop(index=[int(i) for i in deleted]).reset_index(drop=True)
    return df

def save_workflow():
    state = st.session_state.workflow_editor
    df = st.session_state.workflow_table.copy()
    st.session_state.workflow_table = apply_delta(df, state, WORKFLOW_COLUMNS)

def make_display_callback(i):
    def cb():
        key = f"display_editor_{i}"
        state = st.session_state[key]
        df = st.session_state.display_tables[i]["df"].copy()
        cols = st.session_state.display_tables[i]["columns"]
        updated_df = apply_delta(df, state, cols)
        st.session_state.display_tables[i]["df"] = updated_df

        # Validate bounds if table has them
        bounds = st.session_state.table_bounds.get(i, {})
        errors = validate_bounds(updated_df, bounds, i)
        st.session_state.validation_errors[i] = errors
    return cb

# ================================
# SECTION 1 — Workflow
# ================================
st.markdown("### Workflow")

st.data_editor(
    st.session_state.workflow_table,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="workflow_editor",
    on_change=save_workflow,
    column_config={
        "Name": st.column_config.TextColumn("Name", help="Step name"),
        "Type": st.column_config.SelectboxColumn("Type", options=["plugin", "module", "process"]),
        "Description": st.column_config.TextColumn("Description"),
        "Position": st.column_config.SelectboxColumn("Position", options=list(range(1, 21)))
    }
)

st.divider()

# ================================
# SECTION 2 — Display Tables
# ================================
with st.expander(" Add New Table", expanded=len(st.session_state.display_tables) == 0):
    new_title_input = st.text_input("Table Title", placeholder="e.g. Technical Operating Parameters", key="new_table_title")
    new_cols_input = st.text_input("Columns (comma-separated)", placeholder="e.g. Name, Value, Path, Full Name", key="new_table_cols")

    # Bounds toggle inside expander
    enable_bounds = st.checkbox("Enable numeric bounds on Value column", key="new_table_bounds_enable")
    b_min, b_max = None, None
    if enable_bounds:
        bc1, bc2 = st.columns(2)
        with bc1:
            b_min = st.number_input("Min value", value=1.0, key="new_bounds_min")
        with bc2:
            b_max = st.number_input("Max value", value=1000.0, key="new_bounds_max")

    if st.button("Create Table"):
        raw_cols = [c.strip() for c in new_cols_input.split(",") if c.strip()]
        title = new_title_input.strip() or f"Table {len(st.session_state.display_tables) + 1}"
        if raw_cols:
            idx = len(st.session_state.display_tables)
            st.session_state.display_tables.append({
                "title": title,
                "columns": raw_cols,
                "df": pd.DataFrame(columns=raw_cols)
            })
            if enable_bounds and b_min is not None and b_max is not None:
                st.session_state.table_bounds[idx] = {"min": b_min, "max": b_max}
            st.rerun()
        else:
            st.warning("Please define at least one column.")

# --- Render each table ---
for i, tbl in enumerate(st.session_state.display_tables):
    st.markdown(f"###  {tbl['title']}")

    # Bounds config inline per table
    bounds = st.session_state.table_bounds.get(i, {})
    with st.expander(f" Bounds Settings — {tbl['title']}", expanded=False):
        has_bounds = st.checkbox(
            "Enable numeric bounds on Value column",
            value=bool(bounds),
            key=f"bounds_enable_{i}"
        )
        if has_bounds:
            bc1, bc2 = st.columns(2)
            with bc1:
                cur_min = bounds.get("min", 1.0)
                new_min = st.number_input("Min", value=float(cur_min), key=f"bounds_min_{i}")
            with bc2:
                cur_max = bounds.get("max", 1000.0)
                new_max = st.number_input("Max", value=float(cur_max), key=f"bounds_max_{i}")
            st.session_state.table_bounds[i] = {"min": new_min, "max": new_max}
        else:
            if i in st.session_state.table_bounds:
                del st.session_state.table_bounds[i]
            if i in st.session_state.validation_errors:
                del st.session_state.validation_errors[i]

    # Column + delete controls
    col_add_input, col_add_btn, _, col_del_btn = st.columns([2.5, 1, 2, 1])
    with col_add_input:
        new_col_name = st.text_input(
            "New column name",
            placeholder="Column name",
            key=f"new_col_{i}",
            label_visibility="collapsed"
        )
    with col_add_btn:
        if st.button(" Column", key=f"add_col_{i}"):
            col_name = new_col_name.strip()
            if col_name and col_name not in tbl["columns"]:
                st.session_state.display_tables[i]["columns"].append(col_name)
                st.session_state.display_tables[i]["df"][col_name] = None
                st.rerun()
    with col_del_btn:
        if st.button("🗑 Delete Table", key=f"del_table_{i}"):
            st.session_state.display_tables.pop(i)
            st.session_state.table_bounds.pop(i, None)
            st.session_state.validation_errors.pop(i, None)
            st.rerun()

    # Show validation errors
    errors = st.session_state.validation_errors.get(i, [])
    if errors:
        for err in errors:
            st.error(f" {err}")

    # Show active bounds info
    active_bounds = st.session_state.table_bounds.get(i, {})
    if active_bounds:
        st.caption(f"Numeric bounds active on **Value** column: min = `{active_bounds['min']}`, max = `{active_bounds['max']}`")

    st.data_editor(
        tbl["df"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"display_editor_{i}",
        on_change=make_display_callback(i),
        column_config={col: st.column_config.TextColumn(col) for col in tbl["columns"]}
    )

    st.markdown("---")

st.divider()

# ================================
# SECTION 3 — Live Markdown Export
# ================================
st.markdown("### All Tables — Markdown Preview")

md_output = ""

md_output += "## Workflow Steps\n\n"
if not st.session_state.workflow_table.empty:
    md_output += st.session_state.workflow_table.fillna("").to_markdown(index=False)
else:
    md_output += "_No data yet._"
md_output += "\n\n"

for tbl in st.session_state.display_tables:
    md_output += f"## {tbl['title']}\n\n"
    if not tbl["df"].empty:
        md_output += tbl["df"].fillna("").to_markdown(index=False)
    else:
        md_output += "_No data yet._"
    md_output += "\n\n"

st.code(md_output, language="markdown")