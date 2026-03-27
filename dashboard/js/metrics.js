// metrics.js — Pure functions that compute DORA metrics from raw API data.
// All functions return { labels: string[], values: number[] }

// ── Period helpers ────────────────────────────────────────────────────────────

function startOfWeek(date) {
  const d = new Date(date);
  const day = d.getUTCDay(); // 0=Sun
  d.setUTCDate(d.getUTCDate() - ((day + 6) % 7)); // Monday
  d.setUTCHours(0, 0, 0, 0);
  return d;
}

function startOfMonth(date) {
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
}

function periodStart(date, granularity) {
  return granularity === 'weekly' ? startOfWeek(date) : startOfMonth(date);
}

function formatLabel(date, granularity) {
  if (granularity === 'weekly') {
    return date.toLocaleDateString('en-GB', { month: 'short', day: 'numeric', timeZone: 'UTC' });
  }
  return date.toLocaleDateString('en-GB', { month: 'short', year: '2-digit', timeZone: 'UTC' });
}

// Build an ordered array of period-start dates covering rangeStart → rangeEnd
function buildPeriods(granularity, rangeStart, rangeEnd) {
  const start = rangeStart || CONFIG.SIM_START;
  const end   = rangeEnd   || CONFIG.SIM_END;
  const periods = [];
  let cur = periodStart(start, granularity);
  while (cur <= end) {
    periods.push(new Date(cur));
    if (granularity === 'weekly') {
      cur = new Date(cur.getTime() + 7 * 24 * 60 * 60 * 1000);
    } else {
      cur = new Date(Date.UTC(cur.getUTCFullYear(), cur.getUTCMonth() + 1, 1));
    }
  }
  return periods;
}

// Map a date to its period index in the periods array (-1 if out of range)
function periodIndex(date, periods, granularity) {
  const ps = periodStart(date, granularity);
  const t = ps.getTime();
  return periods.findIndex(p => p.getTime() === t);
}

// ── 1. Deployment Frequency ───────────────────────────────────────────────────

function computeDeploymentFrequency(releaseMap, granularity, rangeStart, rangeEnd) {
  const periods = buildPeriods(granularity, rangeStart, rangeEnd);
  const counts  = new Array(periods.length).fill(0);

  Object.values(releaseMap).forEach(({ date }) => {
    const idx = periodIndex(date, periods, granularity);
    if (idx >= 0) counts[idx]++;
  });

  return {
    labels: periods.map(p => formatLabel(p, granularity)),
    values: counts,
  };
}

// ── 2. Lead Time for Changes ──────────────────────────────────────────────────
// Lead time = release date − First Commit Date (in days), per story.
// Bucketed by the story's release date period.

function computeLeadTime(stories, releaseMap, granularity, rangeStart, rangeEnd) {
  const periods = buildPeriods(granularity, rangeStart, rangeEnd);
  const buckets = periods.map(() => []);  // array of lead-time values per period

  stories.forEach(issue => {
    const fields  = issue.fields;
    const tag     = fields[CONFIG.FIELD_DEPLOYMENT_VERSION];
    const fcStr   = fields[CONFIG.FIELD_FIRST_COMMIT_DATE];
    if (!tag || !fcStr) return;

    const rel = releaseMap[tag];
    if (!rel) return;

    const firstCommit = new Date(fcStr);
    const leadDays    = (rel.date - firstCommit) / (1000 * 60 * 60 * 24);
    if (leadDays < 0 || leadDays > 180) return;  // sanity filter

    const idx = periodIndex(rel.date, periods, granularity);
    if (idx >= 0) buckets[idx].push(leadDays);
  });

  return {
    labels: periods.map(p => formatLabel(p, granularity)),
    values: buckets.map(b => b.length ? +(b.reduce((s, v) => s + v, 0) / b.length).toFixed(1) : null),
  };
}

