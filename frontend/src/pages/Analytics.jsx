import React, { useState, useEffect } from 'react';
import Card from '../components/Card';
import api from '../services/api';

const Analytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);
      const stats = await api.getStats();
      setAnalyticsData(stats);
    } catch (err) {
      setError('Failed to load analytics data. Please check if the backend is running.');
      console.error('Analytics fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
    
    // Set up polling for refresh every 30 seconds
    const interval = setInterval(fetchAnalyticsData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
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
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <button 
            onClick={fetchAnalyticsData}
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

  const { total_events, violations_count, unique_workers_count, event_type_breakdown, severity_breakdown } = analyticsData;

  // Prepare common hazards from event type breakdown
  const commonHazards = Object.entries(event_type_breakdown || {})
    .map(([type, count]) => ({
      type: type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      count
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  const maxHazardCount = commonHazards.length > 0 ? Math.max(...commonHazards.map(h => h.count)) : 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Export Analytics
          </button>
          <button 
            onClick={fetchAnalyticsData}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Analytics Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Events</p>
              <p className="text-4xl font-bold text-red-600">{total_events}</p>
            </div>
            <div className="text-3xl">📊</div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">PPE Violations</p>
              <p className="text-4xl font-bold text-orange-600">{violations_count}</p>
            </div>
            <div className="text-3xl">🪖</div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Unique Workers</p>
              <p className="text-4xl font-bold text-blue-600">{unique_workers_count}</p>
            </div>
            <div className="text-3xl">👷</div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Avg Risk Score</p>
              <p className="text-4xl font-bold text-yellow-600">--</p>
            </div>
            <div className="text-3xl">📈</div>
          </div>
        </Card>
      </div>

      {/* Risk Trend Chart Placeholder */}
      <Card title="Risk Trend">
        <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-2">📈</div>
            <p className="text-gray-500 font-medium">Risk Trend Chart</p>
            <p className="text-gray-400 text-sm mt-1">Analytics data not yet available</p>
          </div>
        </div>
      </Card>

      {/* Common Hazards */}
      <Card title="Most Common Hazards">
        {commonHazards.length > 0 ? (
          <div className="space-y-4">
            {commonHazards.map((hazard, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-slate-800 rounded-full flex items-center justify-center text-white font-bold">
                    {index + 1}
                  </div>
                  <span className="font-medium text-gray-900">{hazard.type}</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${(hazard.count / maxHazardCount) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold text-gray-700">{hazard.count}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📋</div>
            <p className="text-gray-500">No hazard data available</p>
          </div>
        )}
      </Card>

      {/* Additional Analytics Placeholders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Incidents by Zone">
          <div className="h-48 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="text-3xl mb-2">🗺️</div>
              <p className="text-gray-500">Zone distribution chart</p>
              <p className="text-gray-400 text-sm mt-1">Analytics data not yet available</p>
            </div>
          </div>
        </Card>

        <Card title="PPE Compliance Rate">
          <div className="h-48 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="text-3xl mb-2">🪖</div>
              <p className="text-gray-500">Compliance rate visualization</p>
              <p className="text-gray-400 text-sm mt-1">Analytics data not yet available</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Analytics;
