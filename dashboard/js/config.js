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
  // We reconstruct simulated dates from release creation order using the same
  // formula as github_sim.py: date = SIM_START + index * DEPLOY_INTERVAL_DAYS
  SIM_START:            new Date('2025-09-01T09:00:00Z'),
  SIM_END:              new Date('2026-03-01T18:00:00Z'),
  DEPLOY_INTERVAL_DAYS: 3,   // 7 // DEPLOYS_PER_WEEK(2)
};
