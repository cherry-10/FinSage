import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { transactionAPI } from '../services/api';
import { Plus, Trash2, TrendingUp, TrendingDown, Filter, Calendar } from 'lucide-react';
import { format, startOfMonth, endOfMonth, subMonths } from 'date-fns';

const Transactions = () => {
  const { isDark } = useTheme();
  const { user } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filter, setFilter] = useState('this_month');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [formData, setFormData] = useState({
    category: '',
    amount: '',
    description: '',
    transaction_type: 'expense',
    date: format(new Date(), 'yyyy-MM-dd')
  });

  const expenseCategories = ['Food', 'Transport', 'Shopping', 'Entertainment', 'Bills', 'Rent', 'Healthcare', 'Education', 'Other'];
  const incomeCategories = ['Salary', 'Bonus', 'Incentives', 'Freelance', 'Investment', 'Gift', 'Other Income'];

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await transactionAPI.getAll();
      setTransactions(response.data);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await transactionAPI.create({
        ...formData,
        amount: parseFloat(formData.amount),
        transaction_date: formData.date
      });
      setShowModal(false);
      setFormData({
        category: '',
        amount: '',
        description: '',
        transaction_type: 'expense',
        date: format(new Date(), 'yyyy-MM-dd')
      });
      fetchTransactions();
    } catch (error) {
      alert('Failed to add transaction');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await transactionAPI.delete(id);
        fetchTransactions();
      } catch (error) {
        alert('Failed to delete transaction');
      }
    }
  };

  const getFilteredTransactions = () => {
    let filtered = [...transactions];

    // Date filter
    const now = new Date();
    const thisMonthStart = startOfMonth(now);
    const thisMonthEnd = endOfMonth(now);
    const lastMonthStart = startOfMonth(subMonths(now, 1));
    const lastMonthEnd = endOfMonth(subMonths(now, 1));

    if (filter === 'this_month') {
      filtered = filtered.filter(t => {
        const date = new Date(t.transaction_date);
        return date >= thisMonthStart && date <= thisMonthEnd;
      });
    } else if (filter === 'last_month') {
      filtered = filtered.filter(t => {
        const date = new Date(t.transaction_date);
        return date >= lastMonthStart && date <= lastMonthEnd;
      });
    }

    // Category filter
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(t => t.category === categoryFilter);
    }

    return filtered.sort((a, b) => new Date(b.transaction_date) - new Date(a.transaction_date));
  };

  const filteredTransactions = getFilteredTransactions();
  const totalExpenses = filteredTransactions.filter(t => t.transaction_type === 'expense').reduce((sum, t) => sum + t.amount, 0);
  
  // Total income derived ONLY from annual_salary / 12 (not from credit transactions)
  const monthlyIncome = user?.annual_salary ? user.annual_salary / 12 : 0;
  const totalIncome = monthlyIncome;
  const netBalance = totalIncome - totalExpenses;

  const allCategories = [...new Set(transactions.map(t => t.category))];

  if (loading) {
    return (
      <>
        <Navbar />
        <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-[#03045e]' : 'bg-gray-50'}`}>
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className={`flex-1 ${isDark ? 'bg-gray-900' : 'bg-gray-50'} py-8`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="section-spacing">
            <h1 className="page-title">Transactions</h1>
            <p className="page-subtitle">Track your income and expenses</p>
          </div>

          {/* Summary Cards */}
          <div className="grid-stats section-spacing">
            <div className={`stat-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
              <div className="flex items-center justify-between mb-2">
                <span className={`card-label ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Total Income</span>
                <TrendingUp className="text-green-600" size={20} />
              </div>
              <p className={`card-value ${isDark ? 'text-white' : 'text-gray-900'}`}>
                ₹{totalIncome.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </p>
            </div>

            <div className={`stat-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
              <div className="flex items-center justify-between mb-2">
                <span className={`card-label ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Total Expenses</span>
                <TrendingDown className="text-red-600" size={20} />
              </div>
              <p className={`card-value ${isDark ? 'text-white' : 'text-gray-900'}`}>
                ₹{totalExpenses.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </p>
            </div>

            <div className={`stat-card ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
              <div className="flex items-center justify-between mb-2">
                <span className={`card-label ${isDark ? 'text-gray-300' : ''}`}>Net Balance</span>
                <Calendar className={netBalance >= 0 ? 'text-green-600' : 'text-red-600'} size={20} />
              </div>
              <p className={`text-3xl font-bold ${netBalance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ₹{netBalance.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </p>
            </div>
          </div>

          {/* Filters and Add Button */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
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
                onClick={() => setFilter('all')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  filter === 'all'
                    ? 'bg-primary-600 text-white shadow-lg'
                    : isDark ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                All Time
              </button>

              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  isDark ? 'bg-gray-800 text-gray-300 border-gray-700' : 'bg-white text-gray-700 border-gray-300'
                } border`}
              >
                <option value="all">All Categories</option>
                {allCategories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setShowModal(true)}
              className="btn-primary flex items-center space-x-2"
            >
              <Plus size={20} />
              <span>Add Transaction</span>
            </button>
          </div>

          {/* Transactions List */}
          <div className={`card overflow-hidden ${isDark ? 'bg-gray-800 border-gray-700' : ''}`}>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className={`${isDark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                  <tr>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-500'} uppercase tracking-wider`}>
                      Date
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-500'} uppercase tracking-wider`}>
                      Category
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-500'} uppercase tracking-wider`}>
                      Description
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-500'} uppercase tracking-wider`}>
                      Type
                    </th>
                    <th className={`px-6 py-3 text-right text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-500'} uppercase tracking-wider`}>
                      Amount
                    </th>
                    <th className={`px-6 py-3 text-right text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-500'} uppercase tracking-wider`}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className={`${isDark ? 'bg-[#1f2937]' : 'bg-[#ffffff]'} divide-y ${isDark ? 'divide-gray-700' : 'divide-gray-200'}`}>
                  {filteredTransactions.length > 0 ? (
                    filteredTransactions.map((transaction) => (
                      <tr key={transaction.id} className={`${isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-50'} transition-colors`}>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDark ? 'text-gray-300' : 'text-gray-900'}`}>
                          {format(new Date(transaction.transaction_date), 'MMM dd, yyyy')}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDark ? 'text-gray-300' : 'text-gray-900'}`}>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            transaction.transaction_type === 'income'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {transaction.category}
                          </span>
                        </td>
                        <td className={`px-6 py-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                          {transaction.description || '-'}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDark ? 'text-gray-300' : 'text-gray-900'}`}>
                          <span className={`flex items-center space-x-1 ${
                            transaction.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {transaction.transaction_type === 'income' ? (
                              <TrendingUp size={16} />
                            ) : (
                              <TrendingDown size={16} />
                            )}
                            <span className="capitalize">{transaction.transaction_type}</span>
                          </span>
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-semibold ${
                          transaction.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {transaction.transaction_type === 'income' ? '+' : '-'}₹{transaction.amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                          <button
                            onClick={() => handleDelete(transaction.id)}
                            className="text-red-600 hover:text-red-800 transition-colors"
                          >
                            <Trash2 size={18} />
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className={`px-6 py-12 text-center ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                        No transactions found for the selected filters
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Add Transaction Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
          <div className={`${isDark ? 'bg-gray-800' : 'bg-white'} rounded-2xl p-6 max-w-md w-full shadow-2xl`} onClick={(e) => e.stopPropagation()}>
            <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Add Transaction
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  Type
                </label>
                <select
                  value={formData.transaction_type}
                  onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value, category: '' })}
                  className={`w-full px-4 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
                  required
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
                  required
                >
                  <option value="">Select Category</option>
                  {(formData.transaction_type === 'expense' ? expenseCategories : incomeCategories).map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  Amount (₹)
                </label>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
                  placeholder="Enter amount"
                  required
                  min="0"
                  step="0.01"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  Description
                </label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
                  placeholder="Enter description"
                  required
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  Date
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className={`w-full px-4 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
                  required
                />
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary"
                >
                  Add Transaction
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

export default Transactions;
