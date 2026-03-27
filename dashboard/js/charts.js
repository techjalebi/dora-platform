// charts.js — Chart.js setup and rendering

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#0f172a',
      borderColor: '#334155',
      borderWidth: 1,
      titleColor: '#f1f5f9',
      bodyColor: '#94a3b8',
      padding: 10,
    },
  },
  scales: {
    x: {
      grid:  { color: 'rgba(51,65,85,.5)', drawBorder: false },
      ticks: { color: '#64748b', font: { size: 11 }, maxTicksLimit: 10 },
    },
    y: {
      grid:  { color: 'rgba(51,65,85,.5)', drawBorder: false },
      ticks: { color: '#64748b', font: { size: 11 } },
      beginAtZero: true,
    },
  },
};

function bandAnnotations(metricKey, granularity) {
  const t = BANDS[metricKey].thresholds[granularity];
  return {
    eliteLine: {
      type: 'line', yMin: t.elite, yMax: t.elite,
      borderColor: 'rgba(16,185,129,.6)', borderWidth: 1.5,
      borderDash: [4, 4],
      label: {
        content: 'Elite', enabled: true, position: 'end',
        backgroundColor: 'rgba(16,185,129,.15)',
        color: '#10b981', font: { size: 10, weight: 'bold' },
        padding: { x: 4, y: 2 },
      },
    },
    highLine: {
      type: 'line', yMin: t.high, yMax: t.high,
      borderColor: 'rgba(59,130,246,.6)', borderWidth: 1.5,
      borderDash: [4, 4],
      label: {
        content: 'High', enabled: true, position: 'end',
        backgroundColor: 'rgba(59,130,246,.15)',
        color: '#3b82f6', font: { size: 10, weight: 'bold' },
        padding: { x: 4, y: 2 },
      },
    },
  };
}

function makeBarChart(canvasId, metricKey, granularity, color = '#3b82f6') {
  const ctx = document.getElementById(canvasId).getContext('2d');
  return new Chart(ctx, {
    type: 'bar',
    data: { labels: [], datasets: [{ data: [], backgroundColor: color + '99',
            borderColor: color, borderWidth: 1.5, borderRadius: 4,
            borderSkipped: false }] },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        annotation: { annotations: bandAnnotations(metricKey, granularity) },
      },
    },
  });
}

function makeLineChart(canvasId, metricKey, granularity, color = '#f59e0b') {
  const ctx = document.getElementById(canvasId).getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: { labels: [], datasets: [{
      data: [], borderColor: color, backgroundColor: color + '22',
      borderWidth: 2, pointRadius: 3, pointHoverRadius: 5,
      fill: true, tension: 0.3, spanGaps: true,
    }]},
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        annotation: { annotations: bandAnnotations(metricKey, granularity) },
      },
    },
  });
}

function updateChartData(chart, labels, values, granularity, metricKey) {
  chart.data.labels = labels;
  chart.data.datasets[0].data = values;
  // Refresh band annotations when granularity changes
  chart.options.plugins.annotation.annotations = bandAnnotations(metricKey, granularity);
  chart.update('active');
}

// Initialise all four charts
function initCharts(granularity) {
  return {
    df:   makeBarChart ('chart-df',   'df',   granularity, '#3b82f6'),
    lt:   makeBarChart ('chart-lt',   'lt',   granularity, '#8b5cf6'),
    cfr:  makeLineChart('chart-cfr',  'cfr',  granularity, '#f59e0b'),
    mttr: makeBarChart ('chart-mttr', 'mttr', granularity, '#06b6d4'),
  };
}
