import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Workflow Builder")

st.title("pyH2A Workflow Builder")

# -----------------------------
# Session state
# -----------------------------
if "new_user_columns" not in st.session_state:
    st.session_state.new_user_columns = []

if "tables" not in st.session_state:
    st.session_state.tables = [
        {
            "title": "Workflow",
            "rendered": True,
            "columns": [
                {"name": "Name", "type": "text"},
                {
                    "name": "Type",
                    "type": "dropdown",
                    "options": ["plugin", "module", "process"],
                },
                {"name": "Description", "type": "text"},
                {
                    "name": "Position",
                    "type": "dropdown",
                    "options": list(range(21)),
                },
            ],
            "rows": [
                {
                    "Name": "Hourly_Irradiation_Plugin",
                    "Type": "plugin",
                    "Description": "Plugin to calculate solar irradiation from typical meteorological year data",
                    "Position": 0,
                },
                {
                    "Name": "PEC_Plugin",
                    "Type": "plugin",
                    "Description": "Plugin to model photoelectrochemical water splitting",
                    "Position": 2,
                },
                {
                    "Name": "Solar_Concentrator_Plugin",
                    "Type": "plugin",
                    "Description": "Plugin to model solar concentration",
                    "Position": 2,
                },
                {
                    "Name": "Multiple_Modules_Plugin",
                    "Type": "plugin",
                    "Description": "Modelling of module plant modules, adjustment of labor requirement",
                    "Position": 3,
                },
            ],
        },
        {
            "title": "Construction",
            "rendered": True,
            "columns": [
                {"name": "Name", "type": "text", "disabled": True},
                {"name": "Full Name", "type": "text", "disabled": True},
                {"name": "Value", "type": "number"},
            ],
            "rows": [
                {
                    "Name": "capital perc 1st",
                    "Full Name": "% of Capital Spent in 1st Year of Construction",
                    "Value": 0.0,
                },
            ],
        },
         {
            "title": "Construction - 1",
            "rendered": True,
            "columns": [
                {"name": "Name", "type": "text", "disabled": True},
                {"name": "Full Name", "type": "text", "disabled": True},
                {"name": "Value", "type": "number"},
                {"name": "Path", "type": "text"},
            ],
            "rows": [
                {
                    "Name": "capital perc 1st",
                    "Full Name": "% of Capital Spent in 1st Year of Construction",
                    "Value": 0.0,
                    "Path": "",
                },
            ],
        },
    ]


# -----------------------------
# Helpers
# -----------------------------
def default_value(col):
    col_type = col["type"]

    if col_type == "number":
        return 0.0

    if col_type == "dropdown":
        options = col.get("options", [])
        return options[0] if options else ""

    return ""


def render_cell(table_idx, row_idx, col):
    col_name = col["name"]
    col_type = col["type"]
    disabled = col.get("disabled", False)

    key = f"cell_{table_idx}_{row_idx}_{col_name}"

    current_value = st.session_state.tables[table_idx]["rows"][row_idx].get(
        col_name,
        default_value(col),
    )

    if col_type == "number":
        value = st.number_input(
            col_name,
            value=float(current_value or 0),
            key=key,
            disabled=disabled,
            label_visibility="collapsed",
        )

    elif col_type == "dropdown":
        options = col.get("options", [])
        index = options.index(current_value) if current_value in options else 0

        value = st.selectbox(
            col_name,
            options=options,
            index=index,
            key=key,
            disabled=disabled,
            label_visibility="collapsed",
        )

    else:
        value = st.text_input(
            col_name,
            value=str(current_value or ""),
            key=key,
            disabled=disabled,
            label_visibility="collapsed",
        )

    st.session_state.tables[table_idx]["rows"][row_idx][col_name] = value


def table_to_markdown(tbl):
    df = pd.DataFrame(
        tbl["rows"],
        columns=[col["name"] for col in tbl["columns"]],
    )

    if df.empty:
        return "_No data yet._"

    return df.fillna("").to_markdown(index=False)


