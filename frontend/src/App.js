import React, { useState, useEffect, useCallback } from 'react';
import ChatWindow from './components/ChatWindow';
import SettingsPanel from './components/SettingsPanel';
import ScreenshotMonitor from './components/ScreenshotMonitor';
import ExistingMemory from './components/ExistingMemory';
import ApiKeyModal from './components/ApiKeyModal';
import BackendLoadingModal from './components/BackendLoadingModal';
import Logo from './components/Logo';
import UpdateChecker from './components/UpdateChecker';
import queuedFetch from './utils/requestQueue';
import './App.css';
import { useTranslation } from 'react-i18next';

function App() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('chat');
  const [settings, setSettings] = useState({
    model: 'gpt-4o-mini',
    persona: 'helpful_assistant',
    timezone: 'America/New_York',
    serverUrl: process.env.REACT_APP_BACKEND_URL || 'http://localhost:47283'
  });

  // Lift chat messages state to App level to persist across tab switches
  const [chatMessages, setChatMessages] = useState([]);

  // Screen monitoring state to share between ChatWindow and ScreenshotMonitor
  const [isScreenMonitoring, setIsScreenMonitoring] = useState(false);

  // Current user state - lift from SettingsPanel to App level for global access
  const [currentUser, setCurrentUser] = useState(null);

  // API Key modal state
  const [apiKeyModal, setApiKeyModal] = useState({
    isOpen: false,
    missingKeys: [],
    modelType: ''
  });

  // Track pending model changes for retry after API key update
  const [pendingModelChange, setPendingModelChange] = useState({
    model: null,
    type: null, // 'chat' or 'memory'
    retryFunction: null
  });

  // Backend loading modal state
  const [backendLoading, setBackendLoading] = useState({
    isVisible: false,
    isChecking: false,
    lastCheckTime: null,
    consecutiveFailures: 0,
    isReconnection: false // Track if this is a reconnection vs initial connection
  });

  const checkApiKeys = useCallback(async (forceOpen = false) => {
    try {
      console.log(`Checking API keys for model: ${settings.model}`);
      const response = await queuedFetch(`${settings.serverUrl}/api_keys/check`);
      if (response.ok) {
        const data = await response.json();
        console.log('API key status:', data);
        
        if (forceOpen || (data.requires_api_key && data.missing_keys.length > 0)) {
          if (forceOpen) {
            console.log('Manual API key update requested');
          } else {
            console.log(`Missing API keys detected: ${data.missing_keys.join(', ')}`);
          }
          setApiKeyModal({
            isOpen: true,
            missingKeys: data.missing_keys,
            modelType: data.model_type
          });
        } else {
          console.log('All required API keys are available');
          setApiKeyModal({
            isOpen: false,
            missingKeys: [],
            modelType: ''
          });
        }
      } else {
        console.error('Failed to check API keys:', response.statusText);
      }
    } catch (error) {
      console.error('Error checking API keys:', error);
    }
  }, [settings.model, settings.serverUrl]);

  // Load user settings from backend
  const loadUserSettings = useCallback(async (userId) => {
    if (!settings.serverUrl || !userId) {
      console.log('loadUserSettings: serverUrl or userId not available');
      return;
    }

    try {
      console.log(`Loading settings for user: ${userId}`);
      const response = await queuedFetch(`${settings.serverUrl}/settings/users/${userId}`);
      if (response.ok) {
        const data = await response.json();
        console.log('User settings loaded:', data);
        if (data.success && data.settings) {
          // Update settings with user-specific values, but keep serverUrl
          setSettings(prev => ({
            ...prev,
            model: data.settings.chat_model || prev.model,
            memoryModel: data.settings.memory_model || prev.memoryModel,
            timezone: data.settings.timezone || prev.timezone,
            persona: data.settings.persona || prev.persona,
            // Keep UI preferences if they exist
            uiPreferences: data.settings.ui_preferences || prev.uiPreferences
          }));
          console.log(`User settings loaded for: ${userId}`);
        }
      } else {
        console.error('Failed to load user settings:', response.statusText);
      }
    } catch (error) {
      console.error('Error loading user settings:', error);
    }
  }, [settings.serverUrl]);

  // Save user settings to backend
  const saveUserSettings = useCallback(async (userId, settingsToSave) => {
    if (!settings.serverUrl || !userId) {
      console.log('saveUserSettings: serverUrl or userId not available');
      return;
    }

    try {
      console.log(`Saving settings for user: ${userId}`, settingsToSave);
      const response = await queuedFetch(`${settings.serverUrl}/settings/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          settings: {
            chat_model: settingsToSave.model,
            memory_model: settingsToSave.memoryModel,
            timezone: settingsToSave.timezone,
            persona: settingsToSave.persona,
            ui_preferences: settingsToSave.uiPreferences || {}
          }
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('User settings saved:', data);
        return data.success;
      } else {
        console.error('Failed to save user settings:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error saving user settings:', error);
      return false;
    }
  }, [settings.serverUrl]);

  // Fetch current user from backend
  const fetchCurrentUser = useCallback(async () => {
    if (!settings.serverUrl) {
      console.log('fetchCurrentUser: serverUrl not available yet');
      return;
    }

    try {
      console.log('Fetching current user from backend...');
      const response = await queuedFetch(`${settings.serverUrl}/users/current`);
      if (response.ok) {
        const data = await response.json();
        console.log('Current user data:', data);
        if (data.user) {
          setCurrentUser(data.user);
          console.log(`Current user set to: ${data.user.name} (${data.user.id})`);
          // Load user settings after setting current user
          await loadUserSettings(data.user.id);
        }
      } else {
        console.error('Failed to fetch current user:', response.statusText);
        // 如果获取失败，使用默认用户ID
        setCurrentUser({
          id: "user-00000000-0000-4000-8000-000000000000",
          name: "default_user"
        });
      }
    } catch (error) {
      console.error('Error fetching current user:', error);
      // 如果获取失败，使用默认用户ID
      setCurrentUser({
        id: "user-00000000-0000-4000-8000-000000000000",
        name: "default_user"
      });
    }
  }, [settings.serverUrl, loadUserSettings]);

  // Refresh backend-dependent data after successful connection
  const refreshBackendData = useCallback(async () => {
    console.log('🔄 Refreshing backend-dependent data...');
    
    // Fetch current user first
    await fetchCurrentUser();
    
    // Check API keys after successful backend connection
    await checkApiKeys();
    
    // Trigger refresh of other backend-dependent components
    // This will cause components like SettingsPanel to re-fetch their data
    setSettings(prev => ({ ...prev, lastBackendRefresh: Date.now() }));
  }, [checkApiKeys, fetchCurrentUser]);

  // Check backend health
  const checkBackendHealth = useCallback(async () => {
    let shouldProceed = true;
    let currentVisibility = false;
    
    // Check if health check is already in progress and capture current visibility
    setBackendLoading(prev => {
      if (prev.isChecking) {
        console.log('Health check already in progress, skipping...');
        shouldProceed = false;
        return prev;
      }
      currentVisibility = prev.isVisible;
      return { ...prev, isChecking: true };
    });

    if (!shouldProceed) {
      return false;
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      const response = await fetch(`${settings.serverUrl}/health`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        }
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        console.log('✅ Backend is healthy - hiding loading modal');
        
        setBackendLoading(prev => ({
          ...prev,
          isVisible: false,
          isChecking: false,
          lastCheckTime: Date.now(),
          consecutiveFailures: 0,
          isReconnection: false // Reset reconnection flag on success
        }));

        // If the loading modal was visible, refresh backend data after successful connection
        if (currentVisibility) {
          console.log('🔄 Backend reconnected - refreshing data...');
          await refreshBackendData();
        }
        
        return true;
      } else {
        throw new Error(`Health check failed with status: ${response.status}`);
      }
    } catch (error) {
      console.warn('❌ Backend health check failed:', error.message);
      setBackendLoading(prev => ({
        ...prev,
        isVisible: true,
        isChecking: false,
        lastCheckTime: Date.now(),
        consecutiveFailures: prev.consecutiveFailures + 1
        // Keep existing isReconnection flag - don't change it on failure
      }));
      return false;
    }
  }, [settings.serverUrl, refreshBackendData]);

  // Retry backend connection
  const retryBackendConnection = useCallback(async () => {
    console.log('🔄 Retrying backend connection...');
    await checkBackendHealth();
  }, [checkBackendHealth]);

  // Check for missing API keys on startup
  useEffect(() => {
    checkApiKeys();
  }, [settings.serverUrl]);

  // Also check API keys when model changes
  useEffect(() => {
    checkApiKeys();
  }, [settings.model]);

  // Initial backend health check on startup
  useEffect(() => {
    const performInitialHealthCheck = async () => {
      // Show loading modal immediately for initial startup
      setBackendLoading(prev => ({ 
        ...prev, 
        isVisible: true, 
        isReconnection: false // This is initial startup, not reconnection
      }));
      
      // Wait a moment for the UI to update
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Check backend health (will automatically refresh data if modal was visible)
      await checkBackendHealth();
    };

    performInitialHealthCheck();
  }, [settings.serverUrl, checkBackendHealth]);

  // Periodic backend health check
  useEffect(() => {
    const interval = setInterval(() => {
      setBackendLoading(prev => {
        const timeSinceLastCheck = Date.now() - (prev.lastCheckTime || 0);
        
        // Check more frequently when modal is visible, less frequently when not
        const shouldCheck = prev.isVisible 
          ? !prev.isChecking // Every 5 seconds when modal is visible
          : timeSinceLastCheck > 30000 && !prev.isChecking; // Every 30 seconds when modal is hidden
        
        if (shouldCheck) {
          console.log('🔄 Periodic health check triggered. Modal visible:', prev.isVisible);
          checkBackendHealth();
        }
        
        return prev; // Don't actually update state, just check conditions
      });
    }, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, [checkBackendHealth]);

  // Handle window focus/visibility events for backend health check - but don't show loading modal unless backend actually fails
  useEffect(() => {
    const handleWindowFocus = async () => {
      console.log('🔍 Window focused - checking backend health silently...');
      
      // Check backend health silently - only show modal if it actually fails
      const healthCheckResult = await checkBackendHealth();
      // Loading modal will be shown automatically by checkBackendHealth if it fails
    };

    const handleVisibilityChange = async () => {
      if (!document.hidden) {
        console.log('🔍 Document became visible - checking backend health silently...');
        
        // Check backend health silently - only show modal if it actually fails
        const healthCheckResult = await checkBackendHealth();
        // Loading modal will be shown automatically by checkBackendHealth if it fails
      }
    };

    // Add event listeners
    window.addEventListener('focus', handleWindowFocus);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Cleanup
    return () => {
      window.removeEventListener('focus', handleWindowFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [checkBackendHealth]);

  const handleApiKeyModalClose = () => {
    setApiKeyModal(prev => ({ ...prev, isOpen: false }));
  };

  const handleApiKeySubmit = async () => {
    // Refresh API key status after submission
    await checkApiKeys();
    
    // If there's a pending model change, retry it now
    if (pendingModelChange.retryFunction) {
      console.log(`Retrying ${pendingModelChange.type} model change to '${pendingModelChange.model}' after API key update`);
      try {
        await pendingModelChange.retryFunction();
      } catch (error) {
        console.error('Failed to retry model change:', error);
      }
      // Clear the pending change after retry attempt
      setPendingModelChange({
        model: null,
        type: null,
        retryFunction: null
      });
    }
  };

  useEffect(() => {
    // Listen for menu events from Electron
    const cleanupFunctions = [];
    
    if (window.electronAPI) {
      const cleanupNewChat = window.electronAPI.onMenuNewChat(() => {
        setActiveTab('chat');
        // Clear chat messages when creating new chat
        setChatMessages([]);
      });
      cleanupFunctions.push(cleanupNewChat);

      const cleanupOpenTerminal = window.electronAPI.onMenuOpenTerminal(() => {
        // Open terminal logic here
        console.log('Open terminal requested');
      });
      cleanupFunctions.push(cleanupOpenTerminal);

      const cleanupTakeScreenshot = window.electronAPI.onMenuTakeScreenshot(() => {
        // Switch to chat tab and let ChatWindow handle the screenshot
        setActiveTab('chat');
      });
      cleanupFunctions.push(cleanupTakeScreenshot);

      // Handle Electron window events - check backend health silently
      const cleanupWindowShow = window.electronAPI.onWindowShow(async () => {
        console.log('🔍 Electron window shown - checking backend health silently...');
        
        // Check backend health silently - only show modal if it actually fails
        const healthCheckResult = await checkBackendHealth();
        // Loading modal will be shown automatically by checkBackendHealth if it fails
      });
      cleanupFunctions.push(cleanupWindowShow);

      const cleanupAppActivate = window.electronAPI.onAppActivate(async () => {
        console.log('🔍 Electron app activated - checking backend health silently...');
        
        // Check backend health silently - only show modal if it actually fails
        const healthCheckResult = await checkBackendHealth();
        // Loading modal will be shown automatically by checkBackendHealth if it fails
      });
      cleanupFunctions.push(cleanupAppActivate);
    }

    // Cleanup listeners on unmount
    return () => {
      cleanupFunctions.forEach(cleanup => {
        if (cleanup) cleanup();
      });
    };
  }, [checkBackendHealth]);

  const handleSettingsChange = async (newSettings) => {
    // Update local state first
    const updatedSettings = { ...settings, ...newSettings };
    setSettings(updatedSettings);

    // Save to backend if user is available
    if (currentUser && currentUser.id) {
      try {
        const success = await saveUserSettings(currentUser.id, updatedSettings);
        if (success) {
          console.log('Settings saved successfully for user:', currentUser.id);
        } else {
          console.error('Failed to save settings for user:', currentUser.id);
        }
      } catch (error) {
        console.error('Error saving settings:', error);
      }
    }
  };

  // Handle user switching with settings loading
  const handleUserSwitch = useCallback(async (newUser) => {
    setCurrentUser(newUser);

    // Load settings for the new user
    if (newUser && newUser.id) {
      await loadUserSettings(newUser.id);
    }
  }, [loadUserSettings]);



  return (
    <div className="App">
      <div className="app-header">
        <div className="app-title">
          <Logo 
            size="small" 
            showText={false} 
          />
          <span className="version">v0.1.4</span>
        </div>
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            {t('tabs.chat')}
          </button>
          <button 
            className={`tab ${activeTab === 'screenshots' ? 'active' : ''}`}
            onClick={() => setActiveTab('screenshots')}
          >
            {t('tabs.screenshots')}
          </button>
          <button 
            className={`tab ${activeTab === 'memory' ? 'active' : ''}`}
            onClick={() => setActiveTab('memory')}
          >
            {t('tabs.memory')}
          </button>
          <button 
            className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            {t('tabs.settings')}
          </button>
        </div>
      </div>

      <div className="app-content">
        {/* Keep ChatWindow always mounted to maintain streaming state */}
        <div style={{ 
          display: activeTab === 'chat' ? 'flex' : 'none',
          flexDirection: 'column',
          height: '100%'
        }}>
          <ChatWindow
            settings={settings}
            messages={chatMessages}
            setMessages={setChatMessages}
            isScreenMonitoring={isScreenMonitoring}
            currentUser={currentUser}
            onApiKeyRequired={(missingKeys, modelType) => {
              setApiKeyModal({
                isOpen: true,
                missingKeys,
                modelType
              });
            }}
          />
        </div>
        {/* Keep ScreenshotMonitor always mounted to maintain monitoring state */}
        <div style={{ display: activeTab === 'screenshots' ? 'block' : 'none' }}>
          <ScreenshotMonitor 
            settings={settings} 
            onMonitoringStatusChange={setIsScreenMonitoring}
            currentUser={currentUser}
          />
        </div>
        {activeTab === 'memory' && (
          <ExistingMemory
            settings={settings}
            currentUser={currentUser}
          />
        )}
        {activeTab === 'settings' && (
          <SettingsPanel
            settings={settings}
            onSettingsChange={handleSettingsChange}
            onApiKeyCheck={checkApiKeys}
            currentUser={currentUser}
            onCurrentUserChange={handleUserSwitch}
            onApiKeyRequired={(missingKeys, modelType, pendingModel, changeType, retryFunction) => {
              setApiKeyModal({
                isOpen: true,
                missingKeys,
                modelType
              });
              setPendingModelChange({
                model: pendingModel,
                type: changeType,
                retryFunction: retryFunction
              });
            }}
            isVisible={activeTab === 'settings'}
          />
        )}
      </div>

      {/* API Key Modal */}
      <ApiKeyModal
        isOpen={apiKeyModal.isOpen}
        missingKeys={apiKeyModal.missingKeys}
        modelType={apiKeyModal.modelType}
        onClose={handleApiKeyModalClose}
        serverUrl={settings.serverUrl}
        onSubmit={handleApiKeySubmit}
      />

      {/* Backend Loading Modal */}
      <BackendLoadingModal
        isVisible={backendLoading.isVisible}
        onRetry={retryBackendConnection}
        isReconnection={backendLoading.isReconnection}
      />

      {/* Update Checker */}
      <UpdateChecker currentVersion="0.1.4" />
    </div>
  );
}

export default App; 