export const mockDashboardData = {
  siteStatus: 'LIVE',
  overallRiskScore: 72,
  activeAlerts: 3,
  nearMisses: 5,
  activeHazards: 7,
  recentEvents: [
    { id: 1, type: 'PPE Violation', severity: 'High Risk', time: '2 min ago', location: 'Zone A' },
    { id: 2, type: 'Hazard Detection', severity: 'Critical', time: '5 min ago', location: 'Zone B' },
    { id: 3, type: 'Safe Operation', severity: 'Safe', time: '8 min ago', location: 'Zone C' },
    { id: 4, type: 'Near Miss', severity: 'Caution', time: '12 min ago', location: 'Zone A' },
    { id: 5, type: 'Zone Entry', severity: 'Safe', time: '15 min ago', location: 'Zone D' },
  ]
};

export const mockIncidents = [
  { id: 'INC-001', time: '10:30 AM', severity: 'Critical', type: 'PPE Violation', location: 'Zone A', status: 'Active' },
  { id: 'INC-002', time: '10:15 AM', severity: 'High Risk', type: 'Hazard Detection', location: 'Zone B', status: 'Investigating' },
  { id: 'INC-003', time: '09:45 AM', severity: 'Caution', type: 'Near Miss', location: 'Zone C', status: 'Resolved' },
  { id: 'INC-004', time: '09:30 AM', severity: 'High Risk', type: 'PPE Violation', location: 'Zone A', status: 'Resolved' },
  { id: 'INC-005', time: '09:00 AM', severity: 'Safe', type: 'Routine Check', location: 'Zone D', status: 'Closed' },
];

export const mockAnalyticsData = {
  riskTrend: [65, 70, 68, 72, 75, 72, 70],
  incidents: 12,
  nearMisses: 8,
  ppeViolations: 5,
  commonHazards: [
    { type: 'Missing Helmet', count: 4 },
    { type: 'No Safety Vest', count: 3 },
    { type: 'Improper Footwear', count: 2 },
    { type: 'Zone Breach', count: 5 },
  ]
};