def inject_equal_click_js():
    components.html(
        """
        <script>
        const doc = window.parent.document;

        if (!window.parent.__equalClickInstalled) {
            window.parent.__equalClickInstalled = true;
            window.parent.__activePathInput = null;

            function cleanText(text) {
                return (text || "")
                    .replace("keyboard_arrow_down", "")
                    .replace("keyboard_arrow_right", "")
                    .replace("— rendered/template", "")
                    .replace("— user added", "")
                    .replace(/\s+/g, " ")
                    .trim();
            }

            function getTableName(el) {
                const details = el.closest("details");
                if (!details) return "";

                const summary = details.querySelector("summary");
                if (!summary) return "";

                return cleanText(summary.innerText);
            }

            function getColName(el) {
                return el.getAttribute("aria-label") || "";
            }

            function getRowName(el) {
                const row = el.closest('[data-testid="stHorizontalBlock"]');
                if (!row) return "";

                const inputs = row.querySelectorAll("input");

                for (const input of inputs) {
                    const label = input.getAttribute("aria-label") || "";

                    if (label.toLowerCase() === "name") {
                        return input.value || "";
                    }
                }

                return "";
            }

            function getFullPath(el) {
                const tableName = getTableName(el);
                const rowName = getRowName(el);
                const colName = getColName(el);

                return `(${tableName} > ${rowName} > ${colName}, )`;
            }

            function setNativeValue(input, value) {
                const nativeInputValueSetter =
                    Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype,
                        "value"
                    ).set;

                nativeInputValueSetter.call(input, value);

                input.dispatchEvent(new Event("input", { bubbles: true }));
                input.dispatchEvent(new Event("change", { bubbles: true }));
                input.dispatchEvent(new Event("blur", { bubbles: true }));
            }
            
            doc.addEventListener("input", function(e) {
                const el = e.target;

                if (el.tagName !== "INPUT") return;

                const label = el.getAttribute("aria-label") || "";

                if (label.toLowerCase() === "path" && el.value.trim() === "=") {
                    window.parent.__activePathInput = el;
                }
            });

            doc.addEventListener("change", function(e) {
                const el = e.target;

                if (el.tagName !== "INPUT") return;

                const label = el.getAttribute("aria-label") || "";

                if (label.toLowerCase() === "path" && el.value.trim() === "=") {
                    window.parent.__activePathInput = el;
                }
            });

            doc.addEventListener("focusin", function(e) {
                const el = e.target;

                if (el.tagName !== "INPUT") return;

                const label = el.getAttribute("aria-label") || "";

                if (label.toLowerCase() === "path" && el.value.trim() === "=") {
                    window.parent.__activePathInput = el;
                }
            });

            doc.addEventListener("mousedown", function(e) {
                const el = e.target;

                if (!window.parent.__activePathInput) return;
                if (el.tagName !== "INPUT") return;
                if (el === window.parent.__activePathInput) return;

                const sourceTableName = getFullPath(el);

                if (sourceTableName) {
                    setNativeValue(window.parent.__activePathInput, sourceTableName);
                    window.parent.__activePathInput = null;
                }
            });
        }
        </script>
        """,
        height=0,
    )


