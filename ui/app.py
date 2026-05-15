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

def is_valid(v):
    try:
        return not pd.isna(v) and v != ""
    except (TypeError, ValueError):
        return v is not None and v != ""

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
        st.session_state.display_tables[i]["df"] = apply_delta(df, state, cols)
    return cb

st.markdown('<div class="table-title">Workflow</div>', unsafe_allow_html=True)

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


with st.expander(" Add New Table", expanded=len(st.session_state.display_tables) == 0):
    new_title_input = st.text_input("Table Title", placeholder="e.g. Display Parameters", key="new_table_title")
    new_cols_input = st.text_input("Columns (comma-separated)", placeholder="e.g. Name, Value, Unit", key="new_table_cols")
    if st.button("Create Table"):
        raw_cols = [c.strip() for c in new_cols_input.split(",") if c.strip()]
        title = new_title_input.strip() or f"Table {len(st.session_state.display_tables) + 1}"
        if raw_cols:
            st.session_state.display_tables.append({
                "title": title,
                "columns": raw_cols,
                "df": pd.DataFrame(columns=raw_cols)
            })
            st.rerun()
        else:
            st.warning("Please define at least one column.")

for i, tbl in enumerate(st.session_state.display_tables):
    st.markdown(f'<div class="table-title"> {tbl["title"]}</div>', unsafe_allow_html=True)

    col_add_input, col_add_btn, _, col_del_btn = st.columns([2.5, 1, 2, 1])
    with col_add_input:
        new_col_name = st.text_input(
            "New column name",
            placeholder="Column name",
            key=f"new_col_{i}",
            label_visibility="collapsed"
        )
    with col_add_btn:
        if st.button("＋ Column", key=f"add_col_{i}"):
            col_name = new_col_name.strip()
            if col_name and col_name not in tbl["columns"]:
                st.session_state.display_tables[i]["columns"].append(col_name)
                st.session_state.display_tables[i]["df"][col_name] = None
                st.rerun()
    with col_del_btn:
        if st.button("🗑 Delete Table", key=f"del_table_{i}"):
            st.session_state.display_tables.pop(i)
            st.rerun()

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

st.markdown('<div class="section-badge">03 — Live Data Export</div>', unsafe_allow_html=True)
st.markdown('<div class="table-title">All Tables — Markdown Preview</div>', unsafe_allow_html=True)

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