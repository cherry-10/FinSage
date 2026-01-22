import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useTheme } from '../context/ThemeContext';
import { insightsAPI } from '../services/api';
import { Lightbulb, TrendingUp, AlertTriangle, Sparkles, ArrowRight, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';

const Insights = () => {
  const { isDark } = useTheme();
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    generateInsights();
  }, []);

  const generateInsights = async () => {
    setLoading(true);
    try {
      const response = await insightsAPI.get();
      setInsights(response.data);
    } catch (error) {
      console.error('Failed to generate insights:', error);
      setInsights({
        summary: "Unable to load insights. Please check your connection and try again.",
        recommendations: [{
          category: "Error",
          message: "Failed to fetch insights data. Please refresh the page.",
          type: "warning"
        }],
        anomalies: [],
        current_month_total: 0,
        last_month_total: 0,
        difference: 0,
        percent_change: 0
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen">
        <Navbar />
        <div className={`flex-1 ${isDark ? 'bg-gray-900' : 'bg-gray-50'} py-8`}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className={`flex-1 ${isDark ? 'bg-gray-900' : 'bg-gray-50'} py-8`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="section-spacing">
            <h1 className="page-title">AI Insights</h1>
            <p className="page-subtitle">Get intelligent analysis of your spending patterns</p>
          </div>

          {/* Insights Results - Always Show */}
          {insights && (
            <>
              {/* Summary Card */}
              <div className={`gradient-card section-spacing ${isDark ? 'from-primary-900 to-success-900' : ''}`}>
                <div className="flex items-start space-x-4">
                  <Lightbulb size={32} className="flex-shrink-0" />
                  <div>
                    <h3 className="text-2xl font-bold mb-3">AI Analysis Summary</h3>
                    <p className="text-lg leading-relaxed whitespace-pre-line">{insights.summary}</p>
                  </div>
                </div>
              </div>

              {/* Comparison Stats */}
              <div className="grid-stats section-spacing">
                <div className={`stat-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <p className={`card-label mb-2 ${isDark ? 'text-gray-300' : ''}`}>Last Month</p>
                  <p className={`card-value ${isDark ? 'text-white' : ''}`}>
                    ₹{(insights.last_month_total || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </p>
                </div>

                <div className={`stat-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <p className={`card-label mb-2 ${isDark ? 'text-gray-300' : ''}`}>This Month</p>
                  <p className={`card-value ${isDark ? 'text-white' : ''}`}>
                    ₹{(insights.current_month_total || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </p>
                </div>

                <div className={`stat-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <p className={`card-label mb-2 ${isDark ? 'text-gray-300' : ''}`}>Change</p>
                  <p className={`text-3xl font-bold ${(insights.difference || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {(insights.difference || 0) >= 0 ? '+' : ''}₹{Math.abs(insights.difference || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </p>
                  <p className={`text-sm font-semibold ${(insights.difference || 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {(insights.difference || 0) >= 0 ? '+' : ''}{(insights.percent_change || 0).toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Recommendations */}
              {insights.recommendations && insights.recommendations.length > 0 && (
                <div className={`card section-spacing ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <h3 className={`card-title mb-4 flex items-center space-x-2 ${isDark ? 'text-white' : ''}`}>
                    <TrendingUp size={24} />
                    <span>Recommendations</span>
                  </h3>
                  <div className="space-y-3">
                    {insights.recommendations.map((rec, index) => (
                      <div
                        key={index}
                        className={`p-4 rounded-lg border-l-4 ${
                          rec.type === 'warning'
                            ? isDark ? 'bg-orange-900 bg-opacity-20 border-orange-500' : 'bg-orange-50 border-orange-500'
                            : rec.type === 'success'
                            ? isDark ? 'bg-green-900 bg-opacity-20 border-green-500' : 'bg-green-50 border-green-500'
                            : isDark ? 'bg-blue-900 bg-opacity-20 border-blue-500' : 'bg-blue-50 border-blue-500'
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <AlertTriangle
                            size={20}
                            className={`flex-shrink-0 mt-0.5 ${
                              rec.type === 'warning'
                                ? 'text-orange-600'
                                : rec.type === 'success'
                                ? 'text-green-600'
                                : 'text-blue-600'
                            }`}
                          />
                          <div>
                            <p className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>{rec.category}</p>
                            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{rec.message}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Anomalies Section */}
          {insights?.anomalies && insights.anomalies.length > 0 && (
            <div className={`card section-spacing ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
              <h3 className={`card-title mb-4 flex items-center space-x-2 ${isDark ? 'text-white' : ''}`}>
                <AlertTriangle size={24} className="text-orange-600" />
                <span>Detected Anomalies</span>
              </h3>
              <div className="space-y-3">
                {insights.anomalies.map((anomaly, index) => (
                  <div key={index} className={`p-4 ${isDark ? 'bg-orange-900 bg-opacity-20' : 'bg-orange-50'} rounded-lg border-l-4 border-orange-500`}>
                    <p className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>{anomaly.category}</p>
                    <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{anomaly.description}</p>
                    <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mt-2`}>
                      Detected on {format(new Date(anomaly.detected_at), 'MMM dd, yyyy')}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Insights;
