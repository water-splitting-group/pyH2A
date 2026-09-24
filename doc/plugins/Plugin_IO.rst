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

           <div class="io-multiselect" id="io-plugin">
               <button
                   type="button"
                   class="io-multiselect-button"
                   aria-haspopup="listbox"
                   aria-expanded="false"
               >
                   <span class="io-multiselect-label">All plugins</span>
                   <span class="io-multiselect-arrow" aria-hidden="true">&#9662;</span>
               </button>

               <div class="io-multiselect-panel" hidden>
                   <div class="io-multiselect-actions">
                       <button type="button" class="io-multiselect-select-all">Select all</button>
                       <button type="button" class="io-multiselect-clear">Clear</button>
                   </div>
                   <div class="io-multiselect-options"></div>
               </div>
           </div>

           <div class="io-multiselect" id="io-direction">
               <button
                   type="button"
                   class="io-multiselect-button"
                   aria-haspopup="listbox"
                   aria-expanded="false"
               >
                   <span class="io-multiselect-label">All directions</span>
                   <span class="io-multiselect-arrow" aria-hidden="true">&#9662;</span>
               </button>

               <div class="io-multiselect-panel" hidden>
                   <div class="io-multiselect-actions">
                       <button type="button" class="io-multiselect-select-all">Select all</button>
                       <button type="button" class="io-multiselect-clear">Clear</button>
                   </div>
                   <div class="io-multiselect-options"></div>
               </div>
           </div>

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