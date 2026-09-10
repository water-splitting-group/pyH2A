document.addEventListener("DOMContentLoaded", function () {

    const search =
        document.getElementById("io-search");

    const plugin =
        document.getElementById("io-plugin");

    const direction =
        document.getElementById("io-direction");

    const optional =
        document.getElementById("io-optional");

    const tableHeader =
        document.getElementById("io-table-header");

    const tableBody =
        document.getElementById("io-table-body");

    const count =
        document.getElementById("io-count");

    const empty =
        document.getElementById("io-empty");

    const prevButton =
        document.getElementById("io-prev");

    const nextButton =
        document.getElementById("io-next");

    const pageDisplay =
        document.getElementById("io-page");


    // ------------------------------------------------------------
    // Settings
    // ------------------------------------------------------------

    const rowsPerPage = 50;

    let currentPage = 1;

    let data = [];


    // ------------------------------------------------------------
    // Load data
    // ------------------------------------------------------------

    fetch("../io_data.json")

        .then(function (response) {

            if (!response.ok) {
                throw new Error(
                    "Could not load io_data.json"
                );
            }

            return response.json();
        })

        .then(function (json) {

            data = json;

            fillPluginFilter();

            render();
        })

        .catch(function (error) {

            console.error(error);

            count.textContent =
                "Error loading Plugin I/O data.";

            empty.style.display = "block";
        });


    // ------------------------------------------------------------
    // Plugin dropdown
    // ------------------------------------------------------------

    function fillPluginFilter() {

        const plugins = [
            ...new Set(
                data.map(function (row) {
                    return row.plugin;
                })
            )
        ].sort();


        plugins.forEach(function (name) {

            const option =
                document.createElement("option");

            option.value = name;

            option.textContent = name;

            plugin.appendChild(option);
        });
    }


    // ------------------------------------------------------------
    // Filter data
    // ------------------------------------------------------------

    function getFilteredData() {

        const text =
            search.value.trim().toLowerCase();


        return data.filter(function (row) {


            // ----------------------------------------------------
            // Plugin filter
            // ----------------------------------------------------

            if (
                plugin.value &&
                row.plugin !== plugin.value
            ) {

                return false;
            }


            // ----------------------------------------------------
            // Direction filter
            // ----------------------------------------------------

            if (
                direction.value &&
                row.direction !== direction.value
            ) {

                return false;
            }


            // ----------------------------------------------------
            // Optional filter
            // ----------------------------------------------------

            if (
                optional.checked &&
                !row.optional
            ) {

                return false;
            }


            // ----------------------------------------------------
            // Search
            //
            // Search only the variable identity.
            // Plugin names and metadata are deliberately excluded.
            // ----------------------------------------------------

            if (text) {

                const variableName =
                    getVariableName(row.path)
                        .toLowerCase();

                if (
                    !variableName.includes(text)
                ) {

                    return false;
                }
            }


            return true;
        });
    }


    // ------------------------------------------------------------
    // Render table
    // ------------------------------------------------------------

    function render() {

        const rows =
            getFilteredData();


        tableHeader.innerHTML = "";

        tableBody.innerHTML = "";


        // --------------------------------------------------------
        // Determine variables
        // --------------------------------------------------------

        const variables = [
            ...new Set(
                rows.map(function (row) {
                    return getVariableName(row.path);
                })
            )
        ].sort();


        // --------------------------------------------------------
        // Determine plugins
        //
        // Only plugins that occur in the filtered data are shown.
        // --------------------------------------------------------

        let plugins = [
            ...new Set(
                rows.map(function (row) {
                    return row.plugin;
                })
            )
        ].sort();


        // --------------------------------------------------------
        // Explicit plugin selection
        //
        // If a plugin is selected, only that plugin is displayed.
        // --------------------------------------------------------

        if (plugin.value) {

            plugins = [
                plugin.value
            ];
        }


        // --------------------------------------------------------
        // Pagination
        // --------------------------------------------------------

        const totalPages =
            Math.max(
                1,
                Math.ceil(
                    variables.length /
                    rowsPerPage
                )
            );


        if (
            currentPage > totalPages
        ) {

            currentPage = totalPages;
        }


        const start =
            (currentPage - 1) *
            rowsPerPage;

        const end =
            start +
            rowsPerPage;

        const visibleVariables =
            variables.slice(
                start,
                end
            );


        // --------------------------------------------------------
        // Header
        // --------------------------------------------------------

        const variableHeader =
            document.createElement("th");

        variableHeader.textContent =
            "Variable";

        tableHeader.appendChild(
            variableHeader
        );


        plugins.forEach(function (pluginName) {

            const th =
                document.createElement("th");

            th.textContent =
                pluginName;

            tableHeader.appendChild(th);
        });


        // --------------------------------------------------------
        // Variables become rows
        // --------------------------------------------------------

        visibleVariables.forEach(function (variable) {

            const tr =
                document.createElement("tr");


            // ----------------------------------------------------
            // Variable
            // ----------------------------------------------------

            const variableCell =
                document.createElement("td");

            variableCell.textContent =
                variable;

            variableCell.title =
                variable;

            tr.appendChild(
                variableCell
            );


            // ----------------------------------------------------
            // Plugin cells
            // ----------------------------------------------------

            plugins.forEach(function (pluginName) {

                const cell =
                    document.createElement("td");


                const matches =
                    rows.filter(function (row) {

                        return (
                            row.plugin === pluginName &&
                            getVariableName(row.path) === variable
                        );
                    });


                if (matches.length > 0) {

                    const directions = [
                        ...new Set(
                            matches.map(function (row) {
                                return row.direction;
                            })
                        )
                    ];

                    cell.textContent =
                        directions.join(" / ");
                }


                tr.appendChild(cell);
            });


            tableBody.appendChild(tr);
        });


        // --------------------------------------------------------
        // Count
        // --------------------------------------------------------

        if (variables.length === 1) {

            count.textContent =
                "1 variable";

        } else {

            count.textContent =
                variables.length +
                " variables";
        }


        // --------------------------------------------------------
        // Pagination
        // --------------------------------------------------------

        pageDisplay.textContent =
            "Page " +
            currentPage +
            " of " +
            totalPages;


        prevButton.disabled =
            currentPage === 1;

        nextButton.disabled =
            currentPage === totalPages;


        // --------------------------------------------------------
        // Empty state
        // --------------------------------------------------------

        const hasResults =
            variables.length > 0;


        empty.style.display =
            hasResults
                ? "none"
                : "block";


        const pagination =
            document.getElementById(
                "io-pagination"
            );


        pagination.style.display =
            hasResults
                ? "flex"
                : "none";
    }


    // ------------------------------------------------------------
    // Get display variable name
    // ------------------------------------------------------------

    function getVariableName(path) {

        if (!path) {
            return "";
        }


        const parts =
            path
                .split(".")
                .filter(function (part) {
                    return part !== "";
                });


        if (parts.length === 0) {
            return "";
        }


        // --------------------------------------------------------
        // Wildcard variables
        //
        // Wildcard paths are implementation details. Keep the
        // meaningful owning table/group and remove the artificial
        // wildcard placeholder where possible.
        // --------------------------------------------------------

        if (
            parts.some(function (part) {
                return part.includes("<...>");
            })
        ) {

            return formatWildcardPath(parts);
        }


        // --------------------------------------------------------
        // Normal variables
        // --------------------------------------------------------

        return formatNormalPath(parts);
    }


    // ------------------------------------------------------------
    // Format normal path
    // ------------------------------------------------------------

    function formatNormalPath(parts) {

        if (parts.length === 1) {
            return parts[0];
        }


        const bottom =
            parts[parts.length - 1];

        const middle =
            parts[parts.length - 2];


        // --------------------------------------------------------
        // Remove "Value" when it is the only value below a
        // variable.
        //
        // A path such as:
        //
        // Electrolyzer.Nominal power.Value
        //
        // becomes:
        //
        // Electrolyzer . Nominal power
        //
        // while Cost_Value / Usage_Value are retained.
        // --------------------------------------------------------

        if (bottom === "Value") {

            return parts
                .slice(0, -1)
                .join(" . ");
        }


        // --------------------------------------------------------
        // Handle *_Value names.
        //
        // Cost_Value -> Cost
        // Usage_Value -> Usage
        //
        // These are only shortened when the path contains the
        // corresponding value key.
        // --------------------------------------------------------

        if (bottom.endsWith("_Value")) {

            const valueName =
                bottom.slice(
                    0,
                    -"_Value".length
                );

            return [
                ...parts.slice(0, -1),
                valueName
            ].join(" . ");
        }


        return parts.join(" . ");
    }


    // ------------------------------------------------------------
    // Format wildcard path
    // ------------------------------------------------------------

    function formatWildcardPath(parts) {

        const meaningfulParts =
            parts.filter(function (part) {

                return (
                    part !== "<...>" &&
                    part.trim() !== ""
                );
            });


        if (meaningfulParts.length === 0) {
            return parts.join(" . ");
        }


        return meaningfulParts.join(" . ");
    }


    // ------------------------------------------------------------
    // Previous page
    // ------------------------------------------------------------

    prevButton.addEventListener(
        "click",
        function () {

            if (currentPage > 1) {

                currentPage--;

                render();
            }
        }
    );


    // ------------------------------------------------------------
    // Next page
    // ------------------------------------------------------------

    nextButton.addEventListener(
        "click",
        function () {

            const rows =
                getFilteredData();

            const variables = [
                ...new Set(
                    rows.map(function (row) {
                        return getVariableName(row.path);
                    })
                )
            ];


            const totalPages =
                Math.max(
                    1,
                    Math.ceil(
                        variables.length /
                        rowsPerPage
                    )
                );


            if (
                currentPage < totalPages
            ) {

                currentPage++;

                render();
            }
        }
    );


    // ------------------------------------------------------------
    // Search
    // ------------------------------------------------------------

    search.addEventListener(
        "input",
        function () {

            currentPage = 1;

            render();
        }
    );


    // ------------------------------------------------------------
    // Plugin filter
    // ------------------------------------------------------------

    plugin.addEventListener(
        "change",
        function () {

            currentPage = 1;

            render();
        }
    );


    // ------------------------------------------------------------
    // Direction filter
    // ------------------------------------------------------------

    direction.addEventListener(
        "change",
        function () {

            currentPage = 1;

            render();
        }
    );


    // ------------------------------------------------------------
    // Optional filter
    // ------------------------------------------------------------

    optional.addEventListener(
        "change",
        function () {

            currentPage = 1;

            render();
        }
    );

});