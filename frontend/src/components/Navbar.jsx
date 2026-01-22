import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { LayoutDashboard, Receipt, PiggyBank, Lightbulb, Sun, Moon, User, Menu, X } from 'lucide-react';

const Navbar = () => {
  const { user } = useAuth();
  const location = useLocation();
  const { isDark, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/transactions', icon: Receipt, label: 'Transactions' },
    { path: '/budget', icon: PiggyBank, label: 'Budget' },
    { path: '/insights', icon: Lightbulb, label: 'AI Insights' },
  ];

  return (
    <nav className={`${isDark ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-gray-200 shadow-sm'} border-b sticky top-0 z-50 backdrop-blur-xl`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center space-x-2 z-10">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 via-primary-600 to-success-500 rounded-xl flex items-center justify-center shadow-lg transform hover:scale-105 transition-transform">
              <span className="text-white font-bold text-xl">F</span>
            </div>
            <span className={`text-xl font-bold bg-gradient-to-r ${isDark ? 'from-primary-400 to-success-400' : 'from-primary-600 to-success-600'} bg-clip-text text-transparent`}>FinSage</span>
          </Link>
          
          {/* Desktop Navigation - Centered Pill-style */}
          <div className="absolute left-1/2 transform -translate-x-1/2 hidden lg:flex items-center ${isDark ? 'bg-gray-800/80' : 'bg-gray-50/80'} backdrop-blur-md rounded-full p-1.5 border ${isDark ? 'border-gray-700' : 'border-gray-200'} shadow-lg">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-5 py-2.5 rounded-full transition-all duration-300 ${
                    isActive
                      ? `${isDark ? 'bg-gradient-to-r from-primary-600 to-success-600' : 'bg-gradient-to-r from-primary-500 to-success-500'} text-white shadow-lg transform scale-105`
                      : isDark ? 'text-gray-300 hover:text-white hover:bg-gray-700/50' : 'text-gray-600 hover:text-gray-900 hover:bg-white/80'
                  }`}
                >
                  <Icon size={18} />
                  <span className="text-sm font-semibold">{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className={`p-2.5 rounded-xl transition-all duration-300 transform hover:scale-110 ${
                isDark ? 'bg-gray-800 text-yellow-400 hover:bg-gray-700 shadow-lg' : 'bg-gradient-to-br from-gray-50 to-gray-100 text-gray-700 hover:from-gray-100 hover:to-gray-200 shadow-md border border-gray-200'
              }`}
              aria-label="Toggle theme"
            >
              {isDark ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            {/* Profile Icon */}
            <Link
              to="/profile"
              className={`p-2.5 rounded-xl transition-all duration-300 transform hover:scale-110 ${
                isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white shadow-lg' : 'bg-gradient-to-br from-gray-50 to-gray-100 text-gray-700 hover:from-primary-50 hover:to-success-50 hover:text-primary-600 shadow-md border border-gray-200'
              }`}
              aria-label="Profile"
              title="Profile"
            >
              <User size={20} />
            </Link>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={`lg:hidden p-2.5 rounded-xl transition-all duration-300 ${
                isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-gradient-to-br from-gray-50 to-gray-100 text-gray-700 hover:from-gray-100 hover:to-gray-200 shadow-md border border-gray-200'
              }`}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className={`lg:hidden py-4 border-t ${isDark ? 'border-gray-700 bg-gray-900' : 'border-gray-200 bg-white'} animate-fadeIn`}>
            <div className="space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                      isActive
                        ? `${isDark ? 'bg-gradient-to-r from-primary-600 to-success-600' : 'bg-gradient-to-r from-primary-500 to-success-500'} text-white shadow-lg`
                        : isDark ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icon size={20} />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
