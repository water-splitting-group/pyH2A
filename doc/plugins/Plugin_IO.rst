Plugin I/O
==========

Interactive overview of the inputs and outputs of all pyH2A plugins.

.. raw:: html

   <div id="io-browser">

       <div id="io-controls">

           <input
               id="io-search"
               type="search"
               placeholder="Search variables..."
               aria-label="Search variables"
           />

           <select
               id="io-plugin"
               aria-label="Filter by plugin"
           >
               <option value="">All plugins</option>
           </select>

           <select
               id="io-direction"
               aria-label="Filter by direction"
           >
               <option value="">All directions</option>
               <option value="Input">Input</option>
               <option value="Output">Output</option>
               <option value="Input/Output">Input/Output</option>
           </select>

           <label>
               <input
                   id="io-optional"
                   type="checkbox"
               >
               Optional only
           </label>

       </div>

       <div id="io-count"></div>

       <div id="io-table-container">

           <table id="io-table">

               <thead>
                   <tr id="io-table-header">
                       <th>Top</th>
                       <th>Medium</th>
                       <th>Bottom</th>
                   </tr>
               </thead>

               <tbody id="io-table-body"></tbody>

           </table>

       </div>

       <div id="io-pagination">

           <button
               id="io-prev"
               type="button"
           >
               Previous
           </button>

           <span id="io-page">
               Page 1 of 1
           </span>

           <button
               id="io-next"
               type="button"
           >
               Next
           </button>

       </div>

       <div id="io-empty">
           No matching interfaces.
       </div>

   </div>