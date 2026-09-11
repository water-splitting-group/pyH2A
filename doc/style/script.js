document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("io-search");
    const pluginSelect = document.getElementById("io-plugin");
    const directionSelect = document.getElementById("io-direction");
    const optionalCheckbox = document.getElementById("io-optional");

    const tableHeader = document.getElementById("io-table-header");
    const tableBody = document.getElementById("io-table-body");

    const countElement = document.getElementById("io-count");

    const previousButton = document.getElementById("io-prev");
    const nextButton = document.getElementById("io-next");
    const pageElement = document.getElementById("io-page");

    const emptyElement = document.getElementById("io-empty");
    const tableContainer =
        document.getElementById("io-table-container");
    const pagination =
        document.getElementById("io-pagination");

    const rowsPerPage = 50;

    let allRows = [];
    let filteredRows = [];
    let currentPage = 1;

    function getVariableName(row) {
        return [
            row.top,
            row.medium,
            row.bottom,
        ]
            .filter(
                part =>
                    part !== undefined &&
                    part !== null &&
                    String(part).trim() !== ""
            )
            .join(" . ");
    }

    function getPlugins(rows) {
        return [...new Set(
            rows.map(row => row.plugin)
        )].sort(
            (a, b) => a.localeCompare(b)
        );
    }

    function populatePluginSelect() {
        const currentValue = pluginSelect.value;
        const plugins = getPlugins(allRows);

        pluginSelect.innerHTML = "";

        const allOption = document.createElement("option");
        allOption.value = "";
        allOption.textContent = "All plugins";

        pluginSelect.appendChild(allOption);

        plugins.forEach(plugin => {
            const option = document.createElement("option");

            option.value = plugin;
            option.textContent = plugin;

            pluginSelect.appendChild(option);
        });

        if (plugins.includes(currentValue)) {
            pluginSelect.value = currentValue;
        }
    }

    function getFilteredRows() {
        const searchTerm = searchInput.value
            .trim()
            .toLowerCase();

        const selectedPlugin = pluginSelect.value;
        const selectedDirection = directionSelect.value;
        const optionalOnly = optionalCheckbox.checked;

        return allRows.filter(row => {
            const variableName = getVariableName(row)
                .toLowerCase();

            if (
                searchTerm &&
                !variableName.includes(searchTerm)
            ) {
                return false;
            }

            if (
                selectedPlugin &&
                row.plugin !== selectedPlugin
            ) {
                return false;
            }

            if (
                selectedDirection &&
                row.direction !== selectedDirection
            ) {
                return false;
            }

            if (
                optionalOnly &&
                !row.optional
            ) {
                return false;
            }

            return true;
        });
    }

    function getVisiblePlugins(rows) {
        const selectedPlugin = pluginSelect.value;

        if (selectedPlugin) {
            return [selectedPlugin];
        }

        return getPlugins(rows);
    }

    function groupRowsByVariable(rows) {
        const grouped = new Map();

        rows.forEach(row => {
            const variableKey = [
                row.top || "",
                row.medium || "",
                row.bottom || "",
            ].join("\u0000");

            if (!grouped.has(variableKey)) {
                grouped.set(
                    variableKey,
                    {
                        top: row.top || "",
                        medium: row.medium || "",
                        bottom: row.bottom || "",
                        optional: Boolean(row.optional),
                        plugins: {},
                    }
                );
            }

            const variable = grouped.get(variableKey);

            if (row.optional) {
                variable.optional = true;
            }

            if (!variable.plugins[row.plugin]) {
                variable.plugins[row.plugin] = [];
            }

            variable.plugins[row.plugin].push(
                row.direction
            );
        });

        return [...grouped.values()];
    }

    function getDirectionText(directions) {
        const uniqueDirections = [
            ...new Set(directions),
        ];

        if (
            uniqueDirections.includes("Input/Output")
        ) {
            return "Input/Output";
        }

        if (
            uniqueDirections.includes("Input") &&
            uniqueDirections.includes("Output")
        ) {
            return "Input/Output";
        }

        return uniqueDirections.join(", ");
    }

    function renderHeader(plugins) {
        tableHeader.innerHTML = "";

        const headers = [
            "Top",
            "Medium",
            "Bottom",
        ];

        headers.forEach(text => {
            const header = document.createElement("th");
            header.textContent = text;
            tableHeader.appendChild(header);
        });

        plugins.forEach(plugin => {
            const header = document.createElement("th");

            header.textContent = plugin;

            tableHeader.appendChild(header);
        });
    }

    function renderBody(rows, plugins) {
        tableBody.innerHTML = "";

        const groupedRows = groupRowsByVariable(rows);

        const startIndex =
            (currentPage - 1) * rowsPerPage;

        const pageRows = groupedRows.slice(
            startIndex,
            startIndex + rowsPerPage
        );

        pageRows.forEach(variable => {
            const tableRow = document.createElement("tr");

            const topCell = document.createElement("td");
            topCell.textContent = variable.top;
            tableRow.appendChild(topCell);

            const mediumCell = document.createElement("td");
            mediumCell.textContent = variable.medium;
            tableRow.appendChild(mediumCell);

            const bottomCell = document.createElement("td");
            bottomCell.textContent = variable.bottom;

            if (variable.optional) {
                const optionalLabel =
                    document.createElement("span");

                optionalLabel.className =
                    "io-optional-label";

                optionalLabel.textContent =
                    "optional";

                bottomCell.appendChild(
                    optionalLabel
                );
            }

            tableRow.appendChild(bottomCell);

            plugins.forEach(plugin => {
                const pluginCell =
                    document.createElement("td");

                const directions =
                    variable.plugins[plugin];

                if (directions) {
                    pluginCell.textContent =
                        getDirectionText(directions);
                } else {
                    pluginCell.textContent = "";
                }

                tableRow.appendChild(pluginCell);
            });

            tableBody.appendChild(tableRow);
        });

        return groupedRows.length;
    }

    function updatePagination(totalRows) {
        const totalPages = Math.max(
            1,
            Math.ceil(totalRows / rowsPerPage)
        );

        if (currentPage > totalPages) {
            currentPage = totalPages;
        }

        pageElement.textContent =
            `Page ${currentPage} of ${totalPages}`;

        previousButton.disabled =
            currentPage <= 1;

        nextButton.disabled =
            currentPage >= totalPages;
    }

    function render() {
        filteredRows = getFilteredRows();

        const plugins = getVisiblePlugins(
            filteredRows
        );

        renderHeader(plugins);

        const totalRows = renderBody(
            filteredRows,
            plugins
        );

        updatePagination(totalRows);

        countElement.textContent =
            `${totalRows} variable${
                totalRows === 1 ? "" : "s"
            }`;

        const hasRows = totalRows > 0;

        emptyElement.style.display =
            hasRows ? "none" : "block";

        tableContainer.style.display =
            hasRows ? "block" : "none";

        pagination.style.display =
            hasRows ? "flex" : "none";
    }

    function applyFilters() {
        currentPage = 1;
        render();
    }

    searchInput.addEventListener(
        "input",
        applyFilters
    );

    pluginSelect.addEventListener(
        "change",
        applyFilters
    );

    directionSelect.addEventListener(
        "change",
        applyFilters
    );

    optionalCheckbox.addEventListener(
        "change",
        applyFilters
    );

    previousButton.addEventListener(
        "click",
        () => {
            if (currentPage > 1) {
                currentPage -= 1;
                render();
            }
        }
    );

    nextButton.addEventListener(
        "click",
        () => {
            const totalRows =
                groupRowsByVariable(
                    filteredRows
                ).length;

            const totalPages = Math.ceil(
                totalRows / rowsPerPage
            );

            if (currentPage < totalPages) {
                currentPage += 1;
                render();
            }
        }
    );

    fetch("../io_data.json")
        .then(response => {
            if (!response.ok) {
                throw new Error(
                    `HTTP error ${response.status}`
                );
            }

            return response.json();
        })
        .then(data => {
            allRows = data;

            populatePluginSelect();
            render();
        })
        .catch(error => {
            console.error(
                "Could not load Plugin I/O data:",
                error
            );

            countElement.textContent =
                "Could not load Plugin I/O data.";

            emptyElement.textContent =
                "Plugin I/O data could not be loaded.";

            emptyElement.style.display = "block";
            tableContainer.style.display = "none";
            pagination.style.display = "none";
        });
});