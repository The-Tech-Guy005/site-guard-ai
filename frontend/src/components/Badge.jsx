import React from 'react';

const Badge = ({ children, variant = 'default' }) => {
  const variants = {
    default: 'bg-gray-100 text-gray-800',
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    caution: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    safe: 'bg-green-100 text-green-800 border-green-200',
    info: 'bg-blue-100 text-blue-800 border-blue-200',
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${variants[variant] || variants.default}`}>
      {children}
    </span>
  );
};

export default Badge;
