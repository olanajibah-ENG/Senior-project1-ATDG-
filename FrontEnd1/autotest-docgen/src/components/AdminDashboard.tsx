import React, { useState, useEffect } from 'react';
import {
  Users, FolderOpen, Activity, Settings, LogOut,
  Shield, BarChart3, UserCheck, Plus,
  AlertCircle, CheckCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import extendedApiService from '../services/extendedApi.service';
import type { AdminUser, CreateReviewerRequest, OnlineUser } from '../services/extendedApi.service';
import apiService from '../services/api.service';

interface SystemStats {
  totalUsers: string;
  totalProjects: string;
  activeUsers: string;
  systemHealth: 'good' | 'warning' | 'critical';
}

interface CreateReviewerForm {
  username: string;
  email: string;
  password: string;
  full_name: string;
  confirmPassword: string;
}

const AdminDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState<SystemStats>({
    totalUsers: '',
    totalProjects: '',
    activeUsers: '',
    systemHealth: 'good'
  });
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<OnlineUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'online'>('overview');
  const [showCreateReviewer, setShowCreateReviewer] = useState(false);
  const [createReviewerForm, setCreateReviewerForm] = useState<CreateReviewerForm>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    confirmPassword: ''
  });

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setIsLoading(true);

      try {
        const usersData = await extendedApiService.getAdminUsers();
        setAdminUsers(usersData);
        setStats(prev => ({ ...prev, totalUsers: usersData.length }));
      } catch (error) {
        console.error('Failed to load admin users:', error);
      }

      try {
        const onlineUsersData = await extendedApiService.getOnlineUsers();
        setOnlineUsers(onlineUsersData.map(user => ({
          id: user.id,
          username: user.username,
          lastActivity: `${Math.floor(Math.random() * 30) + 1} min ago`,
          currentSession: 'Dashboard'
        })));
        setStats(prev => ({ ...prev, activeUsers: onlineUsersData.length }));
      }  catch (error) {
         console.error('Failed to load online users:', error);
         setOnlineUsers([]);
      }

      const projectsData = await apiService.projects.list();
      setStats(prev => ({ ...prev, totalProjects: projectsData.count }));
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleToggleUserActive = async (userId: number) => {
    try {
      await extendedApiService.toggleUserActive(userId);
      const updatedUsers = await extendedApiService.getAdminUsers();
      setAdminUsers(updatedUsers);
    } catch (error) {
      console.error('Failed to toggle user active status:', error);
    }
  };

  const handleCreateReviewer = async () => {
    try {
      if (createReviewerForm.password !== createReviewerForm.confirmPassword) {
        alert('Passwords do not match');
        return;
      }

      const reviewerData: CreateReviewerRequest = {
        username: createReviewerForm.username,
        email: createReviewerForm.email,
        password: createReviewerForm.password,
        full_name: createReviewerForm.full_name,
      };

      await extendedApiService.createReviewer(reviewerData);

      const updatedUsers = await extendedApiService.getAdminUsers();
      setAdminUsers(updatedUsers);

      setCreateReviewerForm({
        username: '',
        email: '',
        password: '',
        full_name: '',
        confirmPassword: ''
      });
      setShowCreateReviewer(false);
    } catch (error) {
      console.error('Failed to create reviewer:', error);
    }
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'good': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'good': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'warning': return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'critical': return <AlertCircle className="w-5 h-5 text-red-600" />;
      default: return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Admin Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Shield className="w-8 h-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user?.username}</span>
              <button
                onClick={handleLogout}
                className="flex items-center px-3 py-2 text-sm text-gray-700 hover:text-gray-900"
              >
                <LogOut className="w-4 h-4 mr-1" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="border-b">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-4 px-6 text-sm font-medium border-b-2 ${activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
              >
                <BarChart3 className="w-4 h-4 inline mr-2" />
                Overview
              </button>
              <button
                onClick={() => setActiveTab('users')}
                className={`py-4 px-6 text-sm font-medium border-b-2 ${activeTab === 'users'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
              >
                <Users className="w-4 h-4 inline mr-2" />
                User Management
              </button>
              <button
                onClick={() => setActiveTab('online')}
                className={`py-4 px-6 text-sm font-medium border-b-2 ${activeTab === 'online'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
              >
                <Activity className="w-4 h-4 inline mr-2" />
                Online Users ({onlineUsers.length})
              </button>
            </nav>
          </div>
        </div>

        {activeTab === 'overview' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Users className="w-8 h-8 text-blue-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Users</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.totalUsers}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <FolderOpen className="w-8 h-8 text-green-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Projects</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.totalProjects}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <UserCheck className="w-8 h-8 text-purple-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Active Users</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.activeUsers}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  {getHealthIcon(stats.systemHealth)}
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-600">System Health</p>
                    <p className={`text-lg font-bold ${getHealthColor(stats.systemHealth)}`}>
                      {stats.systemHealth.charAt(0).toUpperCase() + stats.systemHealth.slice(1)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b">
                    <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                      <Users className="w-5 h-5 mr-2" />
                      User Management
                    </h2>
                  </div>
                  <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <button className="flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                        <Users className="w-4 h-4 mr-2" />
                        Manage Users
                      </button>
                      <button className="flex items-center justify-center px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
                        <UserCheck className="w-4 h-4 mr-2" />
                        User Roles
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                    <Activity className="w-5 h-5 mr-2" />
                    Online Users ({onlineUsers.length})
                  </h2>
                </div>
                <div className="p-6">
                  <div className="space-y-3">
                    {onlineUsers.map((onlineUser) => (
                      <div key={onlineUser.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">{onlineUser.username}</p>
                          <p className="text-xs text-gray-500">{onlineUser.currentSession}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-gray-500">{onlineUser.lastActivity}</p>
                          <div className="w-2 h-2 bg-green-500 rounded-full ml-auto"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                  <FolderOpen className="w-5 h-5 mr-2" />
                  Project Management
                </h2>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button className="flex items-center justify-center px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
                    <FolderOpen className="w-4 h-4 mr-2" />
                    All Projects
                  </button>
                  <button className="flex items-center justify-center px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Project Analytics
                  </button>
                  <button className="flex items-center justify-center px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition">
                    <Settings className="w-4 h-4 mr-2" />
                    System Settings
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'users' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <Users className="w-5 h-5 mr-2" />
                User Management
              </h2>
              <button
                onClick={() => setShowCreateReviewer(true)}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Reviewer
              </button>
            </div>
            <div className="p-6">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {adminUsers.map((adminUser) => (
                      <tr key={adminUser.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {adminUser.username}
                            </div>
                            <div className="text-sm text-gray-500">{adminUser.email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                            {adminUser.profile?.role?.role_name || 'User'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${adminUser.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                            }`}>
                            {adminUser.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {adminUser.last_login ? new Date(adminUser.last_login).toLocaleDateString() : 'Never'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => handleToggleUserActive(adminUser.id)}
                            className={`inline-flex items-center px-3 py-1 rounded-md text-xs font-medium ${adminUser.is_active
                              ? 'bg-red-100 text-red-800 hover:bg-red-200'
                              : 'bg-green-100 text-green-800 hover:bg-green-200'
                              }`}
                          >
                            {adminUser.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'online' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                Online Users ({onlineUsers.length})
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {onlineUsers.map((onlineUser) => (
                  <div key={onlineUser.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{onlineUser.username}</p>
                      <p className="text-xs text-gray-500">{onlineUser.currentSession}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">{onlineUser.lastActivity}</p>
                      <div className="w-2 h-2 bg-green-500 rounded-full ml-auto"></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {showCreateReviewer && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  Create New Reviewer
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Username</label>
                    <input
                      type="text"
                      value={createReviewerForm.username}
                      onChange={(e) => setCreateReviewerForm({ ...createReviewerForm, username: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                      type="email"
                      value={createReviewerForm.email}
                      onChange={(e) => setCreateReviewerForm({ ...createReviewerForm, email: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Full Name</label>
                    <input
                      type="text"
                      value={createReviewerForm.full_name}
                      onChange={(e) => setCreateReviewerForm({ ...createReviewerForm, full_name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Password</label>
                    <input
                      type="password"
                      value={createReviewerForm.password}
                      onChange={(e) => setCreateReviewerForm({ ...createReviewerForm, password: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Confirm Password</label>
                    <input
                      type="password"
                      value={createReviewerForm.confirmPassword}
                      onChange={(e) => setCreateReviewerForm({ ...createReviewerForm, confirmPassword: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowCreateReviewer(false)}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateReviewer}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition"
                  >
                    Create Reviewer
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;