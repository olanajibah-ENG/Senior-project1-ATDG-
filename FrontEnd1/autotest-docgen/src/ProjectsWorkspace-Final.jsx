import React from 'react';
import '../styles/Dashboard.css';
import '../styles/ProjectsWorkspace-Enhanced.css';

const ProjectsWorkspace = () => {
  return (
    <div className="dashboard light">
      {/* Enhanced Projects Workspace Header */}
      <header className="projects-workspace-header">
        <h1 className="projects-workspace-title">Projects Workspace</h1>
        <p className="projects-workspace-subtitle">
          Organize your university projects and attach code artifacts
        </p>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        <div className="content-grid">
          {/* Sample Project Cards */}
          <div className="dash-card">
            <div className="dash-icon">
              <i className="lucide" data-lucide="folder"></i>
            </div>
            <h3>Web Projects</h3>
            <p>Professional web interfaces with latest technologies</p>
            <div className="project-stats">
              <div className="stat-item">
                <span className="stat-number">24</span>
                <span className="stat-label">Files</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">142</span>
                <span className="stat-label">Tasks</span>
              </div>
            </div>
          </div>

          <div className="dash-card">
            <div className="dash-icon">
              <i className="lucide" data-lucide="code"></i>
            </div>
            <h3>Mobile Apps</h3>
            <p>Smart mobile applications with premium user experience</p>
            <div className="project-stats">
              <div className="stat-item">
                <span className="stat-number">18</span>
                <span className="stat-label">Screens</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">89</span>
                <span className="stat-label">Features</span>
              </div>
            </div>
          </div>

          <div className="dash-card">
            <div className="dash-icon">
              <i className="lucide" data-lucide="database"></i>
            </div>
            <h3>Data Systems</h3>
            <p>Efficient management and analysis of big data</p>
            <div className="project-stats">
              <div className="stat-item">
                <span className="stat-number">5.2TB</span>
                <span className="stat-label">Data</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">99.9%</span>
                <span className="stat-label">Uptime</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Theme Toggle Button */}
      <button 
        className="theme-toggle" 
        onClick={() => {
          document.body.classList.toggle('dark');
          document.body.classList.toggle('light');
        }}
      >
        <i className="lucide" data-lucide="sun"></i>
      </button>

      {/* Initialize Lucide Icons */}
      <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    </div>
  );
};

export default ProjectsWorkspace;
