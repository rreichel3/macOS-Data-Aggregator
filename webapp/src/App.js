import React, { useState, useEffect } from 'react';
import { Search, Package, X } from 'lucide-react';
import Fuse from 'fuse.js';

function App() {
  const [apps, setApps] = useState([]);
  const [filteredApps, setFilteredApps] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedApp, setSelectedApp] = useState(null);
  const [activeTab, setActiveTab] = useState('info');
  const [fuse, setFuse] = useState(null);

  useEffect(() => {
    loadAppsData();
  }, []);

  useEffect(() => {
    if (apps.length > 0) {
      const fuseInstance = new Fuse(apps, {
        keys: ['name', 'path', 'codesign.identifier'],
        threshold: 0.3,
        includeScore: true
      });
      setFuse(fuseInstance);
    }
  }, [apps]);

  useEffect(() => {
    if (searchTerm === '') {
      setFilteredApps(apps);
    } else if (fuse) {
      const results = fuse.search(searchTerm);
      setFilteredApps(results.map(result => result.item));
    }
  }, [searchTerm, apps, fuse]);

  const loadAppsData = async () => {
    try {
      setLoading(true);
      
      // First, try to load the data index
      const response = await fetch('./data/index.json');
      if (!response.ok) {
        throw new Error('Failed to load app data index');
      }
      
      const appIndex = await response.json();
      
      // Load manifest data for each app
      const appPromises = appIndex.apps.map(async (appName) => {
        try {
          const manifestResponse = await fetch(`./data/${appName}/manifest.json`);
          if (manifestResponse.ok) {
            const manifest = await manifestResponse.json();
            return {
              ...manifest,
              id: appName
            };
          }
          return null;
        } catch (err) {
          console.warn(`Failed to load manifest for ${appName}:`, err);
          return null;
        }
      });
      
      const loadedApps = await Promise.all(appPromises);
      const validApps = loadedApps.filter(app => app !== null);
      
      setApps(validApps);
      setFilteredApps(validApps);
      setError(null);
    } catch (err) {
      console.error('Error loading apps data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAppDetails = async (app) => {
    try {
      const [entitlementsResponse, infoPlistResponse, sandboxResponse, sdefIndexResponse] = await Promise.all([
        fetch(`./data/${app.id}/entitlements.plist`),
        fetch(`./data/${app.id}/info.plist`),
        fetch(`./data/${app.id}/sandbox.txt`),
        fetch(`./data/${app.id}/sdef_index.json`)
      ]);

      const entitlements = entitlementsResponse.ok ? await entitlementsResponse.text() : 'Not available';
      const infoPlist = infoPlistResponse.ok ? await infoPlistResponse.text() : 'Not available';
      const sandbox = sandboxResponse.ok ? await sandboxResponse.text() : 'Not available';
      
      // Load SDEF files based on index
      let sdefFiles = [];
      if (sdefIndexResponse.ok) {
        const sdefIndex = await sdefIndexResponse.json();
        
        // Load each SDEF file listed in the index
        const sdefPromises = sdefIndex.files.map(async (fileName) => {
          try {
            const sdefResponse = await fetch(`./data/${app.id}/sdef/${fileName}`);
            if (sdefResponse.ok) {
              const sdefContent = await sdefResponse.text();
              return { name: fileName, content: sdefContent };
            }
            return null;
          } catch (err) {
            console.warn(`Failed to load SDEF file ${fileName}:`, err);
            return null;
          }
        });
        
        const loadedSdefFiles = await Promise.all(sdefPromises);
        sdefFiles = loadedSdefFiles.filter(file => file !== null);
      }

      setSelectedApp({
        ...app,
        entitlements,
        infoPlist,
        sandbox,
        sdefFiles
      });
    } catch (err) {
      console.error('Error loading app details:', err);
      setSelectedApp({
        ...app,
        entitlements: 'Error loading entitlements',
        infoPlist: 'Error loading Info.plist',
        sandbox: 'Error loading sandbox info',
        sdefFiles: []
      });
    }
  };

  const openAppModal = (app) => {
    loadAppDetails(app);
  };

  const closeModal = () => {
    setSelectedApp(null);
    setActiveTab('info');
  };

  const renderAppCard = (app) => {
    const iconPath = app.has_icon ? `./data/${app.id}/${app.icon_path}` : null;
    
    return (
      <div key={app.id} className="app-card" onClick={() => openAppModal(app)}>
        <div className="app-header">
          <div className="app-icon">
            {iconPath ? (
              <img src={iconPath} alt={`${app.name} icon`} onError={(e) => { e.target.style.display = 'none'; }} />
            ) : (
              <Package size={24} color="#64748b" />
            )}
          </div>
          <div className="app-details">
            <h3>{app.name}</h3>
            <p className="app-path">{app.path}</p>
          </div>
        </div>
        
        <div className="app-badges">
          {app.sandbox?.sandboxed === 'Yes' && (
            <span className="badge sandboxed">Sandboxed</span>
          )}
          {app.sandbox?.sandboxed === 'No' && (
            <span className="badge not-sandboxed">Not Sandboxed</span>
          )}
          {app.codesign?.signature_status?.includes('Valid') && (
            <span className="badge signed">Signed</span>
          )}
          {app.sdef_count > 0 && (
            <span className="badge sdef">{app.sdef_count} SDEF</span>
          )}
        </div>
        
        <div className="app-info">
          <div className="info-item">
            <span className="info-label">Bundle ID:</span>
            <span className="info-value">{app.codesign?.identifier || 'Unknown'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Team ID:</span>
            <span className="info-value">{app.codesign?.team_identifier || 'Unknown'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Hardened:</span>
            <span className="info-value">{app.sandbox?.hardened_runtime || 'Unknown'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Entitlements:</span>
            <span className="info-value">{app.sandbox?.entitlements_count || 0}</span>
          </div>
        </div>
      </div>
    );
  };

  const renderModal = () => {
    if (!selectedApp) return null;

    return (
      <div className="modal-overlay" onClick={closeModal}>
        <div className="modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2 className="modal-title">{selectedApp.name}</h2>
            <button className="modal-close" onClick={closeModal}>
              <X size={24} />
            </button>
          </div>
          
          <div className="modal-content">
            <div className="tabs">
              <button
                className={`tab ${activeTab === 'info' ? 'active' : ''}`}
                onClick={() => setActiveTab('info')}
              >
                Info.plist
              </button>
              <button
                className={`tab ${activeTab === 'entitlements' ? 'active' : ''}`}
                onClick={() => setActiveTab('entitlements')}
              >
                Entitlements
              </button>
              <button
                className={`tab ${activeTab === 'sandbox' ? 'active' : ''}`}
                onClick={() => setActiveTab('sandbox')}
              >
                Sandbox
              </button>
              {selectedApp.sdefFiles?.length > 0 && (
                <button
                  className={`tab ${activeTab === 'sdef' ? 'active' : ''}`}
                  onClick={() => setActiveTab('sdef')}
                >
                  SDEF Files
                </button>
              )}
            </div>
            
            <div className="tab-content">
              {activeTab === 'info' && (
                <div className="code-block">{selectedApp.infoPlist}</div>
              )}
              {activeTab === 'entitlements' && (
                <div className="code-block">{selectedApp.entitlements}</div>
              )}
              {activeTab === 'sandbox' && (
                <div className="code-block">{selectedApp.sandbox}</div>
              )}
              {activeTab === 'sdef' && (
                <div>
                  {selectedApp.sdefFiles?.map((sdefFile, index) => (
                    <div key={index}>
                      <h4>{sdefFile.name}</h4>
                      <div className="code-block">{sdefFile.content}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const stats = {
    total: apps.length,
    sandboxed: apps.filter(app => app.sandbox?.sandboxed === 'Yes').length,
    signed: apps.filter(app => app.codesign?.signature_status?.includes('Valid')).length,
    withSdef: apps.filter(app => app.sdef_count > 0).length
  };

  if (loading) {
    return (
      <div className="app">
        <div className="header">
          <h1>macOS App Data Browser</h1>
          <p>Loading application data...</p>
        </div>
        <div className="container">
          <div className="loading">Loading application data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="header">
          <h1>macOS App Data Browser</h1>
          <p>Error loading data</p>
        </div>
        <div className="container">
          <div className="error">
            <p>Failed to load application data: {error}</p>
            <p>Make sure the data directory is properly populated and accessible.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="header">
        <h1>macOS App Data Browser</h1>
        <p>Explore SDEF files, entitlements, and application metadata</p>
      </div>
      
      <div className="container">
        <div className="search-container">
          <Search className="search-icon" size={20} />
          <input
            type="text"
            className="search-input"
            placeholder="Search applications by name, bundle ID, or path..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="stats">
          <div className="stat-card">
            <div className="stat-number">{stats.total}</div>
            <div className="stat-label">Total Apps</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.sandboxed}</div>
            <div className="stat-label">Sandboxed</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.signed}</div>
            <div className="stat-label">Code Signed</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.withSdef}</div>
            <div className="stat-label">With SDEF</div>
          </div>
        </div>
        
        {filteredApps.length === 0 && searchTerm && (
          <div className="no-results">
            No applications found matching "{searchTerm}"
          </div>
        )}
        
        <div className="apps-grid">
          {filteredApps.map(renderAppCard)}
        </div>
      </div>
      
      {renderModal()}
    </div>
  );
}

export default App;
