document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const spinner = document.getElementById('spinner');
    const statusMsg = document.getElementById('statusMsg');
    const resultArea = document.getElementById('resultArea');
    let spendingChart = null;

    dropZone.onclick = () => fileInput.click();
    fileInput.onchange = (e) => handleUpload(e.target.files[0]);

    // Drag and drop handlers
    dropZone.ondragover = (e) => { e.preventDefault(); dropZone.style.background = '#e2e6ea'; };
    dropZone.ondragleave = () => { dropZone.style.background = '#f8f9fa'; };
    dropZone.ondrop = (e) => {
        e.preventDefault();
        dropZone.style.background = '#f8f9fa';
        handleUpload(e.dataTransfer.files[0]);
    };

    async function handleUpload(file) {
        if (!file) return;

        statusMsg.innerText = "🔍 Processing pipeline: Image -> OCR -> AI Analysis...";
        spinner.style.display = "inline-block";
        resultArea.style.display = "none";

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', { method: 'POST', body: formData });
            const data = await response.json();

            if (data.error) {
                alert("Pipeline Error: " + (data.message || data.error));
                return;
            }

            updateUI(data);
        } catch (err) {
            console.error(err);
            alert("Upload failed. Check the terminal for detailed errors.");
        } finally {
            spinner.style.display = "none";
            statusMsg.innerText = "";
        }
    }

    function updateUI(data) {
        // Step 5: Summarization Logic
        document.getElementById('totalAmt').innerText = `$${parseFloat(data.total || 0).toFixed(2)}`;
        document.getElementById('storeName').innerText = data.store_name || "Unknown Store";
        document.getElementById('receiptDate').innerText = data.date || "Unknown Date";
        document.getElementById('aiAdvice').innerText = data.advice || "No advice available.";

        const tbody = document.getElementById('itemsTableBody');
        tbody.innerHTML = '';
        const catTotals = {};

        data.items.forEach(item => {
            const itemTotal = parseFloat(item.price) * (parseInt(item.qty) || 1);
            const row = `<tr>
                <td>${item.name}</td>
                <td>${item.qty}</td>
                <td>$${parseFloat(item.price).toFixed(2)}</td>
                <td><span class="badge bg-secondary">${item.category}</span></td>
                <td>$${itemTotal.toFixed(2)}</td>
            </tr>`;
            tbody.innerHTML += row;

            // Aggregate by category
            catTotals[item.category] = (catTotals[item.category] || 0) + itemTotal;
        });

        // Identify Top Category for UI
        const topCat = Object.keys(catTotals).reduce((a, b) => catTotals[a] > catTotals[b] ? a : b);
        const topCatMsg = `🏆 Top Spending Category: <strong>${topCat}</strong> ($${catTotals[topCat].toFixed(2)})`;
        document.getElementById('topCategoryHighlight').innerHTML = topCatMsg;

        // Render Chart (Step 5 visual summary)
        updateChart(catTotals);
        resultArea.style.display = "block";
    }

    function updateChart(totals) {
        const ctx = document.getElementById('spendingChart').getContext('2d');
        if (spendingChart) spendingChart.destroy();

        spendingChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(totals),
                datasets: [{
                    data: Object.values(totals),
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#D3D3D3']
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
});