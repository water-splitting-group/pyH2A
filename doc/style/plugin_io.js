const openMultiselects = [];

function createMultiselect(root, { allLabel, noneLabel, onChange }) {
    const button = root.querySelector(".io-multiselect-button");
    const label = root.querySelector(".io-multiselect-label");
    const panel = root.querySelector(".io-multiselect-panel");
    const optionsContainer = root.querySelector(".io-multiselect-options");
    const selectAllButton = root.querySelector(".io-multiselect-select-all");
    const clearButton = root.querySelector(".io-multiselect-clear");

    let values = [];
    const selected = new Set();

    function updateLabel() {
        if (selected.size === 0) {
            label.textContent = noneLabel;
        } else if (selected.size === values.length) {
            label.textContent = allLabel;
        } else if (selected.size === 1) {
            label.textContent = [...selected][0];
        } else {
            label.textContent = `${selected.size} selected`;
        }
    }

    function notifyChange() {
        updateLabel();
        onChange(new Set(selected));
    }

    function setAllChecked(isChecked) {
        optionsContainer
            .querySelectorAll("input[type=checkbox]")
            .forEach(checkbox => {
                checkbox.checked = isChecked;
            });

        selected.clear();

        if (isChecked) {
            values.forEach(value => selected.add(value));
        }

        notifyChange();
    }

    function setOptions(newValues) {
        values = [...newValues];
        selected.clear();
        values.forEach(value => selected.add(value));

        optionsContainer.innerHTML = "";

        values.forEach(value => {
            const optionLabel = document.createElement("label");
            optionLabel.className = "io-multiselect-option";

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = true;
            checkbox.value = value;

            checkbox.addEventListener("change", () => {
                if (checkbox.checked) {
                    selected.add(value);
                } else {
                    selected.delete(value);
                }
                notifyChange();
            });

            optionLabel.append(checkbox, document.createTextNode(value));
            optionsContainer.appendChild(optionLabel);
        });

        updateLabel();
    }

    function open() {
        panel.hidden = false;
        button.setAttribute("aria-expanded", "true");
    }

    function close() {
        panel.hidden = true;
        button.setAttribute("aria-expanded", "false");
    }

    button.addEventListener("click", () => {
        if (panel.hidden) {
            open();
        } else {
            close();
        }
    });

    selectAllButton.addEventListener("click", () => setAllChecked(true));
    clearButton.addEventListener("click", () => setAllChecked(false));

    openMultiselects.push({ root, close });

    return {
        setOptions,
        getSelected: () => new Set(selected),
    };
}

document.addEventListener("click", event => {
    openMultiselects.forEach(({ root, close }) => {
        if (!root.contains(event.target)) {
            close();
        }
    });
});

document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
        openMultiselects.forEach(({ close }) => close());
    }
});

