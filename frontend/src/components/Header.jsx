import React from 'react';

const Header = () => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-gray-900">Site Operations</h2>
          <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
            LIVE
          </span>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-gray-600">Current Time</p>
            <p className="text-lg font-semibold text-gray-900" id="current-time">
              {new Date().toLocaleTimeString()}
            </p>
          </div>
          <div className="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center text-white font-semibold">
            SG
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
