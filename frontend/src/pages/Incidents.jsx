import React, { useState, useEffect } from 'react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import api from '../services/api';

const Incidents = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      setError(null);
      const events = await api.getEvents();
      setIncidents(events);
    } catch (err) {
      setError('Failed to load incidents. Please check if the backend is running.');
      console.error('Incidents fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    
    // Set up polling for refresh every 30 seconds
    const interval = setInterval(fetchIncidents, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const getSeverityVariant = (severity) => {
    const normalizedSeverity = severity?.toLowerCase() || '';
    if (normalizedSeverity.includes('critical')) return 'critical';
    if (normalizedSeverity.includes('high')) return 'high';
    if (normalizedSeverity.includes('caution') || normalizedSeverity.includes('medium')) return 'caution';
    if (normalizedSeverity.includes('safe') || normalizedSeverity.includes('low')) return 'safe';
    return 'default';
  };

  const getStatusVariant = (status) => {
    const normalizedStatus = status?.toLowerCase() || '';
    if (normalizedStatus.includes('active')) return 'critical';
    if (normalizedStatus.includes('investigating')) return 'high';
    if (normalizedStatus.includes('resolved')) return 'safe';
    if (normalizedStatus.includes('closed')) return 'default';
    return 'default';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    // If timestamp is in seconds, convert to readable format
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
  };

  const handleExport = async () => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
                          (import.meta.env.DEV ? '' : 'http://127.0.0.1:8000');
      const response = await fetch(`${API_BASE_URL}/api/v1/reports/export`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'osha_compliance_report.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        console.error('Export failed');
      }
    } catch (err) {
      console.error('Export error:', err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Incidents</h1>
          <div className="animate-pulse bg-gray-200 h-8 w-24 rounded"></div>
        </div>
        <Card>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Incidents</h1>
          <button 
            onClick={fetchIncidents}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
        <Card>
          <div className="text-center py-8">
            <div className="text-4xl mb-4">⚠️</div>
            <p className="text-red-600 font-medium">{error}</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Incidents</h1>
        <div className="flex gap-2">
          <button 
            onClick={handleExport}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Export Report
          </button>
          <button 
            onClick={fetchIncidents}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      <Card>
        {incidents && incidents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Incident ID</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Time</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Severity</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Type</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Location</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Status</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((incident) => (
                  <tr key={incident.event_id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 font-medium text-gray-900">{incident.event_id}</td>
                    <td className="py-3 px-4 text-gray-600">{formatTimestamp(incident.timestamp_seconds)}</td>
                    <td className="py-3 px-4">
                      <Badge variant={getSeverityVariant(incident.severity)}>{incident.severity}</Badge>
                    </td>
                    <td className="py-3 px-4 text-gray-700">{incident.event_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                    <td className="py-3 px-4 text-gray-600">{incident.zone}</td>
                    <td className="py-3 px-4">
                      <Badge variant={getStatusVariant('Active')}>Active</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📋</div>
            <p className="text-gray-500">No incidents recorded</p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default Incidents;
