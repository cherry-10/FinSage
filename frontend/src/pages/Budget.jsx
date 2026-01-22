import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { budgetAPI, transactionAPI, expenseLimitAPI } from '../services/api';
import { PiggyBank, TrendingUp, Target, Sparkles, AlertCircle, CheckCircle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const Budget = () => {
  const { user } = useAuth();
  const { isDark } = useTheme();
  const [loading, setLoading] = useState(false);
  const [budgetPlan, setBudgetPlan] = useState(null);
  const [expenseLimit, setExpenseLimit] = useState(null);
  const [showLimitModal, setShowLimitModal] = useState(false);
  const [limitData, setLimitData] = useState({
    monthly_limit: '',
    target_savings: ''
  });

  useEffect(() => {
    fetchBudgetData();
  }, []);

  const fetchBudgetData = async () => {
    try {
      const [budgetResponse, limitResponse, transactionsResponse] = await Promise.all([
        budgetAPI.getAll().catch(() => ({ data: [] })),
        expenseLimitAPI.getLatest().catch(() => ({ data: null })),
        transactionAPI.getAll().catch(() => ({ data: [] }))
      ]);
      
      if (budgetResponse.data.length > 0) {
        const budgetItems = budgetResponse.data;
        const categoryMap = {};
        
        budgetItems.forEach(item => {
          if (!categoryMap[item.category]) {
            categoryMap[item.category] = {
              category: item.category,
              allocated: item.allocated_amount,
              spent: 0,
              remaining: item.allocated_amount
            };
          }
        });

        // Filter transactions for current month only
        const now = new Date();
        const currentMonth = now.getMonth();
        const currentYear = now.getFullYear();
        
        const expenseTransactions = transactionsResponse.data.filter(t => {
          if (t.transaction_type !== 'expense') return false;
          const transactionDate = new Date(t.transaction_date);
          return transactionDate.getMonth() === currentMonth && transactionDate.getFullYear() === currentYear;
        });
        
        expenseTransactions.forEach(t => {
          if (categoryMap[t.category]) {
            categoryMap[t.category].spent += t.amount;
            categoryMap[t.category].remaining = Math.max(0, categoryMap[t.category].allocated - categoryMap[t.category].spent);
          }
        });

        const categories = Object.values(categoryMap);
        const totalBudget = categories.reduce((sum, c) => sum + c.allocated, 0);
        const monthlySpent = categories.reduce((sum, c) => sum + c.spent, 0);
        const monthlyIncome = user?.annual_salary ? (parseFloat(user.annual_salary) / 12) : 50000;

        setBudgetPlan({
          total_income: monthlyIncome,
          total_budget: totalBudget,
          monthly_spent: monthlySpent,
          categories: categories,
          generated_at: new Date().toISOString()
        });
      }
      
      setExpenseLimit(limitResponse.data);
    } catch (error) {
      console.error('Failed to fetch budget data:', error);
    }
  };

  const generateIntelligentBudget = async () => {
    setLoading(true);
    try {
      // Get transactions to analyze spending patterns
      const transactionsResponse = await transactionAPI.getAll();
      const transactions = transactionsResponse.data.filter(t => t.transaction_type === 'expense');

      // Calculate category-wise spending
      const categorySpending = {};
      transactions.forEach(t => {
        categorySpending[t.category] = (categorySpending[t.category] || 0) + t.amount;
      });

      // Get monthly income
      const monthlyIncome = user?.annual_salary ? (parseFloat(user.annual_salary) / 12) : 50000;

      // Define priority categories with intelligent allocation
      const priorityCategories = {
        'Rent': { priority: 1, minPercent: 25, maxPercent: 35 },
        'Food': { priority: 1, minPercent: 15, maxPercent: 25 },
        'Bills': { priority: 1, minPercent: 10, maxPercent: 15 },
        'Transport': { priority: 2, minPercent: 8, maxPercent: 12 },
        'Healthcare': { priority: 1, minPercent: 5, maxPercent: 10 },
        'Education': { priority: 2, minPercent: 5, maxPercent: 15 },
        'Savings': { priority: 1, minPercent: 20, maxPercent: 30 },
        'Shopping': { priority: 3, minPercent: 5, maxPercent: 10 },
        'Entertainment': { priority: 3, minPercent: 3, maxPercent: 8 },
        'Other': { priority: 3, minPercent: 2, maxPercent: 5 }
      };

      // Calculate intelligent budget allocation
      const budgetAllocation = {};
      let totalAllocated = 0;

      // First, allocate to priority 1 categories based on past spending
      Object.entries(priorityCategories).forEach(([category, config]) => {
        if (config.priority === 1) {
          const pastSpending = categorySpending[category] || 0;
          const avgPercent = (config.minPercent + config.maxPercent) / 2;
          
          // If there's past spending, use it as a guide but cap it
          if (pastSpending > 0) {
            const pastPercent = (pastSpending / monthlyIncome) * 100;
            const allocatedPercent = Math.min(Math.max(pastPercent, config.minPercent), config.maxPercent);
            budgetAllocation[category] = (monthlyIncome * allocatedPercent) / 100;
          } else {
            budgetAllocation[category] = (monthlyIncome * config.minPercent) / 100;
          }
          totalAllocated += budgetAllocation[category];
        }
      });

      // Allocate to priority 2 categories
      Object.entries(priorityCategories).forEach(([category, config]) => {
        if (config.priority === 2) {
          const pastSpending = categorySpending[category] || 0;
          if (pastSpending > 0) {
            const pastPercent = (pastSpending / monthlyIncome) * 100;
            const allocatedPercent = Math.min(Math.max(pastPercent, config.minPercent), config.maxPercent);
            budgetAllocation[category] = (monthlyIncome * allocatedPercent) / 100;
          } else {
            budgetAllocation[category] = (monthlyIncome * config.minPercent) / 100;
          }
          totalAllocated += budgetAllocation[category];
        }
      });

      // Allocate remaining to priority 3 categories
      const remaining = monthlyIncome - totalAllocated;
      const priority3Categories = Object.entries(priorityCategories).filter(([_, config]) => config.priority === 3);
      
      priority3Categories.forEach(([category, config], index) => {
        const share = remaining / priority3Categories.length;
        const maxAllowed = (monthlyIncome * config.maxPercent) / 100;
        budgetAllocation[category] = Math.min(share, maxAllowed);
      });

      // Create budget plan
      const categories = Object.entries(budgetAllocation).map(([category, allocated]) => ({
        category,
        allocated: Math.round(allocated),
        spent: categorySpending[category] || 0,
        remaining: Math.max(0, Math.round(allocated) - (categorySpending[category] || 0))
      }));

      const totalBudget = categories.reduce((sum, c) => sum + c.allocated, 0);
      const totalSpent = categories.reduce((sum, c) => sum + c.spent, 0);

      const newBudget = {
        total_income: monthlyIncome,
        total_budget: totalBudget,
        total_spent: totalSpent,
        categories,
        generated_at: new Date().toISOString()
      };

      setBudgetPlan(newBudget);
      
      await budgetAPI.generate();
      await fetchBudgetData();
      
    } catch (error) {
      console.error('Failed to generate budget:', error);
      alert('Failed to generate budget. Please ensure you have set your income and expense limits.');
    } finally {
      setLoading(false);
    }
  };

  const handleSetLimit = async (e) => {
    e.preventDefault();
    try {
      await expenseLimitAPI.create({
        monthly_limit: parseFloat(limitData.monthly_limit),
        target_savings: parseFloat(limitData.target_savings)
      });
      setShowLimitModal(false);
      setLimitData({ monthly_limit: '', target_savings: '' });
      fetchBudgetData();
    } catch (error) {
      alert('Failed to set expense limit');
    }
  };

  const chartData = budgetPlan?.categories?.map(cat => ({
    name: cat.category,
    value: cat.allocated
  })) || [];

  const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className={`flex-1 ${isDark ? 'bg-gray-900' : 'bg-gray-50'} py-8`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="section-spacing">
            <h1 className="page-title">Budget Planning</h1>
            <p className="page-subtitle">AI-powered intelligent budget allocation</p>
          </div>

          {/* Action Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 section-spacing">
            {/* Generate Budget Card */}
            <div className={`${isDark ? 'bg-gradient-to-br from-primary-900 to-success-900' : 'bg-gradient-to-br from-primary-600 to-success-600'} rounded-2xl p-8 text-white shadow-xl`}>
              <div className="flex items-start space-x-4 mb-6">
                <div className="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Sparkles size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold mb-2">Intelligent Budget Generation</h3>
                  <p className="text-sm opacity-90">
                    Our AI analyzes your spending patterns and creates a need-based budget with priority allocation
                  </p>
                </div>
              </div>
              <button
                onClick={generateIntelligentBudget}
                disabled={loading}
                className="w-full bg-white text-primary-600 font-semibold py-3 px-6 rounded-lg hover:bg-opacity-90 transition-all disabled:opacity-50"
              >
                {loading ? 'Generating...' : 'Generate Smart Budget'}
              </button>
            </div>

            {/* Set Limits Card */}
            <div className={`${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-2xl p-8 border shadow-lg`}>
              <div className="flex items-start space-x-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Target size={24} className="text-white" />
                </div>
                <div>
                  <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-2`}>Expense Limits</h3>
                  <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    {expenseLimit 
                      ? `Limit: ₹${expenseLimit.monthly_limit?.toLocaleString('en-IN')} | Target: ₹${expenseLimit.target_savings?.toLocaleString('en-IN')}`
                      : 'Set your monthly spending limits and savings targets'
                    }
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowLimitModal(true)}
                className="w-full btn-primary"
              >
                {expenseLimit ? 'Update Limits' : 'Set Limits'}
              </button>
            </div>
          </div>

          {/* Budget Overview */}
          {budgetPlan && (
            <>
              {/* Summary Cards */}
              <div className="grid-kpi section-spacing">
                <div className={`kpi-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <p className={`card-label mb-2 ${isDark ? 'text-gray-300' : ''}`}>Monthly Income</p>
                  <p className={`card-value ${isDark ? 'text-white' : ''}`}>
                    ₹{budgetPlan.total_income?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </p>
                </div>

                <div className={`kpi-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <p className={`card-label mb-2 ${isDark ? 'text-gray-300' : ''}`}>Total Budget</p>
                  <p className={`card-value ${isDark ? 'text-white' : ''}`}>
                    ₹{budgetPlan.total_budget?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </p>
                </div>

                <div className={`kpi-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <p className={`card-label mb-2 ${isDark ? 'text-gray-300' : ''}`}>Monthly Spent</p>
                  <p className={`card-value ${isDark ? 'text-white' : ''}`}>
                    ₹{budgetPlan.monthly_spent?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </p>
                </div>

                <div className={`kpi-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <p className={`card-label mb-2 ${isDark ? 'text-gray-300' : ''}`}>Remaining</p>
                  <p className={`text-3xl font-bold ${budgetPlan.total_budget - budgetPlan.monthly_spent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ₹{(budgetPlan.total_budget - budgetPlan.monthly_spent).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </p>
                </div>
              </div>

              {/* Charts and Categories */}
              <div className="grid-charts section-spacing">
                {/* Pie Chart */}
                <div className={`chart-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <h3 className={`card-title mb-4 ${isDark ? 'text-white' : ''}`}>
                    Budget Distribution
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Category List */}
                <div className={`chart-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
                  <h3 className={`card-title mb-4 ${isDark ? 'text-white' : ''}`}>
                    Category Breakdown
                  </h3>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {budgetPlan.categories?.map((category, index) => {
                      const percentage = (category.spent / category.allocated) * 100;
                      const isOverBudget = percentage > 100;
                      
                      return (
                        <div key={index} className={`p-3 ${isDark ? 'bg-gray-700' : 'bg-gray-50'} rounded-lg`}>
                          <div className="flex items-center justify-between mb-2">
                            <span className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                              {category.category}
                            </span>
                            <span className={`text-sm font-semibold ${isOverBudget ? 'text-red-600' : 'text-green-600'}`}>
                              {percentage.toFixed(0)}%
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-sm mb-2">
                            <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>
                              ₹{category.spent.toLocaleString('en-IN')} / ₹{category.allocated.toLocaleString('en-IN')}
                            </span>
                            <span className={`font-medium ${isOverBudget ? 'text-red-600' : 'text-green-600'}`}>
                              ₹{category.remaining.toLocaleString('en-IN')} left
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-all ${isOverBudget ? 'bg-red-600' : 'bg-green-600'}`}
                              style={{ width: `${Math.min(percentage, 100)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* AI Insights */}
              <div className={`${isDark ? 'bg-blue-900 bg-opacity-20 border-blue-700' : 'bg-blue-50 border-blue-200'} rounded-2xl p-6 border`}>
                <div className="flex items-start space-x-3">
                  <AlertCircle className="text-blue-600 flex-shrink-0" size={24} />
                  <div>
                    <h3 className={`text-lg font-semibold ${isDark ? 'text-blue-200' : 'text-blue-900'} mb-2`}>
                      Smart Budget Allocation
                    </h3>
                    <p className={`${isDark ? 'text-blue-300' : 'text-blue-700'} mb-3`}>
                      This budget was intelligently generated based on your spending patterns. Priority categories like Rent, Food, and Bills 
                      receive higher allocations, while discretionary spending on Entertainment and Shopping is optimized based on your income.
                    </p>
                    <ul className={`space-y-2 ${isDark ? 'text-blue-300' : 'text-blue-700'}`}>
                      <li className="flex items-center space-x-2">
                        <CheckCircle size={16} className="text-green-600" />
                        <span>Essential expenses prioritized</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <CheckCircle size={16} className="text-green-600" />
                        <span>Savings target included</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <CheckCircle size={16} className="text-green-600" />
                        <span>Adaptive allocation based on past spending</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Set/Update Limits Modal */}
      {showLimitModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowLimitModal(false)}>
          <div className={`${isDark ? 'bg-gray-800' : 'bg-white'} rounded-2xl p-6 max-w-md w-full shadow-2xl`} onClick={(e) => e.stopPropagation()}>
            <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {expenseLimit ? 'Update' : 'Set'} Expense Limits
            </h2>
            <form onSubmit={handleSetLimit} className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  Monthly Spending Limit (₹)
                </label>
                <input
                  type="number"
                  value={limitData.monthly_limit}
                  onChange={(e) => setLimitData({ ...limitData, monthly_limit: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
                  placeholder="Enter monthly limit"
                  required
                  min="0"
                  step="0.01"
                />
                <p className={`text-xs mt-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                  Maximum amount you want to spend per month
                </p>
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  Target Savings (₹)
                </label>
                <input
                  type="number"
                  value={limitData.target_savings}
                  onChange={(e) => setLimitData({ ...limitData, target_savings: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
                  placeholder="Enter savings target"
                  required
                  min="0"
                  step="0.01"
                />
                <p className={`text-xs mt-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                  Amount you want to save each month
                </p>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowLimitModal(false)}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary"
                >
                  {expenseLimit ? 'Update' : 'Set'} Limits
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

export default Budget;
