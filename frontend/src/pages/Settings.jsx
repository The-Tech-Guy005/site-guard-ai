import React from 'react';
import Card from '../components/Card';

const Settings = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          Save Changes
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Site Configuration */}
        <Card title="Site Configuration">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Site Name</label>
              <input 
                type="text" 
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Construction Site Alpha"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
              <input 
                type="text" 
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="123 Industrial Blvd, City"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Time Zone</label>
              <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                <option>UTC-8 (Pacific Time)</option>
                <option>UTC-5 (Eastern Time)</option>
                <option>UTC+0 (GMT)</option>
                <option>UTC+1 (Central European)</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Safety Zones */}
        <Card title="Safety Zones">
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Zone A - Excavation</p>
                <p className="text-sm text-gray-600">High risk area</p>
              </div>
              <button className="text-blue-600 hover:text-blue-800">Edit</button>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Zone B - Heavy Equipment</p>
                <p className="text-sm text-gray-600">Medium risk area</p>
              </div>
              <button className="text-blue-600 hover:text-blue-800">Edit</button>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Zone C - Assembly</p>
                <p className="text-sm text-gray-600">Low risk area</p>
              </div>
              <button className="text-blue-600 hover:text-blue-800">Edit</button>
            </div>
            <button className="w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-colors">
              + Add New Zone
            </button>
          </div>
        </Card>

        {/* Alert Preferences */}
        <Card title="Alert Preferences">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Critical Alerts</p>
                <p className="text-sm text-gray-600">Immediate notification for critical events</p>
              </div>
              <input type="checkbox" className="w-5 h-5 text-blue-600 rounded" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">High Risk Alerts</p>
                <p className="text-sm text-gray-600">Notification for high-risk events</p>
              </div>
              <input type="checkbox" className="w-5 h-5 text-blue-600 rounded" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Near Miss Alerts</p>
                <p className="text-sm text-gray-600">Notification for near-miss events</p>
              </div>
              <input type="checkbox" className="w-5 h-5 text-blue-600 rounded" />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Email Notifications</p>
                <p className="text-sm text-gray-600">Receive alerts via email</p>
              </div>
              <input type="checkbox" className="w-5 h-5 text-blue-600 rounded" defaultChecked />
            </div>
          </div>
        </Card>

        {/* Camera Configuration */}
        <Card title="Camera Configuration">
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Camera 1 - Main Entrance</p>
                <p className="text-sm text-gray-600">1920x1080 • 30fps • Online</p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">Active</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Camera 2 - Excavation Zone</p>
                <p className="text-sm text-gray-600">1920x1080 • 30fps • Online</p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">Active</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Camera 3 - Assembly Area</p>
                <p className="text-sm text-gray-600">1280x720 • 25fps • Offline</p>
              </div>
              <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded">Offline</span>
            </div>
            <button className="w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-colors">
              + Add New Camera
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Settings;
