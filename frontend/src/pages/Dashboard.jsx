import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { dashboardAPI, incomeAPI, transactionAPI } from '../services/api';
import { DollarSign, TrendingDown, TrendingUp, PiggyBank, AlertTriangle, ArrowRight, Plus, Sparkles } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { format, startOfMonth, endOfMonth, subMonths } from 'date-fns';

const FINANCIAL_QUOTES = [
  "Small savings today build big futures.",
  "Control your money, or it will control you.",
  "Every expense is a choice. Choose wisely.",
  "Financial freedom starts with awareness.",
  "A budget is telling your money where to go instead of wondering where it went.",
  "The best time to save was yesterday. The next best time is today.",
  "Invest in yourself. Your career is the engine of your wealth.",
  "Don't save what is left after spending; spend what is left after saving.",
  "Financial peace isn't the acquisition of stuff. It's learning to live on less than you make.",
  "The habit of saving is itself an education; it fosters every virtue, teaches self-denial.",
  "Money is a terrible master but an excellent servant.",
  "Wealth is not about having a lot of money; it's about having a lot of options."
];

const Dashboard = () => {
  const { user } = useAuth();
  const { isDark } = useTheme();
  const [stats, setStats] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('this_month');
  const [showIncomeModal, setShowIncomeModal] = useState(false);
  const [incomeAmount, setIncomeAmount] = useState('');
  const [quote, setQuote] = useState('');

  useEffect(() => {
    fetchDashboardStats();
    setQuote(FINANCIAL_QUOTES[Math.floor(Math.random() * FINANCIAL_QUOTES.length)]);
  }, [filter]);

  const fetchDashboardStats = async () => {
    setLoading(true);
    try {
      let period = 'current_month';
      if (filter === 'last_month') period = 'last_month';
      else if (filter === 'all_time') period = 'all_time';
      
      const [statsResponse, trendsResponse] = await Promise.all([
        dashboardAPI.getStats(period),
        dashboardAPI.getTrends(period)
      ]);
      setStats(statsResponse.data);
      setTrends(trendsResponse.data);
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddIncome = async (e) => {
    e.preventDefault();
    try {
      await incomeAPI.create({ monthly_income: parseFloat(incomeAmount) });
      setShowIncomeModal(false);
      setIncomeAmount('');
      fetchDashboardStats();
    } catch (error) {
      alert('Failed to add income');
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
        <Footer />
      </div>
    );
  }

  const totalIncome = stats?.total_income || 0;
  const totalExpenses = stats?.total_expenses || 0;
  const savings = stats?.savings || 0;
  const savingsPercentage = totalIncome > 0 ? ((savings / totalIncome) * 100).toFixed(1) : 0;

  const lineChartData = [
    { name: 'Last Month', expenses: stats?.last_month_expenses || 0, income: totalIncome },
    { name: 'This Month', expenses: stats?.this_month_expenses || 0, income: totalIncome }
  ];

  const categoryData = stats?.category_breakdown?.map(cat => ({
    name: cat.category,
    amount: cat.total
  })) || [];

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className={`flex-1 ${isDark ? 'bg-gray-900' : 'bg-gray-50'} py-8`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Hero Section */}
          <div className={`gradient-card section-spacing ${isDark ? 'from-primary-900 to-success-900' : ''}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Sparkles size={48} />
                <div>
                  <h2 className="text-4xl font-bold mb-2">Welcome back, {user?.name}!</h2>
                  <p className="text-xl font-medium italic">"{quote}"</p>
                </div>
              </div>
              <div className="hidden lg:block">
                <div className="w-32 h-32 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                  <DollarSign size={64} className="text-white" />
                </div>
              </div>
            </div>
          </div>

          {/* Filter Buttons */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setFilter('this_month')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  filter === 'this_month'
                    ? 'bg-primary-600 text-white shadow-lg'
                    : isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                This Month
              </button>
              <button
                onClick={() => setFilter('last_month')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  filter === 'last_month'
                    ? 'bg-primary-600 text-white shadow-lg'
                    : isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                Last Month
              </button>
              <button
                onClick={() => setFilter('all_time')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  filter === 'all_time'
                    ? 'bg-primary-600 text-white shadow-lg'
                    : isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                All Time
              </button>
            </div>
            <button
              onClick={() => setShowIncomeModal(true)}
              className="btn-primary flex items-center space-x-2"
            >
              <Plus size={20} />
              <span>Add Income</span>
            </button>
          </div>

          {/* Spotlight KPI Cards */}
          <div className="grid-kpi section-spacing">
            {/* Income Card */}
            <div className={`kpi-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="icon-container bg-gradient-to-br from-green-500 to-green-600">
                  <TrendingUp className="text-white" size={24} />
                </div>
                <span className={`card-label ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Income</span>
              </div>
              <h3 className={`card-value mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                ₹{totalIncome.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </h3>
              <p className={`text-sm font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                {user?.annual_salary ? 'From annual salary' : 'This month'}
              </p>
            </div>

            {/* Expenses Card */}
            <div className={`kpi-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="icon-container bg-gradient-to-br from-red-500 to-red-600">
                  <TrendingDown className="text-white" size={24} />
                </div>
                <span className={`card-label ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Expenses</span>
              </div>
              <h3 className={`card-value mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                ₹{totalExpenses.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </h3>
              <p className={`text-sm font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>This month</p>
            </div>

            {/* Savings Card */}
            <div className={`kpi-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="icon-container bg-gradient-to-br from-blue-500 to-blue-600">
                  <PiggyBank className="text-white" size={24} />
                </div>
                <span className={`card-label ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Savings</span>
              </div>
              <h3 className={`card-value mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                ₹{savings.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </h3>
              <p className={`text-sm font-semibold ${savings >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {savingsPercentage}% of income
              </p>
            </div>

            {/* Anomalies Card */}
            <div className={`kpi-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="icon-container bg-gradient-to-br from-orange-500 to-orange-600">
                  <AlertTriangle className="text-white" size={24} />
                </div>
                <span className={`card-label ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Alerts</span>
              </div>
              <h3 className={`card-value mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {stats?.anomaly_count || 0}
              </h3>
              <p className={`text-sm font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Anomalies detected</p>
            </div>
          </div>

          {/* Charts Section - Conditional based on filter */}
          {filter === 'all_time' ? (
            <div className="grid-charts section-spacing">
              {/* All Time Monthly Expenses Line Chart */}
              <div className={`chart-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                <h2 className={`card-title mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  All Time - Monthly Expenses
                </h2>
                {trends?.all_time_monthly_expenses && trends.all_time_monthly_expenses.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={trends.all_time_monthly_expenses}>
                      <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                      <XAxis dataKey="month" stroke={isDark ? '#9ca3af' : '#6b7280'} tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                      <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: isDark ? '#1f2937' : '#ffffff',
                          border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                          borderRadius: '8px'
                        }}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="total" stroke="#3b82f6" strokeWidth={3} name="Expenses" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-[300px]">
                    <p className={`${isDark ? 'text-gray-400' : 'text-gray-500'} text-center`}>
                      No expense data available. Start adding transactions to see your spending trends.
                    </p>
                  </div>
                )}
              </div>

              {/* All Time Monthly Savings Bar Chart */}
              <div className={`chart-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                <h2 className={`card-title mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  All Time - Monthly Savings
                </h2>
                {trends?.all_time_monthly_savings && trends.all_time_monthly_savings.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={trends.all_time_monthly_savings}>
                      <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                      <XAxis dataKey="month" stroke={isDark ? '#9ca3af' : '#6b7280'} tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                      <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: isDark ? '#1f2937' : '#ffffff',
                          border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                          borderRadius: '8px'
                        }}
                      />
                      <Legend />
                      <Bar dataKey="savings" fill="#10b981" radius={[8, 8, 0, 0]} name="Savings" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-[300px]">
                    <p className={`${isDark ? 'text-gray-400' : 'text-gray-500'} text-center`}>
                      No savings data available. Start adding transactions to track your savings.
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="grid-charts section-spacing">
              {/* 1. This Month Daily Trend */}
              <div className={`chart-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                <h2 className={`card-title mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  This Month - Daily Expenses
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trends?.this_month_daily || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                    <XAxis dataKey="date" stroke={isDark ? '#9ca3af' : '#6b7280'} tick={{ fontSize: 10 }} />
                    <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: isDark ? '#1f2937' : '#ffffff',
                        border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="total" stroke="#3b82f6" strokeWidth={3} name="Expenses" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* 2. Last Month Daily Trend */}
              <div className={`chart-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                <h2 className={`card-title mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  Last Month - Daily Expenses
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trends?.last_month_daily || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                    <XAxis dataKey="date" stroke={isDark ? '#9ca3af' : '#6b7280'} tick={{ fontSize: 10 }} />
                    <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: isDark ? '#1f2937' : '#ffffff',
                        border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="total" stroke="#ef4444" strokeWidth={3} name="Expenses" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* 3. This Month Category Expenses */}
              <div className={`chart-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                <h2 className={`card-title mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  This Month - Category Breakdown
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trends?.this_month_categories || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                    <XAxis dataKey="category" stroke={isDark ? '#9ca3af' : '#6b7280'} tick={{ fontSize: 10 }} />
                    <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: isDark ? '#1f2937' : '#ffffff',
                        border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Bar dataKey="total" fill="#10b981" radius={[8, 8, 0, 0]} name="Amount" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* 4. Last Month Category Expenses */}
              <div className={`chart-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                <h2 className={`card-title mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  Last Month - Category Breakdown
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trends?.last_month_categories || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                    <XAxis dataKey="category" stroke={isDark ? '#9ca3af' : '#6b7280'} tick={{ fontSize: 10 }} />
                    <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: isDark ? '#1f2937' : '#ffffff',
                        border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Bar dataKey="total" fill="#f59e0b" radius={[8, 8, 0, 0]} name="Amount" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Recent Transactions */}
          <div className={`card section-spacing ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className={`card-title ${isDark ? 'text-white' : ''}`}>Recent Transactions</h2>
              <Link to="/transactions" className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center">
                View All
                <ArrowRight size={16} className="ml-1" />
              </Link>
            </div>
            <div className="space-y-3">
              {stats?.recent_transactions?.length > 0 ? (
                stats.recent_transactions.map((transaction) => (
                  <div key={transaction.id} className={`flex items-center justify-between p-4 ${isDark ? 'bg-gray-700' : 'bg-gray-50'} rounded-lg`}>
                    <div>
                      <p className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>{transaction.category}</p>
                      <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                        {format(new Date(transaction.transaction_date), 'MMM dd, yyyy')}
                      </p>
                    </div>
                    <span className={`text-lg font-semibold ${transaction.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                      {transaction.transaction_type === 'income' ? '+' : '-'}₹{transaction.amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </span>
                  </div>
                ))
              ) : (
                <p className={`${isDark ? 'text-gray-400' : 'text-gray-500'} text-center py-8`}>No transactions yet</p>
              )}
            </div>
          </div>

          {/* Anomaly Alert */}
          {stats?.anomaly_count > 0 && (
            <div className={`mt-6 ${isDark ? 'bg-orange-900 border-orange-700' : 'bg-orange-50 border-orange-200'} rounded-2xl p-6 border`}>
              <div className="flex items-start space-x-3">
                <AlertTriangle className="text-orange-600 flex-shrink-0" size={24} />
                <div className="flex-1">
                  <h3 className={`text-lg font-semibold ${isDark ? 'text-orange-200' : 'text-orange-900'} mb-1`}>
                    Anomalies Detected
                  </h3>
                  <p className={`${isDark ? 'text-orange-300' : 'text-orange-700'} mb-3`}>
                    We've detected {stats.anomaly_count} spending anomalies that need your attention.
                  </p>
                  <Link to="/insights" className="btn-primary inline-flex items-center space-x-2">
                    <span>View AI Insights</span>
                    <ArrowRight size={16} />
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add Income Modal */}
      {showIncomeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={(e) => e.stopPropagation()}>
          <div className={`${isDark ? 'bg-gray-800' : 'bg-white'} rounded-2xl p-6 max-w-md w-full shadow-2xl`} onClick={(e) => e.stopPropagation()}>
            <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Add Monthly Income
            </h2>
            <form onSubmit={handleAddIncome} className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  Monthly Income (₹)
                </label>
                <input
                  type="number"
                  value={incomeAmount}
                  onChange={(e) => setIncomeAmount(e.target.value)}
                  className={`w-full px-4 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
                  placeholder="Enter your monthly income"
                  required
                  min="0"
                  step="0.01"
                />
                <p className={`text-xs mt-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                  This will be used to calculate your budget and savings
                </p>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowIncomeModal(false)}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary"
                >
                  Add Income
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
};

export default Dashboard;
