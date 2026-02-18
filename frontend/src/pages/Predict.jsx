import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useTheme } from '../context/ThemeContext';
import axios from 'axios';
import { TrendingUp, AlertTriangle, Calendar, Activity, RefreshCw, BarChart2, PlusCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

const Predict = () => {
  const { isDark } = useTheme();
  const [loading, setLoading] = useState(true);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState('');
  const [userBudget, setUserBudget] = useState(null);

  useEffect(() => {
    fetchPrediction();
    fetchUserBudget();
  }, []);

  const fetchPrediction = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/predict-expense`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setPrediction(response.data);
    } catch (err) {
      console.error('Failed to fetch prediction:', err);
      setError(err.response?.data?.detail || 'Failed to generate expense prediction. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchUserBudget = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/budget/summary`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      if (response.data && response.data.total_allocated) {
        setUserBudget(response.data.total_allocated);
      }
    } catch (err) {
      console.error('Failed to fetch budget:', err);
    }
  };

  const prepareChartData = () => {
    if (!prediction || !prediction.historical_data) return [];

    const chartData = prediction.historical_data.map(item => ({
      month: item.month,
      actual: item.amount,
      predicted: null
    }));

    // Add prediction point
    chartData.push({
      month: prediction.predicted_month,
      actual: null,
      predicted: prediction.predicted_amount,
      lower: prediction.confidence_range.lower,
      upper: prediction.confidence_range.upper
    });

    return chartData;
  };

  const getInsightIcon = () => {
    if (!prediction || !prediction.insight) return <Activity className="text-blue-500" size={24} />;
    
    if (prediction.insight.includes('increase')) {
      return <TrendingUp className="text-red-500" size={24} />;
    } else if (prediction.insight.includes('decrease')) {
      return <TrendingUp className="text-green-500 transform rotate-180" size={24} />;
    }
    return <Activity className="text-blue-500" size={24} />;
  };

  const isBudgetExceeded = () => {
    return userBudget && prediction && prediction.predicted_amount > userBudget;
  };

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen">
        <Navbar />
        <div className={`flex-1 ${isDark ? 'bg-gray-900' : 'bg-gray-50'} py-8`}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
          </div>
        </div>
        <Footer />
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
            <div className="flex items-center justify-between">
              <div>
                <h1 className="page-title">Expense Prediction</h1>
                <p className="page-subtitle">AI-powered forecast of your next month expenses</p>
              </div>
              <button
                onClick={fetchPrediction}
                className="btn-secondary flex items-center space-x-2"
              >
                <RefreshCw size={18} />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {error && (
            <div className="section-spacing">
              <div className={`rounded-2xl border-2 border-dashed p-12 flex flex-col items-center justify-center text-center ${
                isDark ? 'border-gray-600 bg-gray-800/50' : 'border-gray-300 bg-gray-50'
              }`}>
                <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-5 ${
                  isDark ? 'bg-gray-700' : 'bg-primary-50'
                }`}>
                  <BarChart2 className={isDark ? 'text-gray-400' : 'text-primary-400'} size={40} />
                </div>
                <h3 className={`text-xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  No Prediction Data Yet
                </h3>
                <p className={`text-sm max-w-sm mb-6 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                  Start adding your daily expenses in Transactions. Once you have at least 1 month of data, we'll predict your next month's spending automatically.
                </p>
                <a
                  href="/transactions"
                  className="btn-primary flex items-center space-x-2 px-6 py-2.5"
                >
                  <PlusCircle size={18} />
                  <span>Add Transactions</span>
                </a>
              </div>
            </div>
          )}

          {prediction && (
            <>
              {/* Prediction Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 section-spacing">
                {/* Predicted Amount Card */}
                <div className={`stat-card ${isDark ? 'bg-gradient-to-br from-primary-900 to-primary-800 border-primary-700' : 'bg-gradient-to-br from-primary-50 to-primary-100 border-primary-200'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <p className={`card-label ${isDark ? 'text-primary-200' : 'text-primary-700'}`}>
                      Predicted Expense
                    </p>
                    <Calendar className={isDark ? 'text-primary-300' : 'text-primary-600'} size={20} />
                  </div>
                  <p className={`card-value ${isDark ? 'text-white' : 'text-primary-900'}`}>
                    ₹{prediction.predicted_amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </p>
                  <p className={`text-sm font-medium ${isDark ? 'text-primary-300' : 'text-primary-600'}`}>
                    {prediction.predicted_month}
                  </p>
                </div>

                {/* Confidence Range Card */}
                <div className={`stat-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <div className="flex items-center justify-between mb-2">
                    <p className={`card-label ${isDark ? 'text-gray-300' : ''}`}>Confidence Range</p>
                    <Activity className={isDark ? 'text-gray-400' : 'text-gray-600'} size={20} />
                  </div>
                  <div className="space-y-1">
                    <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      <span className="font-semibold">Lower:</span> ₹{prediction.confidence_range.lower.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </p>
                    <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      <span className="font-semibold">Upper:</span> ₹{prediction.confidence_range.upper.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>80% confidence interval</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'}`}>
                      {prediction.historical_data.length} month{prediction.historical_data.length !== 1 ? 's' : ''} of data
                    </span>
                  </div>
                </div>
              </div>

              {/* Budget Warning */}
              {isBudgetExceeded() && (
                <div className="section-spacing">
                  <div className={`p-4 rounded-lg border-2 flex items-start space-x-3 ${isDark ? 'bg-orange-900 bg-opacity-20 border-orange-500' : 'bg-orange-50 border-orange-300'}`}>
                    <AlertTriangle className="text-orange-600 flex-shrink-0 mt-0.5" size={24} />
                    <div>
                      <p className={`font-bold ${isDark ? 'text-orange-300' : 'text-orange-800'} mb-1`}>
                        Budget Alert!
                      </p>
                      <p className={`text-sm ${isDark ? 'text-orange-200' : 'text-orange-700'}`}>
                        Your predicted expense (₹{prediction.predicted_amount.toLocaleString('en-IN')}) exceeds your monthly budget 
                        (₹{userBudget.toLocaleString('en-IN')}) by ₹{(prediction.predicted_amount - userBudget).toLocaleString('en-IN')}. 
                        Consider reviewing your spending habits or adjusting your budget.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Insight Card */}
              <div className={`card section-spacing ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                <div className="flex items-start space-x-3">
                  {getInsightIcon()}
                  <div>
                    <h3 className={`card-title mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                      AI Insight
                    </h3>
                    <p className={`${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      {prediction.insight}
                    </p>
                  </div>
                </div>
              </div>

              {/* Expense Trend Chart */}
              {prediction.historical_data.length > 0 && (
                <div className={`card section-spacing ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <h3 className={`card-title mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    Expense Trend & Forecast
                  </h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={prepareChartData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                      <XAxis 
                        dataKey="month" 
                        stroke={isDark ? '#9ca3af' : '#6b7280'}
                        tick={{ fontSize: 12 }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis 
                        stroke={isDark ? '#9ca3af' : '#6b7280'}
                        tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: isDark ? '#1f2937' : '#ffffff',
                          border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                          borderRadius: '8px'
                        }}
                        formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, '']}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="actual"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={{ r: 4 }}
                        name="Actual Expenses"
                        connectNulls={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="predicted"
                        stroke="#10b981"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={{ r: 6, fill: '#10b981' }}
                        name="Predicted"
                        connectNulls={false}
                      />
                      {userBudget && (
                        <ReferenceLine
                          y={userBudget}
                          stroke="#ef4444"
                          strokeDasharray="3 3"
                          label={{
                            value: 'Budget Limit',
                            position: 'insideTopRight',
                            fill: '#ef4444',
                            fontSize: 12
                          }}
                        />
                      )}
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-0.5 bg-blue-500"></div>
                      <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>Actual</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-0.5 bg-green-500 border-dashed border-t-2 border-green-500"></div>
                      <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>Predicted</span>
                    </div>
                    {userBudget && (
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-0.5 bg-red-500 border-dashed border-t-2 border-red-500"></div>
                        <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>Budget Limit</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* No Data Message */}
              {prediction.historical_data.length === 0 && (
                <div className={`card section-spacing ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <div className="text-center py-12">
                    <Activity size={48} className={`mx-auto mb-4 ${isDark ? 'text-gray-600' : 'text-gray-400'}`} />
                    <p className={`text-lg font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                      No Historical Data Available
                    </p>
                    <p className={`${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                      Start adding expense transactions to see predictions and trends.
                    </p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Predict;