// ── 3. Change Failure Rate ────────────────────────────────────────────────────
// CFR = (releases that triggered an incident) / (total releases) per period (%)

function computeChangeFailureRate(releaseMap, incidents, granularity, rangeStart, rangeEnd) {
  const periods  = buildPeriods(granularity, rangeStart, rangeEnd);
  const total    = new Array(periods.length).fill(0);
  const failures = new Array(periods.length).fill(0);

  // Count total releases per period
  Object.values(releaseMap).forEach(({ date }) => {
    const idx = periodIndex(date, periods, granularity);
    if (idx >= 0) total[idx]++;
  });

  // Count failure releases (those with an incident) per period
  const failedTags = new Set(
    incidents.map(i => i.fields[CONFIG.FIELD_LINKED_RELEASE]).filter(Boolean)
  );
  Object.entries(releaseMap).forEach(([tag, { date }]) => {
    if (!failedTags.has(tag)) return;
    const idx = periodIndex(date, periods, granularity);
    if (idx >= 0) failures[idx]++;
  });

  return {
    labels: periods.map(p => formatLabel(p, granularity)),
    values: total.map((t, i) =>
      t > 0 ? +((failures[i] / t) * 100).toFixed(1) : null
    ),
  };
}

// ── 4. MTTR ───────────────────────────────────────────────────────────────────
// MTTR = SimulatedResolved − SimulatedCreated (hours), bucketed by incident open date.

function computeMTTR(incidents, granularity, rangeStart, rangeEnd) {
  const periods = buildPeriods(granularity, rangeStart, rangeEnd);
  const buckets = periods.map(() => []);

  incidents.forEach(issue => {
    const desc    = issue.fields.description;
    const opened  = parseDescriptionDate(desc, 'SimulatedCreated');
    const resolved= parseDescriptionDate(desc, 'SimulatedResolved');
    if (!opened || !resolved) return;

    const mttrH = (resolved - opened) / (1000 * 60 * 60);
    if (mttrH < 0 || mttrH > 720) return;  // sanity filter

    const idx = periodIndex(opened, periods, granularity);
    if (idx >= 0) buckets[idx].push(mttrH);
  });

  return {
    labels: periods.map(p => formatLabel(p, granularity)),
    values: buckets.map(b => b.length ? +(b.reduce((s, v) => s + v, 0) / b.length).toFixed(1) : null),
  };
}

// ── DORA band classification ──────────────────────────────────────────────────

const BANDS = {
  df: {   // deployments per week
    classify: v => v >= 7 ? 'elite' : v >= 1 ? 'high' : v >= 0.25 ? 'medium' : 'low',
    thresholds: { weekly: { elite: 7, high: 1 }, monthly: { elite: 30, high: 4 } },
  },
  lt: {   // days
    classify: v => v < 1 ? 'elite' : v < 7 ? 'high' : v < 30 ? 'medium' : 'low',
    thresholds: { weekly: { elite: 1, high: 7 }, monthly: { elite: 1, high: 7 } },
  },
  cfr: {  // %
    classify: v => v <= 5 ? 'elite' : v <= 10 ? 'high' : v <= 15 ? 'medium' : 'low',
    thresholds: { weekly: { elite: 5, high: 10 }, monthly: { elite: 5, high: 10 } },
  },
  mttr: { // hours
    classify: v => v < 1 ? 'elite' : v < 24 ? 'high' : v < 168 ? 'medium' : 'low',
    thresholds: { weekly: { elite: 1, high: 24 }, monthly: { elite: 1, high: 24 } },
  },
};

// Return the last non-null value as the "current" figure
function currentValue(values) {
  for (let i = values.length - 1; i >= 0; i--) {
    if (values[i] !== null && values[i] !== undefined) return values[i];
  }
  return null;
}

// For DF: convert raw count per period to a per-week rate for classification
function dfWeeklyRate(count, granularity) {
  return granularity === 'weekly' ? count : count / 4.33;
}
