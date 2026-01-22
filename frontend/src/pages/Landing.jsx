import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Shield, Zap, Brain, ArrowRight, DollarSign, PieChart, Bell } from 'lucide-react';

const Landing = () => {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Budgeting',
      description: 'Let our AI create personalized budget plans based on your income and savings goals.'
    },
    {
      icon: Shield,
      title: 'Anomaly Detection',
      description: 'Automatically detect unusual spending patterns and get instant alerts.'
    },
    {
      icon: TrendingUp,
      title: 'Smart Recommendations',
      description: 'Receive actionable insights to optimize your spending and maximize savings.'
    },
    {
      icon: PieChart,
      title: 'Visual Analytics',
      description: 'Track your finances with beautiful charts and real-time dashboards.'
    },
    {
      icon: Bell,
      title: 'Real-time Alerts',
      description: 'Stay informed about your spending with intelligent notifications.'
    },
    {
      icon: Zap,
      title: 'Instant Insights',
      description: 'Get immediate financial advice powered by advanced AI technology.'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-success-50">
      <nav className="bg-white/95 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16 sm:h-20">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-primary-500 via-primary-600 to-success-500 rounded-xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform">
                <DollarSign className="text-white" size={24} />
              </div>
              <span className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-primary-600 to-success-600 bg-clip-text text-transparent">
                FinSage
              </span>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <Link to="/login" className="text-gray-600 hover:text-gray-900 font-semibold text-sm sm:text-base transition-colors">
                Login
              </Link>
              <Link to="/signup" className="btn-primary text-sm sm:text-base px-4 sm:px-6 py-2 sm:py-2.5">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="relative overflow-hidden">
        <div 
          className="absolute inset-0 z-0 opacity-10"
          style={{
            backgroundImage: `url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40" fill="%230ea5e9" opacity="0.1"/></svg>')`,
            backgroundSize: '100px 100px'
          }}
        />
        
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 sm:pt-20 pb-16 sm:pb-24">
          <div className="text-center mb-12 sm:mb-16 animate-fadeIn">
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-4 sm:mb-6 leading-tight">
              Smart budgets.
              <br />
              <span className="bg-gradient-to-r from-primary-600 to-success-600 bg-clip-text text-transparent animate-pulse-slow">
                Smarter savings.
              </span>
            </h1>
            <p className="text-base sm:text-lg md:text-xl text-gray-600 mb-6 sm:mb-8 max-w-2xl mx-auto px-4">
              Take control of your finances with AI-powered insights. FinSage helps you budget smarter, 
              save more, and achieve your financial goals faster.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4 px-4">
              <Link to="/signup" className="btn-primary flex items-center justify-center space-x-2 text-base sm:text-lg px-6 sm:px-8 py-3 sm:py-4 w-full sm:w-auto">
                <span>Start Free Today</span>
                <ArrowRight size={20} />
              </Link>
              <Link to="/login" className="btn-secondary text-base sm:text-lg px-6 sm:px-8 py-3 sm:py-4 w-full sm:w-auto">
                Sign In
              </Link>
            </div>
          </div>

          <div className="bg-white rounded-2xl sm:rounded-3xl shadow-2xl p-4 sm:p-8 mb-12 sm:mb-20 border-2 border-gray-100 animate-scaleIn">
            <img 
              src="https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=1200&h=600&fit=crop" 
              alt="Financial Dashboard" 
              className="w-full h-48 sm:h-64 md:h-96 object-cover rounded-xl sm:rounded-2xl"
            />
          </div>

          <div className="mb-12 sm:mb-20">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center text-gray-900 mb-3 sm:mb-4 px-4">
              How AI Helps You Save Money
            </h2>
            <p className="text-center text-sm sm:text-base text-gray-600 mb-8 sm:mb-12 max-w-2xl mx-auto px-4">
              Our advanced AI analyzes your spending patterns, creates personalized budgets, 
              and provides actionable recommendations to help you reach your financial goals.
            </p>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 md:gap-8 px-4">
              {features.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div key={index} className="card hover:scale-105 animate-fadeIn" style={{animationDelay: `${index * 0.1}s`}}>
                    <div className="w-14 h-14 sm:w-16 sm:h-16 bg-gradient-to-br from-primary-100 to-success-100 rounded-xl flex items-center justify-center mb-4 transform hover:rotate-6 transition-transform">
                      <Icon className="text-primary-600" size={28} />
                    </div>
                    <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm sm:text-base text-gray-600">
                      {feature.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-gradient-to-r from-primary-600 to-success-600 rounded-2xl sm:rounded-3xl p-6 sm:p-12 text-center text-white shadow-2xl mx-4 sm:mx-0 animate-scaleIn">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3 sm:mb-4">Ready to Transform Your Finances?</h2>
            <p className="text-base sm:text-lg md:text-xl mb-6 sm:mb-8 opacity-90">
              Join thousands of users who are already saving smarter with FinSage.
            </p>
            <Link to="/signup" className="bg-white text-primary-600 px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-bold hover:bg-gray-100 transition-all transform hover:scale-105 inline-flex items-center space-x-2 shadow-lg">
              <span className="text-sm sm:text-base">Create Your Free Account</span>
              <ArrowRight size={20} />
            </Link>
          </div>
        </div>
      </div>

      <footer className="bg-gradient-to-br from-gray-900 to-gray-800 text-white py-8 sm:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="flex items-center justify-center space-x-2 sm:space-x-3 mb-3 sm:mb-4">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-primary-500 to-success-500 rounded-xl flex items-center justify-center shadow-lg">
              <DollarSign size={20} />
            </div>
            <span className="text-lg sm:text-xl font-bold">FinSage</span>
          </div>
          <p className="text-sm sm:text-base text-gray-400">
            © 2024 FinSage. Smart budgets. Smarter savings.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
