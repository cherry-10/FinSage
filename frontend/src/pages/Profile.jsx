import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { authAPI } from '../services/api';
import { User, Mail, Phone, DollarSign, Calendar, Camera, Settings, LogOut, Lock, Save, X, Edit, Shield, CreditCard, Activity, TrendingUp } from 'lucide-react';
import { format } from 'date-fns';

const Profile = () => {
  const { user, updateUser, logout } = useAuth();
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [formData, setFormData] = useState({
    name: user?.name || '',
    phone: user?.phone || '',
    annual_income: user?.annual_income || ''
  });
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [message, setMessage] = useState({ type: '', text: '' });

  const monthlySalary = formData.annual_income ? (parseFloat(formData.annual_income) / 12).toFixed(2) : '0.00';

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateUser({
        ...formData,
        annual_income: formData.annual_income ? parseFloat(formData.annual_income) : null
      });
      setEditing(false);
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update profile. Please try again.' });
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match!' });
      return;
    }
    try {
      await authAPI.changePassword({
        old_password: passwordData.old_password,
        new_password: passwordData.new_password
      });
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
      setMessage({ type: 'success', text: 'Password changed successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to change password' });
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleCancel = () => {
    setFormData({
      name: user?.name || '',
      phone: user?.phone || '',
      annual_income: user?.annual_income || ''
    });
    setEditing(false);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className={`flex-1 ${isDark ? 'bg-gray-900' : 'bg-gradient-to-br from-gray-50 via-primary-50/20 to-success-50/20'} py-6 sm:py-8 lg:py-12`}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-6 sm:mb-8">
            <h1 className={`text-3xl sm:text-4xl font-bold bg-gradient-to-r ${isDark ? 'from-primary-400 to-success-400' : 'from-primary-600 to-success-600'} bg-clip-text text-transparent`}>My Profile</h1>
            <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'} mt-2 text-sm sm:text-base`}>Manage your account and preferences</p>
          </div>

          {/* Message Alert */}
          {message.text && (
            <div className={`mb-6 p-4 rounded-xl shadow-lg animate-fadeIn ${message.type === 'success' ? 'bg-gradient-to-r from-green-50 to-green-100 text-green-800 border-2 border-green-300' : 'bg-gradient-to-r from-red-50 to-red-100 text-red-800 border-2 border-red-300'}`}>
              <div className="flex items-center space-x-2">
                <Shield size={20} />
                <span className="font-semibold">{message.text}</span>
              </div>
            </div>
          )}

          {/* Profile Header Card */}
          <div className={`${isDark ? 'bg-gradient-to-br from-gray-800 to-gray-900 border-gray-700' : 'bg-white border-gray-200'} rounded-3xl shadow-2xl p-6 sm:p-8 mb-6 border-2 overflow-hidden relative`}>
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-5">
              <div className="absolute inset-0" style={{
                backgroundImage: `radial-gradient(circle at 2px 2px, ${isDark ? '#fff' : '#000'} 1px, transparent 0)`,
                backgroundSize: '32px 32px'
              }}></div>
            </div>
            
            <div className="relative z-10">
              <div className="flex flex-col sm:flex-row items-center sm:items-start space-y-4 sm:space-y-0 sm:space-x-6 mb-6 pb-6 border-b ${isDark ? 'border-gray-700' : 'border-gray-200'}">
                <div className="relative group">
                  <div className="w-24 h-24 sm:w-28 sm:h-28 bg-gradient-to-br from-primary-500 via-primary-600 to-success-500 rounded-2xl flex items-center justify-center shadow-2xl transform group-hover:scale-105 transition-transform duration-300">
                    <User className="text-white" size={48} />
                  </div>
                  <button className="absolute bottom-0 right-0 w-10 h-10 bg-gradient-to-br from-white to-gray-100 rounded-xl shadow-xl flex items-center justify-center border-2 ${isDark ? 'border-gray-700' : 'border-gray-200'} hover:scale-110 transition-transform duration-300">
                    <Camera size={18} className={isDark ? 'text-gray-700' : 'text-gray-600'} />
                  </button>
                </div>
                <div className="flex-1 text-center sm:text-left">
                  <h2 className={`text-2xl sm:text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>{user?.name}</h2>
                  <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} flex items-center justify-center sm:justify-start space-x-2 mb-2`}>
                    <Mail size={16} />
                    <span>{user?.email}</span>
                  </p>
                  {user?.created_at && (
                    <div className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium ${isDark ? 'bg-gray-700 text-gray-300' : 'bg-gradient-to-r from-primary-50 to-success-50 text-primary-700 border border-primary-200'}`}>
                      <Calendar size={14} />
                      <span>Member since {format(new Date(user.created_at), 'MMMM yyyy')}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4 mb-6">
                <div className={`${isDark ? 'bg-gray-700/50' : 'bg-gradient-to-br from-primary-50 to-primary-100'} rounded-xl p-4 text-center transform hover:scale-105 transition-transform`}>
                  <Activity className={`${isDark ? 'text-primary-400' : 'text-primary-600'} mx-auto mb-2`} size={24} />
                  <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'} mb-1`}>Account Status</p>
                  <p className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Active</p>
                </div>
                <div className={`${isDark ? 'bg-gray-700/50' : 'bg-gradient-to-br from-success-50 to-success-100'} rounded-xl p-4 text-center transform hover:scale-105 transition-transform`}>
                  <TrendingUp className={`${isDark ? 'text-success-400' : 'text-success-600'} mx-auto mb-2`} size={24} />
                  <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'} mb-1`}>Plan</p>
                  <p className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Premium</p>
                </div>
                <div className={`${isDark ? 'bg-gray-700/50' : 'bg-gradient-to-br from-orange-50 to-orange-100'} rounded-xl p-4 text-center transform hover:scale-105 transition-transform col-span-2 sm:col-span-1`}>
                  <Shield className={`${isDark ? 'text-orange-400' : 'text-orange-600'} mx-auto mb-2`} size={24} />
                  <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'} mb-1`}>Security</p>
                  <p className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Protected</p>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex space-x-2 sm:space-x-4 mb-6 border-b ${isDark ? 'border-gray-700' : 'border-gray-200'}">
                <button
                  onClick={() => setActiveTab('profile')}
                  className={`pb-3 px-3 sm:px-6 font-semibold transition-all duration-300 relative ${
                    activeTab === 'profile'
                      ? `${isDark ? 'text-primary-400' : 'text-primary-600'}`
                      : isDark ? 'text-gray-400 hover:text-gray-300' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <User size={18} />
                    <span className="text-sm sm:text-base">Profile</span>
                  </div>
                  {activeTab === 'profile' && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-500 to-success-500 rounded-full"></div>
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('settings')}
                  className={`pb-3 px-3 sm:px-6 font-semibold transition-all duration-300 relative ${
                    activeTab === 'settings'
                      ? `${isDark ? 'text-primary-400' : 'text-primary-600'}`
                      : isDark ? 'text-gray-400 hover:text-gray-300' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Settings size={18} />
                    <span className="text-sm sm:text-base">Settings</span>
                  </div>
                  {activeTab === 'settings' && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-500 to-success-500 rounded-full"></div>
                  )}
                </button>
              </div>

              {/* Profile Tab */}
              {activeTab === 'profile' && (
                <>
                  {editing ? (
                    <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
                      <div>
                        <label className={`block text-sm font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                          Full Name
                        </label>
                        <div className="relative">
                          <User className={`absolute left-4 top-1/2 transform -translate-y-1/2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} size={20} />
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            required
                            className={`w-full pl-12 pr-4 py-3 border-2 rounded-xl focus:ring-2 focus:ring-primary-500 transition-all ${
                              isDark ? 'bg-gray-700 border-gray-600 text-white focus:border-primary-500' : 'bg-white border-gray-300 focus:border-primary-500'
                            }`}
                          />
                        </div>
                      </div>

                      <div>
                        <label className={`block text-sm font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                          Phone Number
                        </label>
                        <div className="relative">
                          <Phone className={`absolute left-4 top-1/2 transform -translate-y-1/2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} size={20} />
                          <input
                            type="tel"
                            value={formData.phone}
                            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                            required
                            className={`w-full pl-12 pr-4 py-3 border-2 rounded-xl focus:ring-2 focus:ring-primary-500 transition-all ${
                              isDark ? 'bg-gray-700 border-gray-600 text-white focus:border-primary-500' : 'bg-white border-gray-300 focus:border-primary-500'
                            }`}
                          />
                        </div>
                      </div>

                      <div>
                        <label className={`block text-sm font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                          Annual Salary (₹)
                        </label>
                        <div className="relative">
                          <DollarSign className={`absolute left-4 top-1/2 transform -translate-y-1/2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} size={20} />
                          <input
                            type="number"
                            value={formData.annual_income}
                            onChange={(e) => setFormData({ ...formData, annual_income: e.target.value })}
                            placeholder="Enter annual salary"
                            className={`w-full pl-12 pr-4 py-3 border-2 rounded-xl focus:ring-2 focus:ring-primary-500 transition-all ${
                              isDark ? 'bg-gray-700 border-gray-600 text-white focus:border-primary-500' : 'bg-white border-gray-300 focus:border-primary-500'
                            }`}
                          />
                        </div>
                        {formData.annual_income && (
                          <div className={`mt-3 p-3 rounded-xl ${isDark ? 'bg-gray-700' : 'bg-gradient-to-r from-primary-50 to-success-50'}`}>
                            <p className={`text-sm font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                              💰 Monthly Salary: ₹{monthlySalary}
                            </p>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3 pt-4">
                        <button type="submit" className="btn-primary flex items-center justify-center space-x-2 py-3 w-full sm:w-auto sm:px-8">
                          <Save size={20} />
                          <span className="font-semibold">Save Changes</span>
                        </button>
                        <button type="button" onClick={handleCancel} className="btn-secondary flex items-center justify-center space-x-2 py-3 w-full sm:w-auto sm:px-8">
                          <X size={20} />
                          <span className="font-semibold">Cancel</span>
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div className="space-y-3 sm:space-y-4">
                      <div className={`flex items-center justify-between p-4 sm:p-5 ${isDark ? 'bg-gray-700/50' : 'bg-gradient-to-r from-gray-50 to-gray-100'} rounded-xl border-2 ${isDark ? 'border-gray-600' : 'border-gray-200'} hover:shadow-lg transition-all`}>
                        <div className="flex items-center space-x-4">
                          <div className={`w-12 h-12 rounded-xl ${isDark ? 'bg-gray-600' : 'bg-white'} flex items-center justify-center`}>
                            <Mail className={isDark ? 'text-primary-400' : 'text-primary-600'} size={22} />
                          </div>
                          <div>
                            <p className={`text-xs font-semibold ${isDark ? 'text-gray-400' : 'text-gray-600'} uppercase tracking-wide`}>Email Address</p>
                            <p className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'} mt-0.5`}>{user?.email}</p>
                          </div>
                        </div>
                      </div>

                      <div className={`flex items-center justify-between p-4 sm:p-5 ${isDark ? 'bg-gray-700/50' : 'bg-gradient-to-r from-gray-50 to-gray-100'} rounded-xl border-2 ${isDark ? 'border-gray-600' : 'border-gray-200'} hover:shadow-lg transition-all`}>
                        <div className="flex items-center space-x-4">
                          <div className={`w-12 h-12 rounded-xl ${isDark ? 'bg-gray-600' : 'bg-white'} flex items-center justify-center`}>
                            <Phone className={isDark ? 'text-success-400' : 'text-success-600'} size={22} />
                          </div>
                          <div>
                            <p className={`text-xs font-semibold ${isDark ? 'text-gray-400' : 'text-gray-600'} uppercase tracking-wide`}>Phone Number</p>
                            <p className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'} mt-0.5`}>{user?.phone || 'Not set'}</p>
                          </div>
                        </div>
                      </div>

                      <div className={`flex items-center justify-between p-4 sm:p-5 ${isDark ? 'bg-gradient-to-r from-gray-700/50 to-gray-600/50' : 'bg-gradient-to-r from-primary-50 to-success-50'} rounded-xl border-2 ${isDark ? 'border-gray-600' : 'border-primary-200'} hover:shadow-lg transition-all`}>
                        <div className="flex items-center space-x-4">
                          <div className={`w-12 h-12 rounded-xl ${isDark ? 'bg-gray-600' : 'bg-white'} flex items-center justify-center`}>
                            <DollarSign className={isDark ? 'text-orange-400' : 'text-orange-600'} size={22} />
                          </div>
                          <div>
                            <p className={`text-xs font-semibold ${isDark ? 'text-gray-400' : 'text-gray-600'} uppercase tracking-wide`}>Annual Salary</p>
                            <p className={`font-bold text-lg ${isDark ? 'text-white' : 'text-gray-900'} mt-0.5`}>
                              {user?.annual_income ? `₹${parseFloat(user.annual_income).toLocaleString('en-IN')}` : 'Not set'}
                            </p>
                            {user?.annual_income && (
                              <p className={`text-sm font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'} mt-1`}>
                                💰 Monthly: ₹{(parseFloat(user.annual_income) / 12).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex justify-center mt-6">
                        <button onClick={() => setEditing(true)} className="btn-primary flex items-center justify-center space-x-2 py-3 text-base font-semibold px-8 w-full sm:w-auto">
                          <Edit size={20} />
                          <span>Edit Profile</span>
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Settings Tab */}
              {activeTab === 'settings' && (
                <div className="space-y-6">
                  {/* Change Password */}
                  <div>
                    <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-4 flex items-center space-x-2`}>
                      <Lock size={24} />
                      <span>Change Password</span>
                    </h3>
                    <form onSubmit={handlePasswordChange} className="space-y-4 sm:space-y-5">
                      <div>
                        <label className={`block text-sm font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                          Current Password
                        </label>
                        <div className="relative">
                          <Lock className={`absolute left-4 top-1/2 transform -translate-y-1/2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} size={20} />
                          <input
                            type="password"
                            value={passwordData.old_password}
                            onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                            required
                            className={`w-full pl-12 pr-4 py-3 border-2 rounded-xl focus:ring-2 focus:ring-primary-500 transition-all ${
                              isDark ? 'bg-gray-700 border-gray-600 text-white focus:border-primary-500' : 'bg-white border-gray-300 focus:border-primary-500'
                            }`}
                          />
                        </div>
                      </div>

                      <div>
                        <label className={`block text-sm font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                          New Password
                        </label>
                        <div className="relative">
                          <Lock className={`absolute left-4 top-1/2 transform -translate-y-1/2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} size={20} />
                          <input
                            type="password"
                            value={passwordData.new_password}
                            onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                            required
                            className={`w-full pl-12 pr-4 py-3 border-2 rounded-xl focus:ring-2 focus:ring-primary-500 transition-all ${
                              isDark ? 'bg-gray-700 border-gray-600 text-white focus:border-primary-500' : 'bg-white border-gray-300 focus:border-primary-500'
                            }`}
                          />
                        </div>
                      </div>

                      <div>
                        <label className={`block text-sm font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                          Confirm New Password
                        </label>
                        <div className="relative">
                          <Lock className={`absolute left-4 top-1/2 transform -translate-y-1/2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} size={20} />
                          <input
                            type="password"
                            value={passwordData.confirm_password}
                            onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                            required
                            className={`w-full pl-12 pr-4 py-3 border-2 rounded-xl focus:ring-2 focus:ring-primary-500 transition-all ${
                              isDark ? 'bg-gray-700 border-gray-600 text-white focus:border-primary-500' : 'bg-white border-gray-300 focus:border-primary-500'
                            }`}
                          />
                        </div>
                      </div>

                      <div className="flex justify-center">
                        <button type="submit" className="btn-primary py-3 font-semibold px-8 w-full sm:w-auto">
                          Update Password
                        </button>
                      </div>
                    </form>
                  </div>

                  {/* Logout Button */}
                  <div className={`pt-6 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'} flex justify-center`}>
                    <button
                      onClick={handleLogout}
                      className="flex items-center justify-center space-x-2 px-8 py-4 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl hover:from-red-700 hover:to-red-800 transition-all transform hover:scale-105 shadow-lg font-semibold w-full sm:w-auto"
                    >
                      <LogOut size={22} />
                      <span>Logout from Account</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Profile;
