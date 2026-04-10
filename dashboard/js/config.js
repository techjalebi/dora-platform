// config.js — Dashboard configuration (no secrets stored here)
const CONFIG = {
  // GitHub public repo — no auth needed for read access
  GITHUB_REPO: 'techjalebi/dora-demo-app',
  GITHUB_API:  'https://api.github.com',

  // Jira calls go through the local proxy (handles CORS + Basic Auth)
  JIRA_PROXY: window.location.hostname === 'localhost'
    ? 'http://localhost:8080/jira'
    : 'https://dora.techjalebi.com/jira',
  JIRA_PROJECT: 'DORA',

  // Custom field IDs (set during Phase 1 setup)
  FIELD_DEPLOYMENT_VERSION: 'customfield_10039',
  FIELD_FIRST_COMMIT_DATE:  'customfield_10040',
  FIELD_INCIDENT_SEVERITY:  'customfield_10041',
  FIELD_LINKED_RELEASE:     'customfield_10042',

  // Simulated timeline reconstruction
  // GitHub release published_at timestamps are all "today" (can't be backdated).
  // Releases are distributed across months per MONTHLY_DEPLOY_COUNTS (must sum to
  // total releases). Evenly spaced within each month.
  SIM_START: new Date('2025-09-01T09:00:00Z'),
  SIM_END:   new Date('2026-03-01T18:00:00Z'),

  // Monthly deploy targets — change these to reshape the deployment frequency chart
  // Format: [year, month (0-based), count]
  MONTHLY_DEPLOY_COUNTS: [
    [2025,  8, 10],   // Sep 2025
    [2025,  9, 10],   // Oct 2025
    [2025, 10, 15],   // Nov 2025
    [2025, 11,  5],   // Dec 2025
    [2026,  0, 10],   // Jan 2026
    [2026,  1, 10],   // Feb 2026
  ],
};
