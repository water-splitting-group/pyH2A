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

    const rowsPerPage = 20;

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
            // ----------------------------------------------------

            if (text) {

                const searchable = [

                    row.plugin,

                    row.path,

                    row.direction,

                    row.type,

                    row.dimension,

                    row.description

                ]
                    .join(" ")
                    .toLowerCase();


                if (
                    !searchable.includes(text)
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


        // --------------------------------------------------------
        // Clear table
        // --------------------------------------------------------

        tableHeader.innerHTML = "";

        tableBody.innerHTML = "";


        // --------------------------------------------------------
        // Determine plugins
        // --------------------------------------------------------

        let plugins;


        if (plugin.value) {

            plugins = [
                plugin.value
            ];

        } else {

            plugins = [
                ...new Set(
                    data.map(function (row) {
                        return row.plugin;
                    })
                )
            ].sort();
        }


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
            // Variable name
            // ----------------------------------------------------

            const variableCell =
                document.createElement("td");

            variableCell.textContent =
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
        // Pagination display
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

        empty.style.display =
            variables.length === 0
                ? "block"
                : "none";


        // --------------------------------------------------------
        // Hide pagination if there are no results
        // --------------------------------------------------------

        const pagination =
            document.getElementById(
                "io-pagination"
            );


        if (variables.length === 0) {

            pagination.style.display =
                "none";

        } else {

            pagination.style.display =
                "flex";
        }
    }


    // ------------------------------------------------------------
    // Get variable name from path
    // ------------------------------------------------------------

    function getVariableName(path) {

        if (!path) {

            return "";
        }


        // --------------------------------------------------------
        // Wildcard paths
        //
        // Keep the complete wildcard path.
        //
        // Example:
        //
        // <...> Direct Capital Cost <...>.<...>
        //
        // remains:
        //
        // <...> Direct Capital Cost <...>.<...>
        // --------------------------------------------------------

        if (path.includes("<...>")) {

            return path.trim();
        }


        // --------------------------------------------------------
        // Normal paths
        //
        // Example:
        //
        // Battery.Design capacity
        //
        // becomes:
        //
        // Design capacity
        // --------------------------------------------------------

        const parts =
            path.split(".");


        return parts[
            parts.length - 1
        ];
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