document.addEventListener("DOMContentLoaded", () => {
    // The script is only added to the Plugin I/O page, but guard anyway so
    // that it never fails on pages without the browser.
    if (!document.getElementById("io-browser")) {
        return;
    }

    const searchInput = document.getElementById("io-search");
    const optionalCheckbox = document.getElementById("io-optional");

    const tableHeader = document.getElementById("io-table-header");
    const tableBody = document.getElementById("io-table-body");
    const countElement = document.getElementById("io-count");

    const previousButton = document.getElementById("io-prev");
    const nextButton = document.getElementById("io-next");
    const pageElement = document.getElementById("io-page");

    const emptyElement = document.getElementById("io-empty");
    const tableContainer = document.getElementById("io-table-container");
    const pagination = document.getElementById("io-pagination");

    const rowsPerPage = 50;

    const directionValues = ["Input", "Output", "Input/Output"];

    const directionAbbreviations = {
        Input: "I",
        Output: "O",
        "Input/Output": "I/O",
    };

    const directionClasses = {
        Input: "io-cell-input",
        Output: "io-cell-output",
        "Input/Output": "io-cell-io",
    };

    let allRows = [];
    let filteredRows = [];
    let currentPage = 1;
    let allPluginNames = [];
    let pluginHues = new Map();

    function buildPluginHues(pluginNames) {
        const hues = new Map();
        const goldenAngle = 137.508; // spreads hues evenly regardless of plugin count

        pluginNames.forEach((plugin, index) => {
            hues.set(plugin, Math.round((index * goldenAngle) % 360));
        });

        return hues;
    }

    const pluginSelect = createMultiselect(
        document.getElementById("io-plugin"),
        {
            allLabel: "All plugins",
            noneLabel: "No plugins selected",
            onChange: applyFilters,
        }
    );

    const directionSelect = createMultiselect(
        document.getElementById("io-direction"),
        {
            allLabel: "All directions",
            noneLabel: "No directions selected",
            onChange: applyFilters,
        }
    );

    directionSelect.setOptions(directionValues);

    function getVariableName(row) {
        return [row.top, row.medium, row.bottom]
            .filter(
                part =>
                    part !== undefined &&
                    part !== null &&
                    String(part).trim() !== ""
            )
            .join(" . ");
    }

    function getPlugins(rows) {
        return [...new Set(rows.map(row => row.plugin))].sort((a, b) =>
            a.localeCompare(b)
        );
    }

    function isOptional(row) {
        return Object.values(row.optional || {}).some(Boolean);
    }

    function getSearchText(row) {
        return [getVariableName(row), row.plugin, row.description || ""]
            .join(" ")
            .toLowerCase();
    }

    function getFilteredRows() {
        const searchTerm = searchInput.value.trim().toLowerCase();
        const selectedPlugins = pluginSelect.getSelected();
        const selectedDirections = directionSelect.getSelected();
        const optionalOnly = optionalCheckbox.checked;

        return allRows.filter(row => {
            if (searchTerm && !getSearchText(row).includes(searchTerm)) {
                return false;
            }

            if (!selectedPlugins.has(row.plugin)) {
                return false;
            }

            if (!selectedDirections.has(row.direction)) {
                return false;
            }

            if (optionalOnly && !isOptional(row)) {
                return false;
            }

            return true;
        });
    }

    function getVisiblePlugins(rows) {
        // Rows are already filtered by the plugin selection, so this shows
        // the selected plugins that have at least one matching variable.
        return getPlugins(rows);
    }

    function groupRowsByVariable(rows) {
        const grouped = new Map();

        rows.forEach(row => {
            const key = [row.top || "", row.medium || "", row.bottom || ""].join(
                "\u0000"
            );

            if (!grouped.has(key)) {
                grouped.set(key, {
                    top: row.top || "",
                    medium: row.medium || "",
                    bottom: row.bottom || "",
                    plugins: {},
                });
            }

            // The generator emits one row per plugin and variable, with the
            // input/output direction already combined.
            grouped.get(key).plugins[row.plugin] = row;
        });

        return [...grouped.values()];
    }

    function renderHeader(plugins) {
        tableHeader.innerHTML = "";

        ["Top", "Medium", "Bottom"].forEach(text => {
            const header = document.createElement("th");
            header.textContent = text;
            tableHeader.appendChild(header);
        });

        plugins.forEach(plugin => {
            const header = document.createElement("th");
            header.textContent = plugin;
            header.title = plugin;
            header.className = "io-cell-plugin";
            header.style.setProperty("--io-plugin-hue", pluginHues.get(plugin));
            tableHeader.appendChild(header);
        });
    }

    function renderBody(rows, plugins) {
        tableBody.innerHTML = "";

        const groupedRows = groupRowsByVariable(rows);
        const startIndex = (currentPage - 1) * rowsPerPage;
        const pageRows = groupedRows.slice(startIndex, startIndex + rowsPerPage);

        pageRows.forEach(variable => {
            const tableRow = document.createElement("tr");

            [variable.top, variable.medium].forEach(text => {
                const cell = document.createElement("td");
                cell.textContent = text;
                cell.className = "io-cell-key";
                tableRow.appendChild(cell);
            });

            const bottomCell = document.createElement("td");
            bottomCell.textContent = variable.bottom;
            bottomCell.className = "io-cell-key";
            tableRow.appendChild(bottomCell);

            plugins.forEach(plugin => {
                const pluginCell = document.createElement("td");
                const pluginRow = variable.plugins[plugin];

                pluginCell.style.setProperty(
                    "--io-plugin-hue",
                    pluginHues.get(plugin)
                );

                if (pluginRow) {
                    const direction = pluginRow.direction;
                    const optional = isOptional(pluginRow);
                    const titleParts = [`${plugin}: ${direction}`];

                    if (optional) {
                        titleParts.push("optional");
                    }

                    if (pluginRow.description) {
                        titleParts.push(pluginRow.description);
                    }

                    pluginCell.textContent =
                        (directionAbbreviations[direction] || direction) +
                        (optional ? "*" : "");
                    pluginCell.title = titleParts.join("\n");
                    pluginCell.className =
                        directionClasses[direction] || "io-cell-empty";

                    if (optional) {
                        pluginCell.classList.add("io-cell-optional");
                    }
                } else {
                    pluginCell.className = "io-cell-empty";
                }

                tableRow.appendChild(pluginCell);
            });

            tableBody.appendChild(tableRow);
        });

        return groupedRows.length;
    }

    function updatePagination(totalRows) {
        const totalPages = Math.max(1, Math.ceil(totalRows / rowsPerPage));

        if (currentPage > totalPages) {
            currentPage = totalPages;
        }

        pageElement.textContent = `Page ${currentPage} of ${totalPages}`;
        previousButton.disabled = currentPage <= 1;
        nextButton.disabled = currentPage >= totalPages;
    }

    function render() {
        filteredRows = getFilteredRows();

        const plugins = getVisiblePlugins(filteredRows);

        renderHeader(plugins);
        const totalRows = renderBody(filteredRows, plugins);
        updatePagination(totalRows);

        countElement.textContent = `${totalRows} variable${
            totalRows === 1 ? "" : "s"
        }`;

        const hasRows = totalRows > 0;

        emptyElement.style.display = hasRows ? "none" : "block";
        tableContainer.style.display = hasRows ? "block" : "none";
        pagination.style.display = hasRows ? "flex" : "none";
    }

    function applyFilters() {
        currentPage = 1;
        render();
    }

    searchInput.addEventListener("input", applyFilters);
    optionalCheckbox.addEventListener("change", applyFilters);

    previousButton.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage -= 1;
            render();
        }
    });

    nextButton.addEventListener("click", () => {
        currentPage += 1;
        render();
    });

    function showLoadError() {
        countElement.textContent = "Could not load Plugin I/O data.";
        emptyElement.textContent = "Plugin I/O data could not be loaded.";
        emptyElement.style.display = "block";
        tableContainer.style.display = "none";
        pagination.style.display = "none";
    }

    // Set by _static/plugin_io_data.js, which the documentation build
    // generates (see pyH2A.Utilities.io_information_generator).
    const data = window.PYH2A_PLUGIN_IO_DATA;

    if (!Array.isArray(data)) {
        console.error("Could not load Plugin I/O data: PYH2A_PLUGIN_IO_DATA is missing.");
        showLoadError();
        return;
    }

    allRows = data;
    allPluginNames = getPlugins(allRows);
    pluginHues = buildPluginHues(allPluginNames);

    pluginSelect.setOptions(allPluginNames);

    render();
});