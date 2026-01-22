import React from 'react';

const SpotlightCard = ({ icon: Icon, title, value, subtitle, gradient, iconColor }) => {
  return (
    <div className={`relative overflow-hidden rounded-2xl p-6 ${gradient} text-white shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1`}>
      <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-10 rounded-full -mr-16 -mt-16"></div>
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className={`w-12 h-12 ${iconColor} bg-opacity-20 rounded-xl flex items-center justify-center backdrop-blur-sm`}>
            <Icon size={24} className="text-white" />
          </div>
          <span className="text-sm opacity-90">{subtitle}</span>
        </div>
        <h3 className="text-3xl font-bold mb-1">{value}</h3>
        <p className="text-sm opacity-90">{title}</p>
      </div>
    </div>
  );
};

export default SpotlightCard;
