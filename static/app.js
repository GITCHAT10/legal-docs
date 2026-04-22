document.getElementById('designForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
        island_name: document.getElementById('island_name').value,
        plot_width: parseFloat(document.getElementById('plot_width').value),
        plot_depth: parseFloat(document.getElementById('plot_depth').value),
        target_rooms: parseInt(document.getElementById('target_rooms').value)
    };

    const resultsDiv = document.getElementById('results');
    const outputDiv = document.getElementById('output');

    resultsDiv.classList.remove('hidden');
    outputDiv.innerHTML = '<p class="animate-pulse">Executing Sovereign Pipeline...</p>';

    try {
        const response = await fetch('/api/v1/design', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Pipeline execution failed');
        }

        const result = await response.json();

        outputDiv.innerHTML = `
            <div class="border-l-2 border-blue-500 pl-4 py-2">
                <p class="text-blue-400 font-bold underline mb-2">MNOS SHADOW COMMIT SUCCESS</p>
                <p><span class="text-slate-500">Island:</span> ${result.island.type} Zone</p>
                <p><span class="text-slate-500">Layout:</span> ${result.layout.is_single_loaded ? 'Single-Loaded' : 'Double-Loaded'}</p>
                <p><span class="text-slate-500">Steel:</span> ${result.layout.steel_tonnage_est.toFixed(2)} tons</p>
            </div>

            <div class="border-l-2 border-green-500 pl-4 py-2">
                <p class="text-green-400 font-bold underline mb-2">AEGIS COMPLIANCE</p>
                <p><span class="text-slate-500">Status:</span> ${result.compliance.compliant ? 'PASSED' : 'FAILED'}</p>
                <p><span class="text-slate-500">FAR:</span> ${result.compliance.far.toFixed(2)}</p>
                <p><span class="text-slate-500">Fire Exit:</span> ${result.compliance.needs_second_fire_exit ? 'MANDATORY' : 'STANDARD'}</p>
            </div>

            <div class="border-l-2 border-yellow-500 pl-4 py-2">
                <p class="text-yellow-400 font-bold underline mb-2">FCE / MOATS BILLING</p>
                <p><span class="text-slate-500">Construction:</span> $${result.boq.construction_cost.toLocaleString()}</p>
                <p><span class="text-slate-500">TGST (17%):</span> $${result.boq.fiscal_valuation.tgst.toLocaleString()}</p>
                <p><span class="text-slate-500">TOTAL:</span> $${result.boq.fiscal_valuation.total.toLocaleString()}</p>
            </div>
        `;

    } catch (err) {
        outputDiv.innerHTML = `<p class="text-red-500">ERROR: ${err.message}</p>`;
    }
});
