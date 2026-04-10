// app.js — Entry point: fetches data, computes metrics, renders charts + scorecard

let charts      = null;
let granularity = 'weekly';
let dateFrom    = null;   // Date | null — null means use CONFIG.SIM_START
let dateTo      = null;   // Date | null — null means use CONFIG.SIM_END

// Raw data cache (fetched once)
let _releases   = null;
let _releaseMap = null;
let _stories    = null;
let _incidents  = null;

// ── Status helpers ────────────────────────────────────────────────────────────

function setStatus(state, text) {
  const dot  = document.getElementById('status-dot');
  const span = document.getElementById('status-text');
  dot.className  = 'status-dot ' + state;
  span.textContent = text;
}

// ── Scorecard update ──────────────────────────────────────────────────────────

function updateScorecard(dfData, ltData, cfrData, mttrData) {
  function render(idPrefix, metricKey, values, displayFn) {
    const cur = currentValue(values);
    document.getElementById('val-' + idPrefix).textContent =
      cur !== null ? displayFn(cur) : '—';
    const band   = cur !== null ? BANDS[metricKey].classify(cur) : null;
    const badge  = document.getElementById('badge-' + idPrefix);
    badge.textContent  = band ? band.charAt(0).toUpperCase() + band.slice(1) : '—';
    badge.className    = 'score-badge' + (band ? ' ' + band : '');
    // Colour the card border
    const card = document.getElementById('sc-' + idPrefix);
    const colours = { elite: '#10b981', high: '#3b82f6', medium: '#f59e0b', low: '#ef4444' };
    card.style.borderColor = band ? colours[band] : '';
  }

  const dfDisplay = granularity === 'weekly'
    ? v => v.toFixed(1) + '/wk'
    : v => (v * 4.33).toFixed(1) + '/mo';
  document.getElementById('sub-df').textContent =
    granularity === 'weekly' ? 'deployments / week' : 'deployments / month';
  render('df', 'df', dfData.values.map(v => v !== null ? dfWeeklyRate(v, granularity) : null), dfDisplay);

  render('lt',   'lt',   ltData.values,  v => v.toFixed(1) + 'd');
  render('cfr',  'cfr',  cfrData.values, v => v.toFixed(1) + '%');
  render('mttr', 'mttr', mttrData.values,v => v.toFixed(1) + 'h');
}

// ── Render ────────────────────────────────────────────────────────────────────

function render() {
  if (!_releaseMap || !_stories || !_incidents) return;

  const dfData   = computeDeploymentFrequency(_releaseMap, granularity, dateFrom, dateTo);
  const ltData   = computeLeadTime(_stories, _releaseMap, granularity, dateFrom, dateTo);
  const cfrData  = computeChangeFailureRate(_releaseMap, _incidents, granularity, dateFrom, dateTo);
  const mttrData = computeMTTR(_incidents, granularity, dateFrom, dateTo);

  updateChartData(charts.df,   dfData.labels,   dfData.values,   granularity, 'df');
  updateChartData(charts.lt,   ltData.labels,   ltData.values,   granularity, 'lt');
  updateChartData(charts.cfr,  cfrData.labels,  cfrData.values,  granularity, 'cfr');
  updateChartData(charts.mttr, mttrData.labels, mttrData.values, granularity, 'mttr');

  updateScorecard(dfData, ltData, cfrData, mttrData);
}

// ── Boot ──────────────────────────────────────────────────────────────────────

async function init() {
  charts = initCharts(granularity);
  setStatus('loading', 'Loading…');

  try {
    // Fetch GitHub releases (no auth needed for public repo)
    _releases   = await fetchReleases();
    _releaseMap = buildReleaseMap(_releases);
    setStatus('loading', 'Loading Jira…');

    // Fetch Jira data (via proxy)
    [_stories, _incidents] = await Promise.all([fetchStories(), fetchIncidents()]);

    setStatus('ok', `${_releases.length} releases · ${_stories.length} stories · ${_incidents.length} incidents`);
    render();

  } catch (err) {
    console.error(err);
    if (err.message.includes('localhost') || err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      setStatus('error', 'Proxy offline — run: python3 proxy/server.py');
    } else {
      setStatus('error', 'Error: ' + err.message);
    }
    // Still render GitHub-only data if Jira failed
    if (_releaseMap && !_stories) {
      _stories   = [];
      _incidents = [];
      render();
    }
  }
}

// ── Toggle ────────────────────────────────────────────────────────────────────

document.querySelectorAll('.toggle-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    granularity = btn.dataset.period;
    render();
  });
});

// ── Date range picker (flatpickr) ─────────────────────────────────────────────

let _fpFrom = null;
let _fpTo   = null;

function initDatePicker() {
  const sharedConfig = {
    dateFormat:  'd/M/Y',          // 01/Sep/2025
    minDate:     CONFIG.SIM_START,
    maxDate:     CONFIG.SIM_END,
    disableMobile: true,
  };

  _fpFrom = flatpickr('#date-from', {
    ...sharedConfig,
    defaultDate: CONFIG.SIM_START,
    onChange([selected]) {
      if (!selected) return;
      dateFrom = new Date(Date.UTC(
        selected.getFullYear(), selected.getMonth(), selected.getDate()
      ));
      // Keep "to" >= "from"
      if (dateTo && dateTo < dateFrom) {
        dateTo = new Date(dateFrom);
        _fpTo.setDate(dateTo, false);
      }
      render();
    },
  });

  _fpTo = flatpickr('#date-to', {
    ...sharedConfig,
    defaultDate: CONFIG.SIM_END,
    onChange([selected]) {
      if (!selected) return;
      dateTo = new Date(Date.UTC(
        selected.getFullYear(), selected.getMonth(), selected.getDate(), 23, 59, 59
      ));
      // Keep "from" <= "to"
      if (dateFrom && dateFrom > dateTo) {
        dateFrom = new Date(dateTo);
        _fpFrom.setDate(dateFrom, false);
      }
      render();
    },
  });

  document.getElementById('date-reset').addEventListener('click', () => {
    dateFrom = null;
    dateTo   = null;
    _fpFrom.setDate(CONFIG.SIM_START, false);
    _fpTo.setDate(CONFIG.SIM_END,   false);
    render();
  });
}

// ── Start ─────────────────────────────────────────────────────────────────────
initDatePicker();
init();