# -----------------------------
# Render tables
# -----------------------------
for table_idx, tbl in enumerate(st.session_state.tables):
    label = tbl["title"]

    if tbl.get("rendered"):
        label += " — rendered/template"
    else:
        label += " — user added"

    with st.expander(label, expanded=True):
        header_cols = st.columns(len(tbl["columns"]) + 1)

        for col_idx, col in enumerate(tbl["columns"]):
            header_cols[col_idx].markdown(f"**{col['name']}**")

        header_cols[-1].markdown("**Actions**")

        for row_idx, row in enumerate(tbl["rows"]):
            row_cols = st.columns(len(tbl["columns"]) + 1)

            for col_idx, col in enumerate(tbl["columns"]):
                with row_cols[col_idx]:
                    render_cell(table_idx, row_idx, col)

            with row_cols[-1]:
                if st.button("Delete row", key=f"delete_row_{table_idx}_{row_idx}"):
                    st.session_state.tables[table_idx]["rows"].pop(row_idx)
                    st.rerun()

        st.markdown("---")

        if st.button("Add row", key=f"add_row_{table_idx}"):
            new_row = {
                col["name"]: default_value(col)
                for col in tbl["columns"]
            }

            st.session_state.tables[table_idx]["rows"].append(new_row)
            st.rerun()

        with st.expander("Add column"):
            new_col_name = st.text_input(
                "Column name",
                key=f"new_col_name_{table_idx}",
            )

            new_col_type = st.selectbox(
                "Column type",
                ["text", "number", "dropdown"],
                key=f"new_col_type_{table_idx}",
            )

            dropdown_options = []

            if new_col_type == "dropdown":
                options_text = st.text_input(
                    "Dropdown options, comma-separated",
                    placeholder="Option 1, Option 2, Option 3",
                    key=f"new_dropdown_options_{table_idx}",
                )

                dropdown_options = [
                    option.strip()
                    for option in options_text.split(",")
                    if option.strip()
                ]

            if st.button("Create column", key=f"create_col_{table_idx}"):
                if new_col_name.strip():
                    col_name = new_col_name.strip()

                    new_col = {
                        "name": col_name,
                        "type": new_col_type,
                    }

                    if new_col_type == "dropdown":
                        new_col["options"] = dropdown_options or ["Option 1"]

                    st.session_state.tables[table_idx]["columns"].append(new_col)

                    for row in st.session_state.tables[table_idx]["rows"]:
                        row[col_name] = default_value(new_col)

                    st.rerun()

        if not tbl.get("rendered"):
            if st.button("Delete table", key=f"delete_table_{table_idx}"):
                st.session_state.tables.pop(table_idx)
                st.rerun()


# -----------------------------
# Add user table
# -----------------------------
st.divider()

with st.expander("Add additional user table"):
    table_title = st.text_input("Table name", key="new_table_title")

    st.markdown("#### Columns")

    col_name_input, col_type_input, col_options_input, col_btn = st.columns([2, 1.5, 3, 1])

    with col_name_input:
        new_user_col_name = st.text_input(
            "Column name",
            key="new_user_col_name",
        )

    with col_type_input:
        new_user_col_type = st.selectbox(
            "Column type",
            ["text", "number", "dropdown"],
            key="new_user_col_type",
        )

    with col_options_input:
        new_user_dropdown_options = ""

        if new_user_col_type == "dropdown":
            new_user_dropdown_options = st.text_input(
                "Dropdown options",
                placeholder="Option 1, Option 2, Option 3",
                key="new_user_dropdown_options",
            )

    with col_btn:
        st.write("")
        st.write("")

        if st.button("Add column"):
            col_name = new_user_col_name.strip()

            if col_name:
                new_col = {
                    "name": col_name,
                    "type": new_user_col_type,
                }

                if new_user_col_type == "dropdown":
                    options = [
                        option.strip()
                        for option in new_user_dropdown_options.split(",")
                        if option.strip()
                    ]
                    new_col["options"] = options or ["Option 1"]

                st.session_state.new_user_columns.append(new_col)
                st.rerun()

    if st.session_state.new_user_columns:
        st.markdown("**Selected columns:**")

        for idx, col in enumerate(st.session_state.new_user_columns):
            c1, c2, c3 = st.columns([2, 2, 1])

            c1.write(col["name"])
            c2.write(col["type"])

            if c3.button("Remove", key=f"remove_new_user_col_{idx}"):
                st.session_state.new_user_columns.pop(idx)
                st.rerun()

    if st.button("Create table"):
        title = table_title.strip() or f"User Table {len(st.session_state.tables) + 1}"

        if not st.session_state.new_user_columns:
            st.warning("Please add at least one column.")
        else:
            st.session_state.tables.append(
                {
                    "title": title,
                    "rendered": False,
                    "columns": st.session_state.new_user_columns.copy(),
                    "rows": [],
                }
            )

            st.session_state.new_user_columns = []
            st.rerun()


# -----------------------------
# Markdown export
# -----------------------------
st.divider()
st.markdown("### Markdown Preview")

md_output = ""

for tbl in st.session_state.tables:
    md_output += f"## {tbl['title']}\n\n"
    md_output += table_to_markdown(tbl)
    md_output += "\n\n"

st.code(md_output, language="markdown")

# -----------------------------
# Custom JS
# -----------------------------
inject_equal_click_js()