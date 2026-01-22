import React from 'react';
import { Sparkles } from 'lucide-react';

const HeroSection = ({ userName }) => {
  const quotes = [
    "A penny saved is a penny earned.",
    "Don't save what is left after spending; spend what is left after saving.",
    "The habit of saving is itself an education; it fosters every virtue.",
    "Financial freedom is available to those who learn about it and work for it.",
    "Money is only a tool. It will take you wherever you wish, but it will not replace you as the driver."
  ];

  const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];

  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 p-8 mb-8 shadow-2xl">
      <div className="absolute inset-0 bg-black opacity-10"></div>
      <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full -mr-32 -mt-32"></div>
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-white opacity-5 rounded-full -ml-24 -mb-24"></div>
      
      <div className="relative z-10">
        <div className="flex items-center space-x-2 mb-4">
          <Sparkles className="text-yellow-300" size={24} />
          <span className="text-white text-sm font-medium">Financial Wisdom</span>
        </div>
        
        <h1 className="text-4xl font-bold text-white mb-3">
          Welcome back, {userName}! 👋
        </h1>
        
        <p className="text-white text-lg opacity-90 italic max-w-2xl">
          "{randomQuote}"
        </p>
        
        <div className="mt-6 flex items-center space-x-4">
          <div className="h-1 w-20 bg-white opacity-30 rounded-full"></div>
          <span className="text-white text-sm opacity-75">Your journey to financial freedom continues</span>
        </div>
      </div>
    </div>
  );
};

export default HeroSection;
