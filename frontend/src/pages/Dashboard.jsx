import React, { useState, useEffect } from 'react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import CCTVViewer from '../components/CCTVViewer';
import api from '../services/api';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processingStatus, setProcessingStatus] = useState(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const dashboardData = await api.getDashboard();
      setData(dashboardData);
    } catch (err) {
      setError('Failed to load dashboard data. Please check if the backend is running.');
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    
    // Set up polling for refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    
    // Poll processing status every 2 seconds
    const processingInterval = setInterval(async () => {
      try {
        const progressData = await api.getProgress();
        setProcessingStatus(progressData);
      } catch (err) {
        // Silently fail on processing status polling
        console.debug('Processing status polling error:', err);
      }
    }, 2000);
    
    return () => {
      clearInterval(interval);
      clearInterval(processingInterval);
    };
  }, []);

  const getSeverityVariant = (severity) => {
    const normalizedSeverity = severity?.toLowerCase() || '';
    if (normalizedSeverity.includes('critical')) return 'critical';
    if (normalizedSeverity.includes('high')) return 'high';
    if (normalizedSeverity.includes('caution') || normalizedSeverity.includes('medium')) return 'caution';
    if (normalizedSeverity.includes('safe') || normalizedSeverity.includes('low')) return 'safe';
    return 'default';
  };

  const getRiskColor = (score) => {
    if (score >= 80) return 'text-red-600';
    if (score >= 60) return 'text-orange-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <div className="animate-pulse bg-gray-200 h-8 w-24 rounded"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <div className="animate-pulse space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <button 
            onClick={fetchDashboardData}
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

  const { site_status, overall_risk_score, active_alerts, active_hazards, recent_events } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex items-center gap-4">
          <button 
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Refresh
          </button>
          <Badge variant={site_status === 'LIVE' ? 'safe' : 'default'}>{site_status}</Badge>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Overall Risk Score</p>
              <p className={`text-4xl font-bold ${getRiskColor(overall_risk_score)}`}>
                {overall_risk_score}/100
              </p>
            </div>
            <div className="text-3xl">📊</div>
          </div>
        </Card>

        {/* Processing Status Card */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Processing Status</p>
              <p className="text-2xl font-bold text-gray-900">
                {processingStatus?.status || 'Idle'}
              </p>
              {processingStatus?.status === 'processing' && (
                <p className="text-sm text-gray-500 mt-1">
                  {processingStatus.progress?.toFixed(1)}% complete
                </p>
              )}
            </div>
            <div className="text-3xl">
              {processingStatus?.status === 'processing' ? '⚙️' : 
               processingStatus?.status === 'completed' ? '✅' : 
               processingStatus?.status === 'failed' ? '❌' : '💤'}
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Active Alerts</p>
              <p className="text-4xl font-bold text-red-600">{active_alerts}</p>
            </div>
            <div className="text-3xl">🚨</div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Active Hazards</p>
              <p className="text-4xl font-bold text-orange-600">{active_hazards}</p>
            </div>
            <div className="text-3xl">⚡</div>
          </div>
        </Card>
      </div>

      {/* CCTV and Digital Twin */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="CCTV Feed">
          <CCTVViewer />
        </Card>

        <Card title="Digital Safety Twin">
          <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🏗️</div>
              <p className="text-gray-400 font-medium">Digital Safety Twin</p>
              <p className="text-gray-500 text-sm mt-2">Placeholder for future 3D visualization</p>
            </div>
          </div>
        </Card>

        <Card title="Digital Safety Twin">
          <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🏗️</div>
              <p className="text-gray-400 font-medium">Digital Safety Twin</p>
              <p className="text-gray-500 text-sm mt-2">Placeholder for future 3D visualization</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Events */}
      <Card title="Recent Safety Events">
        {recent_events && recent_events.length > 0 ? (
          <div className="space-y-3">
            {recent_events.map((event) => (
              <div key={event.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-4">
                  <Badge variant={getSeverityVariant(event.severity)}>{event.severity}</Badge>
                  <div>
                    <p className="font-medium text-gray-900">{event.type}</p>
                    <p className="text-sm text-gray-600">{event.location}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-500">{event.time}</p>
              </div>
            ))}
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

export default Dashboard;
