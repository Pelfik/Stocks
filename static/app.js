const button = document.getElementById("run");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
let frontierChart = null;

function pct(value) {
  return `${(value * 100).toFixed(2)}%`;
}

function renderWeights(weights) {
  const container = document.getElementById("weights");
  container.innerHTML = "";

  Object.entries(weights)
    .sort((a, b) => b[1] - a[1])
    .forEach(([ticker, weight]) => {
      const row = document.createElement("div");
      row.className = "weight-row";
      row.innerHTML = `
        <div class="ticker">${ticker}</div>
        <div class="bar"><div style="width:${Math.max(0, Math.min(100, weight * 100))}%"></div></div>
        <div class="value">${pct(weight)}</div>
      `;
      container.appendChild(row);
    });
}

function renderChart(data) {
  const frontier = data.frontier.map(p => ({
    x: p.volatility * 100,
    y: p.return * 100
  }));

  const maxSharpe = {
    x: data.max_sharpe.volatility * 100,
    y: data.max_sharpe.return * 100
  };

  const minVar = {
    x: data.min_variance.volatility * 100,
    y: data.min_variance.return * 100
  };

  if (frontierChart) frontierChart.destroy();

  frontierChart = new Chart(
    document.getElementById("frontierChart"),
    {
      type: "scatter",
      data: {
        datasets: [
          {
            label: "Efficient frontier",
            data: frontier,
            showLine: true,
            pointRadius: 2,
            tension: 0.1
          },
          {
            label: "Max Sharpe",
            data: [maxSharpe],
            pointRadius: 7
          },
          {
            label: "Minimum variance",
            data: [minVar],
            pointRadius: 7
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        parsing: false,
        scales: {
          x: {
            title: { display: true, text: "Annualized volatility, %" }
          },
          y: {
            title: { display: true, text: "Expected annual return, %" }
          }
        }
      }
    }
  );
}

button.addEventListener("click", async () => {
  const tickers = document.getElementById("tickers").value
    .split(",")
    .map(x => x.trim().toUpperCase())
    .filter(Boolean);

  const years = Number(document.getElementById("years").value);
  const riskFreeRate = Number(document.getElementById("rf").value) / 100;

  button.disabled = true;
  statusEl.textContent = "Fetching market data and optimizing…";

  try {
    const response = await fetch("/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tickers,
        years,
        risk_free_rate: riskFreeRate
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Optimization failed");
    }

    document.getElementById("ret").textContent = pct(data.max_sharpe.return);
    document.getElementById("vol").textContent = pct(data.max_sharpe.volatility);
    document.getElementById("sharpe").textContent = data.max_sharpe.sharpe.toFixed(3);
    document.getElementById("period").textContent =
      `${data.start_date} → ${data.end_date} · ${data.observations} observations`;

    renderWeights(data.max_sharpe.weights);
    renderChart(data);

    resultsEl.classList.remove("hidden");
    statusEl.textContent = "Done.";
  } catch (err) {
    statusEl.textContent = err.message;
  } finally {
    button.disabled = false;
  }
});
