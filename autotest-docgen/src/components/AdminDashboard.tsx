import React, { useState, useEffect } from 'react';
import {
  Users, FolderOpen, Activity, Settings, LogOut,
  Shield, BarChart3, UserCheck, Plus,
  AlertCircle, CheckCircle, Moon, Sun, Menu, X, Lock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import extendedApiService from '../services/extendedApi.service';
import type { AdminUser, CreateReviewerRequest, OnlineUser } from '../services/extendedApi.service';
import apiService from '../services/api.service';
import './AdminDashboard.css';
import '../Dashboard-Modern.css';

interface SystemStats {
  totalUsers: number | string;
  totalProjects: number | string;
  activeUsers: number | string;
  systemHealth: 'good' | 'warning' | 'critical';
}

interface CreateReviewerForm {
  username: string;
  email: string;
  password: string;
  full_name: string;
  confirmPassword: string;
}

const getInitials = (name: string): string => {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
};

const AdminDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return (
      localStorage.getItem('adminTheme') === 'dark' ||
      (!localStorage.getItem('adminTheme') &&
        window.matchMedia('(prefers-color-scheme: dark)').matches)
    );
  });
  const [stats, setStats] = useState<SystemStats>({
    totalUsers: 0,
    totalProjects: 0,
    activeUsers: 0,
    systemHealth: 'good',
  });
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<OnlineUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'online' | 'projects'>('overview');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [allProjects, setAllProjects] = useState<any[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [showCreateReviewer, setShowCreateReviewer] = useState(false);
  const [createReviewerForm, setCreateReviewerForm] = useState<CreateReviewerForm>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    confirmPassword: '',
  });

  useEffect(() => {
    loadAdminData();
  }, []);

  // Cycle tab label during loading
  const [adLoadingLabel, setAdLoadingLabel] = React.useState('Overview');
  useEffect(() => {
    if (!isLoading) return;
    const labels = ['Overview', 'User Management', 'Online Users'];
    let idx = 1;
    const interval = setInterval(() => {
      setAdLoadingLabel(labels[idx % 3]);
      idx++;
    }, 2000);
    return () => clearInterval(interval);
  }, [isLoading]);

  useEffect(() => {
    const body = document.body;
    if (isDarkMode) {
      body.classList.add('ad-dark');
      body.classList.remove('ad-light');
      localStorage.setItem('adminTheme', 'dark');
    } else {
      body.classList.add('ad-light');
      body.classList.remove('ad-dark');
      localStorage.setItem('adminTheme', 'light');
    }
  }, [isDarkMode]);

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
        setOnlineUsers(onlineUsersData);
        setStats(prev => ({ ...prev, activeUsers: onlineUsersData.length }));
      } catch (error) {
        console.error('Failed to load online users:', error);
        setOnlineUsers([]);
      }

      try {
        const projectsData = await apiService.projects.list();
        setStats(prev => ({ ...prev, totalProjects: projectsData.count }));
      } catch (error) {
        console.error('Failed to load projects count:', error);
      }
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const loadAllProjects = async () => {
    setProjectsLoading(true);
    setProjectsError(null);
    try {
      const token = localStorage.getItem('access_token') || '';
      const res = await fetch('/api/upm/projects/', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      const list = Array.isArray(data) ? data : data.results || data.data || [];
      setAllProjects(list);
    } catch (err: any) {
      setProjectsError(err.message || 'Failed to load projects');
    } finally {
      setProjectsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'projects' && allProjects.length === 0 && !projectsLoading) {
      loadAllProjects();
    }
  }, [activeTab]);

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
      setCreateReviewerForm({ username: '', email: '', password: '', full_name: '', confirmPassword: '' });
      setShowCreateReviewer(false);
    } catch (error) {
      console.error('Failed to create reviewer:', error);
    }
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'good':     return 'text-green-600';
      case 'warning':  return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default:         return 'text-gray-600';
    }
  };

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'good':     return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'warning':  return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'critical': return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:         return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  const getHealthSubText = (health: string) => {
    switch (health) {
      case 'good':     return 'All systems operational';
      case 'warning':  return 'Some issues detected';
      case 'critical': return 'Immediate attention needed';
      default:         return 'Status unknown';
    }
  };

  if (isLoading) {
    const adTabData = [
      { icon: <BarChart3 />, label: 'Overview' },
      { icon: <Users />, label: 'User Management' },
      { icon: <Activity />, label: 'Online Users' },
    ];
    return (
      <div className={`ad-loading-screen ${isDarkMode ? 'ad-dark' : 'ad-light'}`}>
        <div className="ad-orbit-container">
          <div className="ad-center-glow" />
          {adTabData.map((tab, i) => (
            <div key={i} className="ad-orbit-icon">{tab.icon}</div>
          ))}
        </div>
        <div className="ad-tab-label"><span key={adLoadingLabel}>{adLoadingLabel}</span></div>
        <div className="ad-loading-text">
          <p className="ad-loading-title">Admin Dashboard</p>
          <p className="ad-loading-subtitle">
            Loading
            <span className="ad-loading-dot" />
            <span className="ad-loading-dot" />
            <span className="ad-loading-dot" />
          </p>
        </div>
        <div className="ad-loading-line" />
      </div>
    );
  }

  return (
    <div className={`ad-layout ${isDarkMode ? 'ad-dark' : 'ad-light'}${isSidebarOpen ? ' sidebar-open' : ''}`}>

      {/* ── Header ──────────────────────────────────────────────────── */}
      <header className="ad-topbar">
        <div className="ad-topbar-left">
          <button className="ad-sidebar-toggle" onClick={() => setIsSidebarOpen(o => !o)}>
            {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="ad-logo">
            <div className="ad-logo-icon"><Shield size={16} /></div>
            <span className="ad-logo-text">AutoTestDocGen</span>
          </div>
        </div>
        <div className="ad-topbar-right">
          <span className="ad-welcome">Welcome, <strong>{user?.username}</strong></span>
          <button onClick={() => setIsDarkMode(!isDarkMode)} className="unified-theme-toggle" title="Toggle theme">
            {isDarkMode ? <Sun width={16} height={16} style={{ color: '#f59e0b' }} /> : <Moon width={16} height={16} style={{ color: '#764ba2' }} />}
          </button>
        </div>
      </header>

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className={`ad-sidebar${isSidebarOpen ? ' open' : ' closed'}`}>
        <nav className="ad-sidebar-nav">
          <button onClick={() => setActiveTab('overview')} className={`ad-nav-item${activeTab === 'overview' ? ' active' : ''}`}>
            <BarChart3 size={18} /><span>Overview</span>
          </button>
          <button onClick={() => setActiveTab('users')} className={`ad-nav-item${activeTab === 'users' ? ' active' : ''}`}>
            <Users size={18} /><span>User Management</span>
            {adminUsers.length > 0 && <span className="ad-nav-badge">{adminUsers.length}</span>}
          </button>
          <button onClick={() => setActiveTab('online')} className={`ad-nav-item${activeTab === 'online' ? ' active' : ''}`}>
            <Activity size={18} /><span>Online Users</span>
            {onlineUsers.length > 0 && <span className="ad-nav-badge">{onlineUsers.length}</span>}
          </button>
          <button onClick={() => setActiveTab('projects')} className={`ad-nav-item${activeTab === 'projects' ? ' active' : ''}`}>
            <FolderOpen size={18} /><span>Project Management</span>
            {allProjects.length > 0 && <span className="ad-nav-badge">{allProjects.length}</span>}
          </button>
        </nav>

        <div className="ad-sidebar-footer">
          <div className="ad-user-profile">
            <div className="ad-user-avatar">{getInitials(user?.username || 'A')}</div>
            <div className="ad-user-details">
              <div className="ad-user-name">{user?.username || 'Admin'}</div>
              <div className="ad-user-role">Administrator</div>
            </div>
          </div>
          <div className="ad-sidebar-actions">
            <button onClick={() => setShowCreateReviewer(true)} className="ad-action-btn">
              <Plus size={15} /><span>Create Reviewer</span>
            </button>
            <button onClick={handleLogout} className="ad-action-btn ad-logout-btn">
              <LogOut size={15} /><span>Logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────── */}
      <main className={`ad-main${isSidebarOpen ? '' : ' sidebar-closed'}`}>

        {/* Overview tab */}
        {activeTab === 'overview' && (
          <>
            <div className="ad-kpi-grid">
              <div className="ad-stat ad-stat-card-enter">
                <div className="ad-stat-icon"><Users className="w-5 h-5" /></div>
                <p className="ad-stat-label">Total Users</p>
                <p className="ad-stat-value">{stats.totalUsers}</p>
                <p className="ad-stat-sub">Registered accounts</p>
              </div>
              <div className="ad-stat ad-stat-card-enter">
                <div className="ad-stat-icon"><FolderOpen className="w-5 h-5" /></div>
                <p className="ad-stat-label">Total Projects</p>
                <p className="ad-stat-value">{stats.totalProjects}</p>
                <p className="ad-stat-sub">All time projects</p>
              </div>
              <div className="ad-stat ad-stat-card-enter">
                <div className="ad-stat-icon"><UserCheck className="w-5 h-5" /></div>
                <p className="ad-stat-label">Active Users</p>
                <p className="ad-stat-value">{stats.activeUsers}</p>
                <p className="ad-stat-sub">Currently online</p>
              </div>
              <div className="ad-stat ad-stat-card-enter">
                <div className="ad-stat-icon">{getHealthIcon(stats.systemHealth)}</div>
                <p className="ad-stat-label">System Health</p>
                <p className={`ad-stat-value text-lg ${getHealthColor(stats.systemHealth)}`}>
                  {stats.systemHealth.charAt(0).toUpperCase() + stats.systemHealth.slice(1)}
                </p>
                <p className="ad-stat-sub">{getHealthSubText(stats.systemHealth)}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              <div className="lg:col-span-2">
                <div className="ad-card ad-anim-fadeup-1">
                  <div className="ad-card-header px-6 py-4 border-b flex items-center justify-between">
                    <h2 className="text-base font-semibold flex items-center gap-2">
                      <Users className="w-5 h-5" style={{ color: 'var(--ad-primary)' }} />
                      User Management
                    </h2>
                    <button onClick={() => setActiveTab('users')} className="ad-btn ad-btn-secondary" style={{ fontSize: '.75rem' }}>
                      View all
                    </button>
                  </div>
                  <div className="p-6">
                    {adminUsers.slice(0, 4).map(u => (
                      <div key={u.id} className="ad-user-preview-row">
                        <div className="ad-user-avatar">{getInitials(u.full_name || u.username || '?')}</div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p className="ad-user-name">{u.full_name || u.username}</p>
                          <p className="ad-user-email">{u.email}</p>
                        </div>
                        <span className={`ad-role-${(u.role_type || 'developer').toLowerCase()}`}>
                          {u.role_type || 'DEVELOPER'}
                        </span>
                        <span className={u.is_active ? 'ad-status-active' : 'ad-status-inactive'}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    ))}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                      <button className="ad-action-card" onClick={() => setActiveTab('users')}>
                        <div className="ad-action-card-icon"><Users className="w-4 h-4" /></div>
                        <p className="ad-action-card-label">Manage Users</p>
                        <p className="ad-action-card-sub">Activate, deactivate accounts</p>
                      </button>
                      <button className="ad-action-card" onClick={() => setShowCreateReviewer(true)}>
                        <div className="ad-action-card-icon"><Plus className="w-4 h-4" /></div>
                        <p className="ad-action-card-label">Create Reviewer</p>
                        <p className="ad-action-card-sub">Add a new reviewer account</p>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="ad-card ad-anim-fadeup-2">
                <div className="ad-card-header px-6 py-4 border-b flex items-center justify-between">
                  <h2 className="text-base font-semibold flex items-center gap-2">
                    <Activity className="w-5 h-5" style={{ color: 'var(--ad-primary)' }} />
                    Online
                  </h2>
                  <span className="ad-tab-badge">{onlineUsers.length}</span>
                </div>
                <div className="px-6 py-4">
                  {onlineUsers.length === 0 ? (
                    <p style={{ color: 'var(--ad-text-secondary)', fontSize: '.875rem', textAlign: 'center', padding: '1rem 0' }}>
                      No users online.
                    </p>
                  ) : (
                    onlineUsers.map((u, i) => (
                      <div key={i} className="ad-online-item">
                        <div className="ad-online-avatar">{getInitials(u.username || '?')}</div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p className="ad-online-name">{u.username}</p>
                          <p className="ad-online-sub">{u.full_name}</p>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '.25rem' }}>
                          <span className={`ad-role-${(u.role_type || 'developer').toLowerCase()}`}>
                            {u.role_type || 'DEV'}
                          </span>
                          <div className="ad-online-dot" />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="ad-card ad-anim-fadeup-3">
              <div className="ad-card-header px-6 py-4 border-b">
                <h2 className="text-base font-semibold flex items-center gap-2">
                  <FolderOpen className="w-5 h-5" style={{ color: 'var(--ad-primary)' }} />
                  Project Management
                </h2>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button className="ad-action-card" onClick={() => setActiveTab('projects')}>
                    <div className="ad-action-card-icon"><FolderOpen className="w-4 h-4" /></div>
                    <p className="ad-action-card-label">All Projects</p>
                    <p className="ad-action-card-sub">Browse & manage projects</p>
                  </button>
                  <button className="ad-action-card">
                    <div className="ad-action-card-icon"><BarChart3 className="w-4 h-4" /></div>
                    <p className="ad-action-card-label">Project Analytics</p>
                    <p className="ad-action-card-sub">View stats & reports</p>
                  </button>
                  <button className="ad-action-card">
                    <div className="ad-action-card-icon"><Settings className="w-4 h-4" /></div>
                    <p className="ad-action-card-label">System Settings</p>
                    <p className="ad-action-card-sub">Configure platform options</p>
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Users tab */}
        {activeTab === 'users' && (
          <div className="ad-card ad-anim-fadeup">
            <div className="ad-card-header px-6 py-4 border-b flex justify-between items-center">
              <h2 className="text-base font-semibold flex items-center gap-2">
                <Users className="w-5 h-5" style={{ color: 'var(--ad-primary)' }} />
                User Management
              </h2>
              <button onClick={() => setShowCreateReviewer(true)} className="ad-btn ad-btn-primary">
                <Plus className="w-4 h-4" /> Create Reviewer
              </button>
            </div>
            <div className="p-6">
              <div className="ad-table-wrap">
                <table className="ad-table">
                  <thead>
                    <tr>
                      <th>User</th><th>Role</th><th>Status</th><th>Last Seen</th><th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminUsers.map(adminUser => (
                      <tr key={adminUser.id}>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '.625rem' }}>
                            <div className="ad-user-avatar" style={{ width: '2rem', height: '2rem', fontSize: '.7rem' }}>
                              {getInitials(adminUser.full_name || adminUser.username || '?')}
                            </div>
                            <div>
                              <div style={{ fontWeight: 500, fontSize: '.8125rem' }}>{adminUser.full_name}</div>
                              <div style={{ fontSize: '.75rem', color: 'var(--ad-text-secondary)' }}>{adminUser.email}</div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className={`ad-role-${(adminUser.role_type || 'developer').toLowerCase()}`}>
                            {adminUser.role_type || 'DEVELOPER'}
                          </span>
                        </td>
                        <td>
                          <span className={adminUser.is_active ? 'ad-status-active' : 'ad-status-inactive'}>
                            {adminUser.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td style={{ color: 'var(--ad-text-secondary)', fontSize: '.8rem' }}>
                          {adminUser.last_seen ? new Date(adminUser.last_seen).toLocaleDateString() : 'Never'}
                        </td>
                        <td>
                          <button
                            onClick={() => handleToggleUserActive(adminUser.id)}
                            className={`ad-btn ${adminUser.is_active ? 'ad-btn-danger' : 'ad-btn-primary'}`}
                            style={{ fontSize: '.75rem', padding: '.35rem .7rem' }}
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

        {/* Online Users tab */}
        {activeTab === 'online' && (
          <div className="ad-card ad-anim-fadeup">
            <div className="ad-card-header px-6 py-4 border-b flex items-center justify-between">
              <h2 className="text-base font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5" style={{ color: 'var(--ad-primary)' }} />
                Online Users
              </h2>
              <span className="ad-tab-badge">{onlineUsers.length} online</span>
            </div>
            <div className="p-6">
              {onlineUsers.length === 0 ? (
                <p style={{ textAlign: 'center', color: 'var(--ad-text-secondary)', padding: '2rem 0' }}>
                  No users online.
                </p>
              ) : (
                onlineUsers.map((u, i) => (
                  <div key={i} className="ad-online-item">
                    <div className="ad-online-avatar">{getInitials(u.username || '?')}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p className="ad-online-name">{u.username}</p>
                      <p className="ad-online-sub">{u.full_name}</p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
                      <span className={`ad-role-${(u.role_type || 'developer').toLowerCase()}`}>
                        {u.role_type || 'DEV'}
                      </span>
                      {u.last_seen && (
                        <span style={{ fontSize: '.75rem', color: 'var(--ad-text-secondary)' }}>
                          {new Date(u.last_seen).toLocaleTimeString()}
                        </span>
                      )}
                      <div className="ad-online-dot" />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Projects tab */}
        {activeTab === 'projects' && (
          <div className="ad-card ad-anim-fadeup">
            <div className="ad-card-header px-6 py-4 border-b flex items-center justify-between">
              <h2 className="text-base font-semibold flex items-center gap-2">
                <FolderOpen className="w-5 h-5" style={{ color: 'var(--ad-primary)' }} />
                All Projects
                {allProjects.length > 0 && <span className="ad-tab-badge">{allProjects.length}</span>}
              </h2>
              <button
                onClick={loadAllProjects}
                className="ad-btn ad-btn-secondary"
                style={{ fontSize: '.75rem' }}
                disabled={projectsLoading}
              >
                {projectsLoading ? '...' : '↻ Refresh'}
              </button>
            </div>
            <div className="p-6">
              {projectsLoading && (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--ad-text-secondary)' }}>
                  <div className="ad-loading-dot" style={{ display: 'inline-block' }} /> Loading projects…
                </div>
              )}
              {!projectsLoading && projectsError && (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#ef4444' }}>
                  {projectsError}
                  <br />
                  <button onClick={loadAllProjects} className="ad-btn ad-btn-secondary" style={{ marginTop: '.75rem', fontSize: '.75rem' }}>
                    Retry
                  </button>
                </div>
              )}
              {!projectsLoading && !projectsError && allProjects.length === 0 && (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--ad-text-secondary)' }}>
                  No projects found.
                </div>
              )}
              {!projectsLoading && !projectsError && allProjects.length > 0 && (
                <div className="ad-table-wrap">
                  <table className="ad-table">
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Description</th>
                        <th>Owner</th>
                        <th>Created</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allProjects.map((p: any, i: number) => (
                        <tr key={p.id || p._id || i}>
                          <td style={{ fontWeight: 500 }}>{p.title || p.name || '—'}</td>
                          <td style={{ color: 'var(--ad-text-secondary)', fontSize: '.8rem', maxWidth: '220px' }}>
                            <span style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {p.description || '—'}
                            </span>
                          </td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
                              <div className="ad-online-avatar" style={{ width: '1.75rem', height: '1.75rem', fontSize: '.65rem' }}>
                                {getInitials(p.username || p.owner || 'U')}
                              </div>
                              <span style={{ fontSize: '.8125rem' }}>{p.username || p.owner || '—'}</span>
                            </div>
                          </td>
                          <td style={{ color: 'var(--ad-text-secondary)', fontSize: '.8rem', whiteSpace: 'nowrap' }}>
                            {p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}
                          </td>
                          <td>
                            <span className={p.is_active === false ? 'ad-status-inactive' : 'ad-status-active'}>
                              {p.is_active === false ? 'Inactive' : 'Active'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Create Reviewer Modal */}
        {showCreateReviewer && (
          <div className="ad-modal-overlay" onClick={() => setShowCreateReviewer(false)}>
            <div className="ad-modal" onClick={e => e.stopPropagation()}>
              <div className="ad-modal-header">
                <h3 className="text-base font-semibold flex items-center gap-2">
                  <Plus className="w-5 h-5" style={{ color: 'var(--ad-primary)' }} />
                  Create New Reviewer
                </h3>
              </div>
              <div className="ad-modal-body">
                <div className="space-y-4">
                  {(['username', 'email', 'full_name', 'password', 'confirmPassword'] as const).map(field => (
                    <div key={field} className="ad-form-group" style={{ marginBottom: 0 }}>
                      <label className="ad-form-label">
                        {field === 'confirmPassword' ? 'Confirm Password'
                          : field === 'full_name' ? 'Full Name'
                          : field.charAt(0).toUpperCase() + field.slice(1)}
                      </label>
                      <input
                        type={field.toLowerCase().includes('password') ? 'password' : field === 'email' ? 'email' : 'text'}
                        value={createReviewerForm[field]}
                        onChange={e => setCreateReviewerForm({ ...createReviewerForm, [field]: e.target.value })}
                        className="ad-form-input"
                        placeholder={field === 'confirmPassword' ? 'Re-enter password' : ''}
                      />
                    </div>
                  ))}
                </div>
              </div>
              <div className="ad-modal-footer">
                <button onClick={() => setShowCreateReviewer(false)} className="ad-btn ad-btn-secondary">
                  Cancel
                </button>
                <button onClick={handleCreateReviewer} className="ad-btn ad-btn-primary">
                  <Plus className="w-4 h-4" /> Create Reviewer
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminDashboard;
