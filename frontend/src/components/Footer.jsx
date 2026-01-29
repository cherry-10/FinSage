import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { DollarSign, Github, Twitter, Linkedin, Mail, Heart } from 'lucide-react';

const Footer = () => {
  const { isDark } = useTheme();
  const currentYear = new Date().getFullYear();

  return (
    <footer className={`${isDark ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} border-t mt-auto`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Section */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 via-primary-600 to-success-500 rounded-xl flex items-center justify-center shadow-lg">
                <DollarSign className="text-white" size={24} />
              </div>
              <span className={`text-xl font-bold bg-gradient-to-r ${isDark ? 'from-primary-400 to-success-400' : 'from-primary-600 to-success-600'} bg-clip-text text-transparent`}>
                FinSage
              </span>
            </div>
            <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} text-sm mb-4 max-w-md`}>
              AI-powered financial management platform helping you budget smarter, save more, and achieve your financial goals faster.
            </p>
            <div className="flex space-x-4">
              <a href="https://github.com/cherry-10/" target="_blank" rel="noopener noreferrer" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} transition-colors`}>
                <Github size={20} />
              </a>
              <a href="#" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} transition-colors`}>
                <Twitter size={20} />
              </a>
              <a href="https://www.linkedin.com/in/charan-teja-995a0a31a/" target="_blank" rel="noopener noreferrer" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} transition-colors`}>
                <Linkedin size={20} />
              </a>
              <a href="mailto:charanteja1039@gmail.com" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} transition-colors`}>
                <Mail size={20} />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className={`${isDark ? 'text-white' : 'text-gray-900'} font-semibold mb-4`}>Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <a href="/dashboard" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} text-sm transition-colors`}>
                  Dashboard
                </a>
              </li>
              <li>
                <a href="/transactions" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} text-sm transition-colors`}>
                  Transactions
                </a>
              </li>
              <li>
                <a href="/budget" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} text-sm transition-colors`}>
                  Budget
                </a>
              </li>
              <li>
                <a href="/insights" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} text-sm transition-colors`}>
                  AI Insights
                </a>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className={`${isDark ? 'text-white' : 'text-gray-900'} font-semibold mb-4`}>Support</h3>
            <ul className="space-y-2">
              <li>
                <a href="#" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} text-sm transition-colors`}>
                  Help Center
                </a>
              </li>
              <li>
                <a href="#" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} text-sm transition-colors`}>
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} text-sm transition-colors`}>
                  Terms of Service
                </a>
              </li>
              <li>
                <a href="#" className={`${isDark ? 'text-gray-400 hover:text-primary-400' : 'text-gray-600 hover:text-primary-600'} text-sm transition-colors`}>
                  Contact Us
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className={`${isDark ? 'border-gray-800' : 'border-gray-200'} border-t pt-8`}>
          <div className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
            <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} text-sm text-center sm:text-left`}>
              © {currentYear} FinSage. All rights reserved.
            </p>
            <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} text-sm flex items-center space-x-1`}>
              <span>Made with</span>
              <Heart size={16} className="text-red-500 fill-current" />
              <span>for smarter savings</span>
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
