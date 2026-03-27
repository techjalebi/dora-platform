// api.js — All fetch() calls to GitHub and Jira (via proxy)

// ── Helpers ───────────────────────────────────────────────────────────────────

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${url}`);
  return res.json();
}

// Paginate through Jira search results using the POST /search/jql endpoint
// (new Jira Cloud API uses nextPageToken, not startAt)
async function jiraSearchAll(jql, fields) {
  const results = [];
  const maxResults = 100;
  const url = `${CONFIG.JIRA_PROXY}/rest/api/3/search/jql`;
  let nextPageToken = undefined;

  while (true) {
    const body = { jql, fields, maxResults };
    if (nextPageToken) body.nextPageToken = nextPageToken;

    const data = await fetchJSON(url, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body),
    });

    results.push(...(data.issues || []));
    nextPageToken = data.nextPageToken;
    if (!nextPageToken || !data.issues || data.issues.length < maxResults) break;
  }
  return results;
}

// ── Release date reconstruction ───────────────────────────────────────────────
// GitHub release timestamps reflect when the sim script ran, not the simulated
// period. We reconstruct dates from release creation order (ascending by id).

function buildReleaseMap(releases) {
  // releases: sorted ascending by creation order (index = position in sort)
  const map = {};   // tag -> { date: Date, isHotfix: bool }
  releases.forEach((rel, i) => {
    const simDate = new Date(
      CONFIG.SIM_START.getTime() +
      (i + 1) * CONFIG.DEPLOY_INTERVAL_DAYS * 24 * 60 * 60 * 1000
    );
    map[rel.tag_name] = {
      date:     simDate,
      isHotfix: rel.tag_name.endsWith('-hotfix'),
      index:    i,
    };
  });
  return map;
}

// ── GitHub ────────────────────────────────────────────────────────────────────

async function fetchReleases() {
  // Fetch all releases (paginated) sorted by creation ascending
  const allReleases = [];
  let page = 1;
  while (true) {
    const url = `${CONFIG.GITHUB_API}/repos/${CONFIG.GITHUB_REPO}/releases` +
                `?per_page=100&page=${page}`;
    const batch = await fetchJSON(url);
    if (!batch.length) break;
    allReleases.push(...batch);
    page++;
  }
  // Sort by id ascending (creation order = simulation order)
  allReleases.sort((a, b) => a.id - b.id);
  return allReleases;
}

// ── Jira ──────────────────────────────────────────────────────────────────────

async function fetchStories() {
  const jql = `project = ${CONFIG.JIRA_PROJECT} AND issuetype = Story ORDER BY created ASC`;
  const fields = [
    'summary',
    CONFIG.FIELD_DEPLOYMENT_VERSION,
    CONFIG.FIELD_FIRST_COMMIT_DATE,
  ];
  return jiraSearchAll(jql, fields);
}

async function fetchIncidents() {
  const jql = `project = ${CONFIG.JIRA_PROJECT} AND issuetype = Incident ORDER BY created ASC`;
  const fields = [
    'summary',
    'description',
    CONFIG.FIELD_LINKED_RELEASE,
    CONFIG.FIELD_INCIDENT_SEVERITY,
  ];
  return jiraSearchAll(jql, fields);
}

// ── Description parser ────────────────────────────────────────────────────────
// Incidents store simulated dates in their description text:
//   SimulatedCreated: 2025-10-03T14:22:00Z
//   SimulatedResolved: 2025-10-04T01:22:00Z

function parseDescriptionDate(description, key) {
  // Walk Atlassian Document Format (ADF) content tree to extract plain text
  function extractText(node) {
    if (!node) return '';
    if (node.type === 'text') return node.text || '';
    return (node.content || []).map(extractText).join('');
  }
  const text = extractText(description);
  const match = text.match(new RegExp(`${key}:\\s*(\\S+)`));
  return match ? new Date(match[1]) : null;
}
