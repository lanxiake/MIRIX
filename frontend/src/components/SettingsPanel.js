import React, { useState, useEffect, useCallback } from 'react';
import './SettingsPanel.css';
import queuedFetch from '../utils/requestQueue';
import LocalModelModal from './LocalModelModal';
import { useTranslation } from 'react-i18next';

const SettingsPanel = ({ settings, onSettingsChange, onApiKeyCheck, onApiKeyRequired, isVisible, currentUser, onCurrentUserChange }) => {
  const { t, i18n } = useTranslation();
  const [personaDetails, setPersonaDetails] = useState({});
  const [selectedPersonaText, setSelectedPersonaText] = useState('');
  const [isUpdatingPersona, setIsUpdatingPersona] = useState(false);
  const [isApplyingTemplate, setIsApplyingTemplate] = useState(false);
  const [updateMessage, setUpdateMessage] = useState('');
  const [isChangingModel, setIsChangingModel] = useState(false);
  const [modelUpdateMessage, setModelUpdateMessage] = useState('');
  const [isChangingMemoryModel, setIsChangingMemoryModel] = useState(false);
  const [memoryModelUpdateMessage, setMemoryModelUpdateMessage] = useState('');
  const [isChangingTimezone, setIsChangingTimezone] = useState(false);
  const [timezoneUpdateMessage, setTimezoneUpdateMessage] = useState('');
  const [isCheckingApiKeys, setIsCheckingApiKeys] = useState(false);
  const [apiKeyMessage, setApiKeyMessage] = useState('');
  const [isEditingPersona, setIsEditingPersona] = useState(false);
  const [selectedTemplateInEdit, setSelectedTemplateInEdit] = useState('');
  const [showLocalModelModal, setShowLocalModelModal] = useState(false);
  const [editingModel, setEditingModel] = useState(null);
  const [customModels, setCustomModels] = useState([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [modelToDelete, setModelToDelete] = useState(null);
  const [isDeletingModel, setIsDeletingModel] = useState(false);
  const [mcpMarketplace, setMcpMarketplace] = useState({ servers: [], categories: [] });
  const [mcpSearchQuery, setMcpSearchQuery] = useState('');
  const [mcpSearchResults, setMcpSearchResults] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isLoadingMcp, setIsLoadingMcp] = useState(false);
  const [mcpMessage, setMcpMessage] = useState('');
  const [showGmailModal, setShowGmailModal] = useState(false);
  const [gmailCredentials, setGmailCredentials] = useState({ clientId: '', clientSecret: '' });
  const [users, setUsers] = useState([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [newUserName, setNewUserName] = useState('');
  const [showDeleteUserConfirm, setShowDeleteUserConfirm] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [isDeletingUser, setIsDeletingUser] = useState(false);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [saveSettingsMessage, setSaveSettingsMessage] = useState('');

  // Debug logging for settings
  useEffect(() => {
    console.log('SettingsPanel: settings changed:', {
      serverUrl: settings.serverUrl,
      model: settings.model,
      persona: settings.persona,
      timezone: settings.timezone
    });
  }, [settings]);

  const handleInputChange = (key, value) => {
    onSettingsChange({ [key]: value });
  };

  const fetchPersonaDetails = useCallback(async () => {
    if (!settings.serverUrl) {
      console.log('fetchPersonaDetails: serverUrl not available yet');
      return;
    }
    try {
      const response = await queuedFetch(`${settings.serverUrl}/personas`);
      if (response.ok) {
        const data = await response.json();
        setPersonaDetails(prevDetails => {
          const hasChanged = JSON.stringify(prevDetails) !== JSON.stringify(data.personas);
          return hasChanged ? data.personas : prevDetails;
        });
      } else {
        console.error('Failed to fetch persona details');
      }
    } catch (error) {
      console.error('Error fetching persona details:', error);
    }
  }, [settings.serverUrl]);

  const fetchCoreMemoryPersona = useCallback(async () => {
    if (!settings.serverUrl) {
      console.log('fetchCoreMemoryPersona: serverUrl not available yet');
      return;
    }
    try {
      const response = await queuedFetch(`${settings.serverUrl}/personas/core_memory`);
      if (response.ok) {
        const data = await response.json();
        setSelectedPersonaText(prevText => {
          return prevText !== data.text ? data.text : prevText;
        });
      } else {
        console.error('Failed to fetch core memory persona');
      }
    } catch (error) {
      console.error('Error fetching core memory persona:', error);
    }
  }, [settings.serverUrl]);

  const fetchCurrentModel = useCallback(async () => {
    if (!settings.serverUrl) {
      console.log('fetchCurrentModel: serverUrl not available yet');
      return;
    }
    try {
      const response = await queuedFetch(`${settings.serverUrl}/models/current`);
      if (response.ok) {
        const data = await response.json();
        // Only update if the model is different from current settings
        if (data.current_model !== settings.model) {
          onSettingsChange({ model: data.current_model });
        }
      } else {
        console.error('Failed to fetch current model');
      }
    } catch (error) {
      console.error('Error fetching current model:', error);
    }
  }, [settings.serverUrl, settings.model, onSettingsChange]);

  const fetchCurrentMemoryModel = useCallback(async () => {
    if (!settings.serverUrl) {
      console.log('fetchCurrentMemoryModel: serverUrl not available yet');
      return;
    }
    try {
      const response = await queuedFetch(`${settings.serverUrl}/models/memory/current`);
      if (response.ok) {
        const data = await response.json();
        // Only update if the memory model is different from current settings
        if (data.current_model !== settings.memoryModel) {
          onSettingsChange({ memoryModel: data.current_model });
        }
      } else {
        console.error('Failed to fetch current memory model');
      }
    } catch (error) {
      console.error('Error fetching current memory model:', error);
    }
  }, [settings.serverUrl, settings.memoryModel, onSettingsChange]);

  const fetchCurrentTimezone = useCallback(async () => {
    if (!settings.serverUrl) {
      console.log('fetchCurrentTimezone: serverUrl not available yet');
      return;
    }
    try {
      const response = await queuedFetch(`${settings.serverUrl}/timezone/current`);
      if (response.ok) {
        const data = await response.json();
        // Only update if the timezone is different from current settings
        if (data.timezone !== settings.timezone) {
          onSettingsChange({ timezone: data.timezone });
        }
      } else {
        console.error('Failed to fetch current timezone');
      }
    } catch (error) {
      console.error('Error fetching current timezone:', error);
    }
  }, [settings.serverUrl, settings.timezone, onSettingsChange]);

  const fetchCustomModels = useCallback(async () => {
    if (!settings.serverUrl) {
      console.log('fetchCustomModels: serverUrl not available yet');
      return;
    }
    try {
      const response = await queuedFetch(`${settings.serverUrl}/models/custom/list`);
      if (response.ok) {
        const data = await response.json();
        setCustomModels(prevModels => {
          const newModels = data.models || [];
          const hasChanged = JSON.stringify(prevModels) !== JSON.stringify(newModels);
          return hasChanged ? newModels : prevModels;
        });
      } else {
        console.error('Failed to fetch custom models');
      }
    } catch (error) {
      console.error('Error fetching custom models:', error);
    }
  }, [settings.serverUrl]);

  // 处理编辑自定义模型
  const handleEditModel = (modelName) => {
    setEditingModel(modelName);
    setShowLocalModelModal(true);
  };

  // 处理删除自定义模型
  const handleDeleteModel = (modelName) => {
    setModelToDelete(modelName);
    setShowDeleteConfirm(true);
  };

  // 确认删除模型
  const confirmDeleteModel = async () => {
    if (!modelToDelete) return;
    
    setIsDeletingModel(true);
    try {
      // 从模型名称生成模型ID
      const modelId = modelToDelete.replace(/[^a-zA-Z0-9_.-]/g, '_');
      const response = await queuedFetch(`${settings.serverUrl}/models/custom/${modelId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // 刷新模型列表
          fetchCustomModels();
          setShowDeleteConfirm(false);
          setModelToDelete(null);
        } else {
          alert(result.message || '删除模型失败');
        }
      } else {
        alert('删除模型失败');
      }
    } catch (error) {
      console.error('Error deleting model:', error);
      alert('删除模型时发生错误');
    } finally {
      setIsDeletingModel(false);
    }
  };

  // 取消删除
  const cancelDeleteModel = () => {
    setShowDeleteConfirm(false);
    setModelToDelete(null);
  };

  const fetchMcpMarketplace = useCallback(async () => {
    if (!settings.serverUrl) {
      console.log('fetchMcpMarketplace: serverUrl not available yet');
      return;
    }
    try {
      setIsLoadingMcp(true);
      console.log('Fetching MCP marketplace data...');
      const response = await queuedFetch(`${settings.serverUrl}/mcp/marketplace`);
      if (response.ok) {
        const data = await response.json();
        console.log('MCP marketplace data:', data);
        
        const newMarketplace = { 
          servers: data.servers || [], 
          categories: ['All', ...(data.categories || [])] 
        };
        
        // Only update state if data has actually changed
        setMcpMarketplace(prevMarketplace => {
          const hasChanged = JSON.stringify(prevMarketplace) !== JSON.stringify(newMarketplace);
          return hasChanged ? newMarketplace : prevMarketplace;
        });
        
        setMcpSearchResults(prevResults => {
          const newResults = data.servers || [];
          const hasChanged = JSON.stringify(prevResults) !== JSON.stringify(newResults);
          return hasChanged ? newResults : prevResults;
        });
        
        // Log connection status
        const connectedServers = data.servers?.filter(s => s.is_connected) || [];
        console.log(`Found ${connectedServers.length} connected MCP servers:`, connectedServers.map(s => s.id));
      } else {
        console.error('Failed to fetch MCP marketplace');
        setMcpMessage(`❌ ${t('settings.messages.failedToLoadMcpMarketplace')}`);
      }
    } catch (error) {
      console.error('Error fetching MCP marketplace:', error);
      setMcpMessage(`❌ ${t('settings.messages.errorLoadingMcpMarketplace')}`);
    } finally {
      setIsLoadingMcp(false);
    }
  }, [settings.serverUrl]);

  const fetchUsers = useCallback(async () => {
    if (!settings.serverUrl) {
      console.log('fetchUsers: serverUrl not available yet');
      return;
    }
    try {
      setIsLoadingUsers(true);
      console.log('Fetching users data...');
      const response = await queuedFetch(`${settings.serverUrl}/users`);
      if (response.ok) {
        const data = await response.json();
        console.log('Users data:', data);
        const usersList = data.users || [];
        setUsers(usersList);

        // Only set current user if not already set
        // This prevents循环 by not calling onCurrentUserChange on every fetch
        const activeUser = usersList.find(user => user.status === 'active');
        if (activeUser && (!currentUser || currentUser.id !== activeUser.id)) {
          onCurrentUserChange(activeUser);
        }
      } else {
        console.error('Failed to fetch users');
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setIsLoadingUsers(false);
    }
  }, [settings.serverUrl]);

  const searchMcpMarketplace = useCallback(async (query = '') => {
    if (!settings.serverUrl) {
      return;
    }
    try {
      setIsLoadingMcp(true);
      let url = `${settings.serverUrl}/mcp/marketplace`;
      if (query.trim()) {
        url += `/search?query=${encodeURIComponent(query)}`;
      }
      
      const response = await queuedFetch(url);
      if (response.ok) {
        const data = await response.json();
        const results = query.trim() ? (data.results || []) : (data.servers || []);
        
        // Filter by category if not 'All'
        const filteredResults = selectedCategory === 'All' || selectedCategory === t('settings.mcp.filterAll')
          ? results 
          : results.filter(server => server.category === selectedCategory);
          
        setMcpSearchResults(filteredResults);
      }
    } catch (error) {
      console.error('Error searching MCP marketplace:', error);
    } finally {
      setIsLoadingMcp(false);
    }
  }, [settings.serverUrl, selectedCategory]);

  const refreshMcpStatus = useCallback(async () => {
    if (!settings.serverUrl) {
      return;
    }
    try {
      console.log('Refreshing MCP connection status...');
      const response = await queuedFetch(`${settings.serverUrl}/mcp/status`);
      if (response.ok) {
        const data = await response.json();
        console.log('MCP status:', data);
        
        // Check if we have any connected servers
        if (data.connected_servers && data.connected_servers.length > 0) {
          console.log(`Found ${data.connected_servers.length} connected MCP servers:`, data.connected_servers);
        }
        
        // Refresh the marketplace to get updated connection status
        await fetchMcpMarketplace();
        await searchMcpMarketplace(mcpSearchQuery);
      }
    } catch (error) {
      console.error('Error refreshing MCP status:', error);
    }
  }, [settings.serverUrl, fetchMcpMarketplace, searchMcpMarketplace, mcpSearchQuery]);

  const connectMcpServer = useCallback(async (serverId, envVars = {}) => {
    if (!settings.serverUrl) {
      return;
    }
    
    // Special handling for Gmail - show modal for credentials
    if (serverId === 'gmail-native') {
      setShowGmailModal(true);
      return; // Exit here, actual connection happens in handleGmailConnect
    }
    
    try {
      setIsLoadingMcp(true);
      setMcpMessage(t('settings.mcp.connectingTo', { serverId }));
      
      const response = await queuedFetch(`${settings.serverUrl}/mcp/marketplace/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_id: serverId, env_vars: envVars })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setMcpMessage(`✅ ${t('settings.mcp.connectedSuccess', { serverName: data.server_name, toolsCount: data.tools_count })}`);
          // Refresh the marketplace to update connection status
          await fetchMcpMarketplace();
          await searchMcpMarketplace(mcpSearchQuery);
        } else {
          setMcpMessage(`❌ ${data.error}`);
        }
      } else {
        setMcpMessage('❌ Failed to connect to server');
      }
    } catch (error) {
      console.error('Error connecting MCP server:', error);
      setMcpMessage(`❌ ${t('settings.mcp.connectionError')}`);
    } finally {
      setIsLoadingMcp(false);
      setTimeout(() => setMcpMessage(''), 5000);
    }
  }, [settings.serverUrl, fetchMcpMarketplace, searchMcpMarketplace, mcpSearchQuery]);

  const handleGmailConnect = useCallback(async () => {
    const { clientId, clientSecret } = gmailCredentials;
    
    if (!clientId.trim()) {
      setMcpMessage(`❌ ${t('settings.messages.gmailClientIdRequired')}`);
      return;
    }
    
    if (!clientSecret.trim()) {
      setMcpMessage(`❌ ${t('settings.messages.gmailClientSecretRequired')}`);
      return;
    }
    
    setShowGmailModal(false);
    setMcpMessage(`🔐 ${t('settings.mcp.gmailOAuth')}`);
    
    const envVars = { client_id: clientId.trim(), client_secret: clientSecret.trim() };
    
    try {
      setIsLoadingMcp(true);
      setMcpMessage(t('settings.mcp.connectingToGmail'));
      
      const response = await queuedFetch(`${settings.serverUrl}/mcp/marketplace/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_id: 'gmail-native', env_vars: envVars })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setMcpMessage(`✅ ${t('settings.mcp.connectedSuccess', { serverName: data.server_name, toolsCount: data.tools_count })}`);
          // Clear credentials for security
          setGmailCredentials({ clientId: '', clientSecret: '' });
          // Refresh the marketplace to update connection status
          await fetchMcpMarketplace();
          await searchMcpMarketplace(mcpSearchQuery);
        } else {
          setMcpMessage(`❌ ${data.error}`);
        }
      } else {
        setMcpMessage('❌ Failed to connect to Gmail server');
      }
    } catch (error) {
      console.error('Error connecting Gmail server:', error);
      setMcpMessage(`❌ ${t('settings.mcp.gmailConnectionError')}`);
    } finally {
      setIsLoadingMcp(false);
      setTimeout(() => setMcpMessage(''), 5000);
    }
  }, [gmailCredentials, settings.serverUrl, fetchMcpMarketplace, searchMcpMarketplace, mcpSearchQuery]);

  const handleGmailModalClose = useCallback(() => {
    setShowGmailModal(false);
    setGmailCredentials({ clientId: '', clientSecret: '' });
  }, []);

  const handleUserSelection = useCallback(async (selectedUser) => {
    if (!settings.serverUrl) {
      return;
    }

    try {
      console.log('Switching to user:', selectedUser);

      const response = await queuedFetch(`${settings.serverUrl}/users/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: selectedUser.id })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          onCurrentUserChange(selectedUser);
          console.log('Successfully switched to user:', data.user);

          // Refresh all user-specific data
          console.log('Refreshing all settings data for new user...');
          await Promise.all([
            fetchUsers(),                // Refresh users list to update status
            fetchCurrentModel(),         // Refresh current model
            fetchCurrentMemoryModel(),   // Refresh memory model
            fetchCurrentTimezone(),      // Refresh timezone
            fetchPersonaDetails(),       // Refresh persona details
            fetchCoreMemoryPersona(),    // Refresh core memory persona
            fetchCustomModels(),         // Refresh custom models list
            fetchMcpMarketplace(),       // Refresh MCP marketplace
          ]);
          console.log('All settings data refreshed successfully');
        } else {
          console.error('Failed to switch user:', data.message);
        }
      } else {
        console.error('Failed to switch user - server error');
      }
    } catch (error) {
      console.error('Error switching user:', error);
    } finally {
      setIsUserDropdownOpen(false);
    }
  }, [
    settings.serverUrl,
    fetchUsers,
    onCurrentUserChange,
    fetchCurrentModel,
    fetchCurrentMemoryModel,
    fetchCurrentTimezone,
    fetchPersonaDetails,
    fetchCoreMemoryPersona,
    fetchCustomModels,
    fetchMcpMarketplace
  ]);

  const handleCreateUser = useCallback(async () => {
    if (!settings.serverUrl || !newUserName.trim()) {
      return;
    }

    try {
      const response = await queuedFetch(`${settings.serverUrl}/users/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newUserName.trim(), set_as_active: true })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('User created successfully:', data);

        // Close modal and reset form
        setShowAddUserModal(false);
        setNewUserName('');

        // Set the new user as current user
        if (data.user) {
          onCurrentUserChange(data.user);
        }

        // Refresh all user-specific data for the new user
        console.log('Refreshing all settings data for new user...');
        await Promise.all([
          fetchUsers(),                // Refresh users list
          fetchCurrentModel(),         // Refresh current model
          fetchCurrentMemoryModel(),   // Refresh memory model
          fetchCurrentTimezone(),      // Refresh timezone
          fetchPersonaDetails(),       // Refresh persona details
          fetchCoreMemoryPersona(),    // Refresh core memory persona
          fetchCustomModels(),         // Refresh custom models list
          fetchMcpMarketplace(),       // Refresh MCP marketplace
        ]);
        console.log('All settings data refreshed for new user');
      } else {
        console.error('Failed to create user');
      }
    } catch (error) {
      console.error('Error creating user:', error);
    }
  }, [
    settings.serverUrl,
    newUserName,
    fetchUsers,
    onCurrentUserChange,
    fetchCurrentModel,
    fetchCurrentMemoryModel,
    fetchCurrentTimezone,
    fetchPersonaDetails,
    fetchCoreMemoryPersona,
    fetchCustomModels,
    fetchMcpMarketplace
  ]);

  const handleDeleteUser = useCallback(async (user) => {
    if (!settings.serverUrl) {
      return;
    }

    setUserToDelete(user);
    setShowDeleteUserConfirm(true);
  }, [settings.serverUrl]);

  const confirmDeleteUser = useCallback(async () => {
    if (!userToDelete || !settings.serverUrl) {
      return;
    }

    setIsDeletingUser(true);
    try {
      const response = await queuedFetch(`${settings.serverUrl}/users/${userToDelete.id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log('User deleted successfully:', data);

          // If deleted user was current user, switch to another user
          if (currentUser?.id === userToDelete.id) {
            const remainingUsers = users.filter(u => u.id !== userToDelete.id);
            if (remainingUsers.length > 0) {
              onCurrentUserChange(remainingUsers[0]);
            } else {
              onCurrentUserChange(null);
            }
          }

          // Refresh users list
          await fetchUsers();

          // Close modal and reset
          setShowDeleteUserConfirm(false);
          setUserToDelete(null);
        } else {
          alert(data.message || 'Failed to delete user');
        }
      } else {
        alert('Failed to delete user - server error');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Error deleting user');
    } finally {
      setIsDeletingUser(false);
    }
  }, [userToDelete, settings.serverUrl, currentUser, users, fetchUsers, onCurrentUserChange]);

  const cancelDeleteUser = useCallback(() => {
    setShowDeleteUserConfirm(false);
    setUserToDelete(null);
  }, []);

  // Save all settings to backend database
  const handleSaveAllSettings = useCallback(async () => {
    if (!currentUser || !settings.serverUrl) {
      setSaveSettingsMessage('❌ No user selected or server not available');
      setTimeout(() => setSaveSettingsMessage(''), 3000);
      return;
    }

    setIsSavingSettings(true);
    setSaveSettingsMessage('💾 Saving all settings...');

    try {
      const response = await queuedFetch(`${settings.serverUrl}/settings/users/${currentUser.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.id,
          settings: {
            chat_model: settings.model,
            memory_model: settings.memoryModel,
            timezone: settings.timezone,
            persona: settings.persona,
            persona_text: selectedPersonaText,
            ui_preferences: settings.uiPreferences || {},
            custom_settings: settings.customSettings || {}
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Settings saved successfully:', data);
        setSaveSettingsMessage('✅ Settings saved successfully!');
      } else {
        const errorData = await response.text();
        console.error('Failed to save settings:', errorData);
        setSaveSettingsMessage('❌ Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaveSettingsMessage('❌ Error saving settings');
    } finally {
      setIsSavingSettings(false);
      setTimeout(() => setSaveSettingsMessage(''), 3000);
    }
  }, [currentUser, settings, selectedPersonaText]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isUserDropdownOpen && !event.target.closest('.user-selector-dropdown')) {
        setIsUserDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isUserDropdownOpen]);

  const disconnectMcpServer = useCallback(async (serverId) => {
    if (!settings.serverUrl) {
      return;
    }
    try {
      setIsLoadingMcp(true);
      setMcpMessage(t('settings.mcp.disconnectingFrom', { serverId }));
      
      const response = await queuedFetch(`${settings.serverUrl}/mcp/marketplace/disconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_id: serverId })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setMcpMessage(`✅ ${t('settings.mcp.disconnectedSuccess', { serverId })}`);
          // Refresh the marketplace to update connection status
          await fetchMcpMarketplace();
          await searchMcpMarketplace(mcpSearchQuery);
        } else {
          setMcpMessage(`❌ ${data.error}`);
        }
      } else {
        setMcpMessage('❌ Failed to disconnect from server');
      }
    } catch (error) {
      console.error('Error disconnecting MCP server:', error);
      setMcpMessage(`❌ ${t('settings.mcp.disconnectionError')}`);
    } finally {
      setIsLoadingMcp(false);
      setTimeout(() => setMcpMessage(''), 5000);
    }
  }, [settings.serverUrl, fetchMcpMarketplace, searchMcpMarketplace, mcpSearchQuery]);

  const applyPersonaTemplate = useCallback(async (personaName) => {
    if (!settings.serverUrl) {
      console.log('applyPersonaTemplate: serverUrl not available yet');
      return;
    }
    try {
      const response = await queuedFetch(`${settings.serverUrl}/personas/apply_template`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          persona_name: personaName,
        }),
      });

      if (response.ok) {
        // Refresh the core memory persona text
        fetchCoreMemoryPersona();
        console.log(`Applied persona template: ${personaName}`);
      } else {
        console.error('Failed to apply persona template');
      }
    } catch (error) {
      console.error('Error applying persona template:', error);
    }
  }, [settings.serverUrl, fetchCoreMemoryPersona]);

  // Fetch initial data only when serverUrl is available
  useEffect(() => {
    if (settings.serverUrl) {
      console.log('SettingsPanel: serverUrl is available, fetching initial data');
      fetchPersonaDetails();
      fetchCoreMemoryPersona();
      fetchCurrentModel();
      fetchCurrentMemoryModel();
      fetchCurrentTimezone();
      fetchCustomModels();
      fetchMcpMarketplace();
      fetchUsers();
    }
  // Only run when serverUrl changes, not when the fetch functions change
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings.serverUrl]);

  // Fetch current models and timezone whenever settings panel becomes visible
  useEffect(() => {
    if (isVisible && settings.serverUrl) {
      console.log('SettingsPanel: became visible, refreshing current models and timezone');
      fetchCurrentModel();
      fetchCurrentMemoryModel();
      fetchCurrentTimezone();
      fetchCustomModels();
      fetchMcpMarketplace();
      // Don't fetch users again on visibility change to avoid循环
      // Also refresh MCP status to ensure connections are shown correctly
      refreshMcpStatus();
    }
  // Only run when visibility or serverUrl changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isVisible, settings.serverUrl]);

  // Refresh all backend data when backend reconnects
  useEffect(() => {
    if (settings.lastBackendRefresh && settings.serverUrl) {
      console.log('SettingsPanel: backend reconnected, refreshing all data');
      fetchPersonaDetails();
      fetchCoreMemoryPersona();
      fetchCurrentModel();
      fetchCurrentMemoryModel();
      fetchCurrentTimezone();
      fetchCustomModels();
      fetchMcpMarketplace();
      fetchUsers();
    }
  // Only run when backend refresh timestamp or serverUrl changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings.lastBackendRefresh, settings.serverUrl]);

  // Handle MCP search and filtering
  useEffect(() => {
    if (settings.serverUrl && mcpMarketplace.servers.length > 0) {
      searchMcpMarketplace(mcpSearchQuery);
    }
  }, [mcpSearchQuery, selectedCategory, searchMcpMarketplace, settings.serverUrl, mcpMarketplace.servers.length]);

  const handlePersonaChange = async (newPersona) => {
    console.log('handlePersonaChange called with:', newPersona);
    console.log('personaDetails:', personaDetails);
    console.log('settings.serverUrl:', settings.serverUrl);
    
    if (!settings.serverUrl) {
      console.error('Cannot change persona: serverUrl not available');
      setUpdateMessage(`❌ ${t('settings.messages.serverNotAvailable')}`);
      return;
    }
    
    // Only update the settings, don't apply template to backend yet
    handleInputChange('persona', newPersona);
    
    // Apply the template regardless of whether personaDetails is loaded
    // The backend will handle checking if the persona exists
    setIsApplyingTemplate(true);
    setUpdateMessage(t('settings.messages.applyingPersonaTemplate'));
    
    try {
      console.log(`Applying persona template: ${newPersona}`);
      
      const response = await queuedFetch(`${settings.serverUrl}/personas/apply_template`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          persona_name: newPersona,
        }),
      });

      console.log('Response status:', response.status);
      
      if (response.ok) {
        // Immediately refresh the core memory persona text
        await fetchCoreMemoryPersona();
        setUpdateMessage(`✅ ${t('settings.messages.personaTemplateAppliedSuccess')}`);
        console.log(`Successfully applied and updated persona: ${newPersona}`);
      } else {
        const errorData = await response.text();
        console.error('Failed to apply persona template:', errorData);
        setUpdateMessage(`❌ ${t('settings.messages.personaTemplateApplyFailed')}`);
      }
    } catch (error) {
      console.error('Error applying persona template:', error);
      setUpdateMessage(`❌ ${t('settings.messages.personaTemplateApplyError')}`);
    } finally {
      setIsApplyingTemplate(false);
      // Clear message after 2 seconds
      setTimeout(() => setUpdateMessage(''), 2000);
    }
  };

    const handlePersonaTemplateChange = async (newPersona) => {
    console.log('handlePersonaTemplateChange called with:', newPersona);
    
    // Only update the edit-mode template selection (don't update main settings)
    setSelectedTemplateInEdit(newPersona);
    
    // Load the template text without updating backend
    if (personaDetails[newPersona]) {
      // Use cached persona details
      setSelectedPersonaText(personaDetails[newPersona]);
      setUpdateMessage(`📝 ${t('settings.messages.templateLoaded')}`);
      setTimeout(() => setUpdateMessage(''), 3000);
    } else {
      // Fallback: refresh persona details if not found
      setIsApplyingTemplate(true);
      setUpdateMessage(t('settings.messages.loadingTemplate'));
      
      try {
        if (!settings.serverUrl) {
          setUpdateMessage(`❌ ${t('settings.messages.serverNotAvailable')}`);
          return;
        }
        
        const response = await queuedFetch(`${settings.serverUrl}/personas`);
        if (response.ok) {
          const data = await response.json();
          setPersonaDetails(data.personas);
          
          if (data.personas[newPersona]) {
            setSelectedPersonaText(data.personas[newPersona]);
            setUpdateMessage(`📝 ${t('settings.messages.templateLoaded')}`);
          } else {
            setUpdateMessage(`❌ ${t('settings.messages.templateNotFound')}`);
          }
        } else {
          setUpdateMessage(`❌ ${t('settings.messages.loadTemplatesFailed')}`);
        }
      } catch (error) {
        console.error('Error loading persona template:', error);
        setUpdateMessage(`❌ ${t('settings.messages.loadTemplateError')}`);
      } finally {
        setIsApplyingTemplate(false);
        setTimeout(() => setUpdateMessage(''), 3000);
      }
    }
  };

  const handleModelChange = async (newModel) => {
    console.log('handleModelChange called with:', newModel);
    
    if (!settings.serverUrl) {
      console.error('Cannot change model: serverUrl not available');
      setModelUpdateMessage(`❌ ${t('settings.messages.serverNotAvailable')}`);
      return;
    }
    
    handleInputChange('model', newModel);
    
    setIsChangingModel(true);
    setModelUpdateMessage(t('settings.messages.changingChatModel'));
    
    try {
      console.log(`Setting chat agent model: ${newModel}`);
      
      const response = await queuedFetch(`${settings.serverUrl}/models/set`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: newModel,
        }),
      });

      console.log('Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.success) {
          setModelUpdateMessage(`✅ ${t('settings.messages.chatModelSetSuccess')}`);
          console.log(`Successfully set chat agent model: ${newModel}`);
          
          // Show initialization message when model is successfully set
          setModelUpdateMessage(`🔄 ${t('settings.messages.initializingChatAgent')}`);
          
          // Automatically check for API keys after model change
          if (onApiKeyCheck) {
            console.log('Checking API keys for new model...');
            setTimeout(() => {
              onApiKeyCheck();
            }, 500); // Small delay to allow backend to update
          }
        } else {
          // Handle case where backend returned success: false
          if (data.missing_keys && data.missing_keys.length > 0) {
            // If there are missing API keys, immediately open the API key modal
            console.log(`Missing API keys for chat model '${newModel}': ${data.missing_keys.join(', ')}`);
            setModelUpdateMessage('🔑 Opening API key configuration...');
            
            if (onApiKeyRequired) {
              // Create retry function for this model change
              const retryFunction = () => handleModelChange(newModel);
              
              // Small delay to show the message before opening modal
              setTimeout(() => {
                onApiKeyRequired(data.missing_keys, newModel, newModel, 'chat', retryFunction);
              }, 500);
            }
          } else {
            // Show error message for other types of failures
            let errorMessage = data.message || t('settings.messages.failedToSetChatModel');
            setModelUpdateMessage(`❌ ${errorMessage}`);
            console.error('Chat model set failed:', data);
          }
        }
      } else {
        const errorData = await response.text();
        console.error('Failed to set chat agent model:', errorData);
        setModelUpdateMessage(`❌ ${t('settings.messages.failedToSetChatModel')}`);
      }
    } catch (error) {
      console.error('Error setting chat agent model:', error);
      setModelUpdateMessage(`❌ ${t('settings.messages.errorSettingChatModel')}`);
    } finally {
      setIsChangingModel(false);
      // Clear message after 2 seconds
      setTimeout(() => setModelUpdateMessage(''), 2000);
    }
  };

  const handleMemoryModelChange = async (newModel) => {
    console.log('handleMemoryModelChange called with:', newModel);
    
    if (!settings.serverUrl) {
      console.error('Cannot change memory model: serverUrl not available');
      setMemoryModelUpdateMessage(`❌ ${t('settings.messages.serverNotAvailable')}`);
      return;
    }
    
    handleInputChange('memoryModel', newModel);
    
    setIsChangingMemoryModel(true);
    setMemoryModelUpdateMessage(t('settings.messages.changingMemoryModel'));
    
    try {
      console.log(`Setting memory manager model: ${newModel}`);
      
      const response = await queuedFetch(`${settings.serverUrl}/models/memory/set`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: newModel,
        }),
      });

      console.log('Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.success) {
          setMemoryModelUpdateMessage(`✅ ${t('settings.messages.memoryModelSetSuccess')}`);
          console.log(`Successfully set memory manager model: ${newModel}`);
          
          // Show initialization message when model is successfully set
          setMemoryModelUpdateMessage(`🔄 ${t('settings.messages.initializingMemoryManager')}`);
          
          // Automatically check for API keys after memory model change
          if (onApiKeyCheck) {
            console.log('Checking API keys for new memory model...');
            setTimeout(() => {
              onApiKeyCheck();
            }, 500); // Small delay to allow backend to update
          }
        } else {
          // Handle case where backend returned success: false
          if (data.missing_keys && data.missing_keys.length > 0) {
            // If there are missing API keys, immediately open the API key modal
            console.log(`Missing API keys for memory model '${newModel}': ${data.missing_keys.join(', ')}`);
            setMemoryModelUpdateMessage('🔑 Opening API key configuration...');
            
            if (onApiKeyRequired) {
              // Create retry function for this model change
              const retryFunction = () => handleMemoryModelChange(newModel);
              
              // Small delay to show the message before opening modal
              setTimeout(() => {
                onApiKeyRequired(data.missing_keys, newModel, newModel, 'memory', retryFunction);
              }, 500);
            }
          } else {
            // Show error message for other types of failures
            let errorMessage = data.message || t('settings.messages.failedToSetMemoryModel');
            setMemoryModelUpdateMessage(`❌ ${errorMessage}`);
            console.error('Memory model set failed:', data);
          }
        }
      } else {
        const errorData = await response.text();
        console.error('Failed to set memory manager model:', errorData);
        setMemoryModelUpdateMessage(`❌ ${t('settings.messages.failedToSetMemoryModel')}`);
      }
    } catch (error) {
      console.error('Error setting memory manager model:', error);
      setMemoryModelUpdateMessage(`❌ ${t('settings.messages.errorSettingMemoryModel')}`);
    } finally {
      setIsChangingMemoryModel(false);
      // Clear message after 2 seconds
      setTimeout(() => setMemoryModelUpdateMessage(''), 2000);
    }
  };

  const handleTimezoneChange = async (newTimezone) => {
    console.log('handleTimezoneChange called with:', newTimezone);
    
    if (!settings.serverUrl) {
      console.error('Cannot change timezone: serverUrl not available');
      setTimezoneUpdateMessage(`❌ ${t('settings.messages.serverNotAvailable')}`);
      return;
    }
    
    handleInputChange('timezone', newTimezone);
    
    setIsChangingTimezone(true);
    setTimezoneUpdateMessage(t('settings.messages.changingTimezone'));
    
    try {
      console.log(`Setting timezone: ${newTimezone}`);
      
      const response = await queuedFetch(`${settings.serverUrl}/timezone/set`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          timezone: newTimezone,
        }),
      });

      console.log('Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        setTimezoneUpdateMessage(`✅ ${t('settings.messages.timezoneSetSuccess')}`);
        console.log(`Successfully set timezone: ${newTimezone}`);
      } else {
        const errorData = await response.text();
        console.error('Failed to set timezone:', errorData);
        setTimezoneUpdateMessage(`❌ ${t('settings.messages.failedToSetTimezone')}`);
      }
    } catch (error) {
      console.error('Error setting timezone:', error);
      setTimezoneUpdateMessage(`❌ ${t('settings.messages.errorSettingTimezone')}`);
    } finally {
      setIsChangingTimezone(false);
      // Clear message after 2 seconds
      setTimeout(() => setTimezoneUpdateMessage(''), 2000);
    }
  };

  const handlePersonaTextChange = (event) => {
    setSelectedPersonaText(event.target.value);
  };

  const updatePersonaText = async () => {
    if (!settings.serverUrl) {
      console.error('Cannot update persona text: serverUrl not available');
      setUpdateMessage(`❌ ${t('settings.messages.serverNotAvailable')}`);
      return;
    }
    
    setIsUpdatingPersona(true);
    setUpdateMessage('Updating core memory persona...');
    
    try {
      const response = await queuedFetch(`${settings.serverUrl}/personas/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: selectedPersonaText,
        }),
      });

      if (response.ok) {
        setUpdateMessage('✅ Core memory persona updated successfully!');
        // Update the main settings with the selected template
        if (selectedTemplateInEdit) {
          handleInputChange('persona', selectedTemplateInEdit);
        }
        // Stay in edit mode - don't close automatically
      } else {
        const errorData = await response.text();
        console.error('Failed to update core memory persona:', errorData);
        setUpdateMessage('❌ Failed to update core memory persona');
      }
    } catch (error) {
      console.error('Error updating core memory persona:', error);
      setUpdateMessage('❌ Error updating core memory persona');
    } finally {
      setIsUpdatingPersona(false);
      // Clear message after 2 seconds
      setTimeout(() => setUpdateMessage(''), 2000);
    }
  };

  const baseModels = [
    'deepseek-chat',
    'deepseek-reasoner',
    'gpt-4o-mini',
    'gpt-4o',
    'gpt-4.1-mini',
    'gpt-4.1',
    'claude-3-5-sonnet-20241022',
    'gemini-2.0-flash',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-1.5-pro',
    'gemini-2.0-flash-lite'
  ];

  // Combine base models with custom models
  const models = [...baseModels, ...customModels];

  // Memory models support both Gemini and OpenAI models, plus custom models
  const baseMemoryModels = [
    'deepseek-chat',
    'deepseek-reasoner',
    'gemini-2.0-flash',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gpt-4o-mini',
    'gpt-4o',
    'gpt-4.1-mini',
    'gpt-4.1',
  ];

  // Combine base memory models with custom models
  const memoryModels = [...baseMemoryModels, ...customModels];

  // Convert personaDetails object to array format for dropdown
  const personas = Object.keys(personaDetails).map(key => ({
    value: key,
    label: key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }));

  const timezones = [
    'America/New_York (UTC-5:00)',
    'America/Los_Angeles (UTC-8:00)',
    'America/Chicago (UTC-6:00)',
    'America/Denver (UTC-7:00)',
    'America/Toronto (UTC-5:00)',
    'America/Vancouver (UTC-8:00)',
    'Europe/London (UTC+0:00)',
    'Europe/Paris (UTC+1:00)',
    'Europe/Berlin (UTC+1:00)',
    'Europe/Rome (UTC+1:00)',
    'Europe/Madrid (UTC+1:00)',
    'Europe/Amsterdam (UTC+1:00)',
    'Europe/Stockholm (UTC+1:00)',
    'Europe/Moscow (UTC+3:00)',
    'Asia/Tokyo (UTC+9:00)',
    'Asia/Shanghai (UTC+8:00)',
    'Asia/Seoul (UTC+9:00)',
    'Asia/Hong_Kong (UTC+8:00)',
    'Asia/Singapore (UTC+8:00)',
    'Asia/Bangkok (UTC+7:00)',
    'Asia/Jakarta (UTC+7:00)',
    'Asia/Manila (UTC+8:00)',
    'Asia/Kolkata (UTC+5:30)',
    'Asia/Dubai (UTC+4:00)',
    'Asia/Tehran (UTC+3:30)',
    'Australia/Sydney (UTC+10:00)',
    'Australia/Melbourne (UTC+10:00)',
    'Australia/Perth (UTC+8:00)',
    'Pacific/Auckland (UTC+12:00)',
    'Pacific/Honolulu (UTC-10:00)',
    'Africa/Cairo (UTC+2:00)',
    'Africa/Lagos (UTC+1:00)',
    'Africa/Johannesburg (UTC+2:00)',
    'America/Sao_Paulo (UTC-3:00)',
    'America/Buenos_Aires (UTC-3:00)',
    'America/Mexico_City (UTC-6:00)'
  ];

  return (
    <div className="settings-panel">
      <div className="settings-header">
        <h2>{t('settings.title')}</h2>
        <p>{t('settings.subtitle')}</p>
      </div>

      <div className="settings-content">
        {/* User Selection Section - Moved to top */}
        <div className="settings-section">
          <h3>👥 {t('settings.userSelection.title')}</h3>

          <div className="setting-item">
            <label htmlFor="user-selector">{t('settings.userSelection.currentUser')}</label>
            <div className="user-selector-container">
              <div className="user-selector-with-add">
                <div
                  className={`user-selector-dropdown ${isUserDropdownOpen ? 'open' : ''}`}
                  onClick={() => setIsUserDropdownOpen(!isUserDropdownOpen)}
                >
                  <div className="user-selector-current">
                    {isLoadingUsers ? (
                      <span className="loading-text">🔄 {t('settings.userSelection.loadingUsers')}</span>
                    ) : currentUser ? (
                      <span className="current-user-display">
                        {currentUser.name}
                      </span>
                    ) : (
                      <span className="no-user-selected">{t('settings.userSelection.noUserSelected')}</span>
                    )}
                    <span className={`dropdown-arrow ${isUserDropdownOpen ? 'up' : 'down'}`}>
                      {isUserDropdownOpen ? '▲' : '▼'}
                    </span>
                  </div>

                  {isUserDropdownOpen && !isLoadingUsers && (
                    <div className="user-dropdown-list">
                      {users.length > 0 ? (
                        users.map(user => (
                          <div
                            key={user.id}
                            className={`user-dropdown-item ${currentUser?.id === user.id ? 'selected' : ''}`}
                          >
                            <div
                              className="user-dropdown-info"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleUserSelection(user);
                              }}
                            >
                              <span className="user-dropdown-name">{user.name}</span>
                              {currentUser?.id === user.id && (
                                <span className="selected-indicator">✓</span>
                              )}
                            </div>
                            <button
                              className="delete-user-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteUser(user);
                              }}
                              title={t('settings.userSelection.deleteUser')}
                            >
                              🗑️
                            </button>
                          </div>
                        ))
                      ) : (
                        <div className="no-users-dropdown">{t('settings.userSelection.noUsersAvailable')}</div>
                      )}
                    </div>
                  )}
                </div>
                <button
                  className="add-user-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowAddUserModal(true);
                  }}
                  title={t('settings.userSelection.addUserTooltip')}
                >
                  + {t('settings.userSelection.addUser')}
                </button>
              </div>
            </div>
            <span className="setting-description">
              {t('settings.userSelection.description')}
            </span>
          </div>
        </div>

        <div className="settings-section">
          <h3>{t('settings.sections.model')}</h3>

          <div className="setting-item">
            <label htmlFor="model-select">{t('settings.chatModel')}</label>
            <div className="model-select-container">
              <select
                id="model-select"
                value={settings.model}
                onChange={(e) => handleModelChange(e.target.value)}
                className="setting-select"
                disabled={isChangingModel}
              >
                {models.map(model => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <button
                className="add-model-button"
                onClick={() => {
                  setEditingModel(null);
                  setShowLocalModelModal(true);
                }}
                title={t('settings.descriptions.addModelTooltip')}
                disabled={isChangingModel}
              >
                {t('settings.add')}
              </button>
            </div>
            <span className="setting-description">
              {isChangingModel ? t('settings.descriptions.changingChatModel') : t('settings.descriptions.chatModel')}
            </span>
            {modelUpdateMessage && (
              <span className={`update-message ${modelUpdateMessage.includes('✅') ? 'success' : modelUpdateMessage.includes('Changing') ? 'info' : 'error'}`}>
                {modelUpdateMessage}
              </span>
            )}
            
            {/* 自定义模型管理 */}
            {customModels.length > 0 && (
              <div className="custom-models-section">
                <h4>{t('settings.customModels')}</h4>
                <div className="custom-models-list">
                  {customModels.map(modelName => (
                    <div key={modelName} className="custom-model-item">
                      <span className="custom-model-name">{modelName}</span>
                      <div className="custom-model-actions">
                        <button
                          className="edit-model-button"
                          onClick={() => handleEditModel(modelName)}
                          title={t('localModel.form.editModel')}
                          disabled={isChangingModel}
                        >
                          ✏️
                        </button>
                        <button
                          className="delete-model-button"
                          onClick={() => handleDeleteModel(modelName)}
                          title={t('localModel.form.deleteModel')}
                          disabled={isChangingModel}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="setting-item">
            <label htmlFor="memory-model-select">{t('settings.memoryModel')}</label>
            <div className="model-select-container">
              <select
                id="memory-model-select"
                value={settings.memoryModel || settings.model}
                onChange={(e) => handleMemoryModelChange(e.target.value)}
                className="setting-select"
                disabled={isChangingMemoryModel}
              >
                {memoryModels.map(model => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <button
                className="add-model-button"
                onClick={() => {
                  setEditingModel(null);
                  setShowLocalModelModal(true);
                }}
                title={t('settings.descriptions.addModelTooltip')}
                disabled={isChangingMemoryModel}
              >
                {t('settings.add')}
              </button>
            </div>
            <span className="setting-description">
              {isChangingMemoryModel ? t('settings.descriptions.changingMemoryModel') : t('settings.descriptions.memoryModel')}
            </span>
            {memoryModelUpdateMessage && (
              <span className={`update-message ${memoryModelUpdateMessage.includes('✅') ? 'success' : memoryModelUpdateMessage.includes('Changing') ? 'info' : 'error'}`}>
                {memoryModelUpdateMessage}
              </span>
            )}
          </div>

          {/* Persona Display/Editor */}
          <div className="setting-item persona-container">
            <label>{t('settings.persona')}</label>
            
            {!isEditingPersona ? (
              /* Display Mode */
              <div className="persona-display-mode">
                <div className="persona-display-text">
                  {selectedPersonaText || t('settings.descriptions.loadingPersona')}
                </div>
                <button
                  onClick={() => {
                    setIsEditingPersona(true);
                    setSelectedTemplateInEdit(settings.persona); // Initialize with current persona
                  }}
                  className="edit-persona-btn"
                  disabled={isApplyingTemplate}
                >
                  ✏️ {t('settings.personaEdit')}
                </button>
              </div>
            ) : (
              /* Edit Mode */
              <div className="persona-edit-mode">
                <div className="persona-template-selector">
                  <label htmlFor="persona-select">{t('settings.applyTemplate')}</label>
                  <select
                    id="persona-select"
                    value={selectedTemplateInEdit}
                    onChange={(e) => handlePersonaTemplateChange(e.target.value)}
                    className="setting-select"
                    disabled={isApplyingTemplate}
                  >
                    {personas.map(persona => (
                      <option key={persona.value} value={persona.value}>
                        {persona.label}
                      </option>
                    ))}
                  </select>
                  <span className="setting-description">
                    {isApplyingTemplate ? t('settings.descriptions.loadingTemplate') : t('settings.descriptions.templateSelector')}
                  </span>
                </div>
                
                <div className="persona-text-editor">
                  <label htmlFor="persona-text">{t('settings.editPersonaText')}</label>
                  <textarea
                    id="persona-text"
                    value={selectedPersonaText}
                    onChange={handlePersonaTextChange}
                    className="persona-textarea"
                    placeholder={t('settings.descriptions.personaPlaceholder')}
                    rows={6}
                    disabled={isApplyingTemplate}
                  />
                </div>
                
                <div className="persona-edit-actions">
                  <button
                    onClick={updatePersonaText}
                    disabled={isUpdatingPersona || isApplyingTemplate}
                    className="save-persona-btn"
                  >
                    {isUpdatingPersona ? t('settings.states.saving') : `💾 ${t('settings.buttons.save')}`}
                  </button>
                  <button
                    onClick={() => {
                      setIsEditingPersona(false);
                      setSelectedTemplateInEdit('');
                      setUpdateMessage('');
                    }}
                    className="cancel-persona-btn"
                    disabled={isUpdatingPersona || isApplyingTemplate}
                  >
                    {t('settings.buttons.cancel')}
                  </button>
                  {updateMessage && (
                    <span className={`update-message ${updateMessage.includes('✅') ? 'success' : updateMessage.includes('Applying') || updateMessage.includes('Updating') ? 'info' : 'error'}`}>
                      {updateMessage}
                    </span>
                  )}
                </div>
              </div>
            )}
            
            <span className="setting-description">
              {isEditingPersona 
                ? t('settings.descriptions.personaEdit')
                : t('settings.descriptions.personaDisplay')
              }
            </span>
          </div>
        </div>

        <div className="settings-section">
          <h3>{t('settings.sections.preferences')}</h3>
          
          {/* Language */}
          <div className="setting-item">
            <label htmlFor="language-select">{t('settings.language')}</label>
            <select
              id="language-select"
              value={i18n.language?.startsWith('zh') ? 'zh' : 'en'}
              onChange={(e) => i18n.changeLanguage(e.target.value)}
              className="setting-select"
            >
              <option value="en">English</option>
              <option value="zh">
                {i18n.language?.startsWith('zh') ? '中文简体' : 'Chinese Simplified (中文简体)'}
              </option>
            </select>
            <span className="setting-description">
              {t('settings.languageDescription')}
            </span>
          </div>
          
          <div className="setting-item">
            <label htmlFor="timezone-select">{t('settings.timezone')}</label>
            <select
              id="timezone-select"
              value={settings.timezone}
              onChange={(e) => handleTimezoneChange(e.target.value)}
              className="setting-select"
              disabled={isChangingTimezone}
            >
              {timezones.map(tz => (
                <option key={tz} value={tz}>
                  {tz.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
            <span className="setting-description">
              {isChangingTimezone ? t('settings.descriptions.changingTimezone') : t('settings.descriptions.timezone')}
            </span>
            {timezoneUpdateMessage && (
              <span className={`update-message ${timezoneUpdateMessage.includes('✅') ? 'success' : timezoneUpdateMessage.includes('Changing') ? 'info' : 'error'}`}>
                {timezoneUpdateMessage}
              </span>
            )}
          </div>
        </div>

        <div className="settings-section">
          <h3>{t('settings.sections.apiKeys')}</h3>
          
          <div className="setting-item">
            <label>{t('settings.apiKeyManagement')}</label>
            <div className="api-key-actions">
              <button
                onClick={() => {
                  // Force API key modal to open for manual updates
                  if (onApiKeyCheck) {
                    onApiKeyCheck(true); // Pass true to force modal open regardless of missing keys
                  }
                }}
                className="api-key-update-btn"
              >
                {`🔧 ${t('settings.updateApiKeys')}`}
              </button>
              {apiKeyMessage && (
                <span className={`update-message ${apiKeyMessage.includes('✅') ? 'success' : apiKeyMessage.includes('Checking') ? 'info' : 'error'}`}>
                  {apiKeyMessage}
                </span>
              )}
            </div>
            <span className="setting-description">
              {t('settings.descriptions.apiKeyManagement')}
            </span>
          </div>
        </div>

        <div className="settings-section">
          <div className="section-header-with-action">
            <div>
              <h3>🔧 {t('settings.mcp.title')}</h3>
              <p>{t('settings.mcp.description')}</p>
            </div>
            <button
              onClick={refreshMcpStatus}
              disabled={isLoadingMcp}
              className="refresh-mcp-btn"
              title={t('settings.mcp.refreshTooltip')}
            >
              🔄 {t('settings.mcp.refresh')}
            </button>
          </div>
          
          <div className="mcp-marketplace">
            {/* Search and Filter Controls */}
            <div className="mcp-controls">
              <div className="mcp-search">
                <input
                  type="text"
                  placeholder={t('settings.mcp.searchPlaceholder')}
                  value={mcpSearchQuery}
                  onChange={(e) => setMcpSearchQuery(e.target.value)}
                  className="mcp-search-input"
                />
              </div>
              <div className="mcp-filter">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="mcp-category-select"
                >
                  {mcpMarketplace.categories.map(category => (
                    <option key={category} value={category}>
                      {category === 'All' ? t('settings.mcp.filterAll') : category}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Status Message */}
            {mcpMessage && (
              <div className={`mcp-message ${mcpMessage.includes('✅') ? 'success' : mcpMessage.includes('❌') ? 'error' : 'info'}`}>
                {mcpMessage}
              </div>
            )}

            {/* Loading State */}
            {isLoadingMcp && (
              <div className="mcp-loading">🔄 {t('settings.mcp.loading')}</div>
            )}

            {/* MCP Tools List */}
            <div className="mcp-servers-list">
              {mcpSearchResults.map(server => (
                <div key={server.id} className="mcp-server-item">
                  <div className="mcp-server-header">
                    <div className="mcp-server-info">
                      <h4 className="mcp-server-name">{server.name}</h4>
                      <span className="mcp-server-category">{server.category}</span>
                      {server.is_connected && <span className="mcp-connected-badge">✅ {t('settings.mcp.connected')}</span>}
                    </div>
                    <div className="mcp-server-actions">
                      {server.is_connected ? (
                        <button
                          onClick={() => disconnectMcpServer(server.id)}
                          disabled={isLoadingMcp}
                          className="mcp-disconnect-btn"
                        >
                          {t('settings.mcp.disconnect')}
                        </button>
                      ) : (
                        <button
                          onClick={() => connectMcpServer(server.id)}
                          disabled={isLoadingMcp}
                          className="mcp-connect-btn"
                        >
                          {t('settings.mcp.connect')}
                        </button>
                      )}
                    </div>
                  </div>
                  <p className="mcp-server-description">{server.description}</p>
                  <div className="mcp-server-details">
                    {server.author && <span className="mcp-author">{t('settings.mcp.author', { author: server.author })}</span>}
                    {server.tags && server.tags.length > 0 && (
                      <div className="mcp-tags">
                        {server.tags.map(tag => (
                          <span key={tag} className="mcp-tag">{tag}</span>
                        ))}
                      </div>
                    )}
                    {server.requirements && server.requirements.length > 0 && (
                      <div className="mcp-requirements">
                        <strong>{t('settings.mcp.requirements')}</strong> {server.requirements.join(', ')}
                      </div>
                    )}
                    {server.documentation_url && (
                      <a 
                        href={server.documentation_url} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="mcp-github-link"
                      >
                        📖 {t('settings.mcp.documentation')}
                      </a>
                    )}
                  </div>
                </div>
              ))}
              
              {!isLoadingMcp && mcpSearchResults.length === 0 && (
                <div className="mcp-no-results">
                  {mcpSearchQuery ? t('settings.mcp.noResults') : t('settings.mcp.noResultsDefault')}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Save All Settings Section */}
        <div className="settings-section save-settings-section">
          <div className="save-settings-container">
            <button
              onClick={handleSaveAllSettings}
              disabled={isSavingSettings || !currentUser}
              className="save-all-settings-btn"
            >
              {isSavingSettings ? '💾 Saving...' : '💾 Save All Settings'}
            </button>
            {saveSettingsMessage && (
              <span className={`update-message ${saveSettingsMessage.includes('✅') ? 'success' : saveSettingsMessage.includes('Saving') ? 'info' : 'error'}`}>
                {saveSettingsMessage}
              </span>
            )}
            <span className="setting-description">
              Save all current settings (models, timezone, persona) and associate them with the current user
            </span>
          </div>
        </div>

        <div className="settings-section">
          <h3>{t('settings.sections.about')}</h3>
          <div className="about-info">
            <p><strong>{t('settings.about.name')}</strong></p>
            <p>{t('settings.about.version')} 0.1.4</p>
            <p>{t('settings.about.description')}</p>
            <div className="about-links">
              <button 
                className="link-button"
                onClick={() => window.open('https://docs.mirix.io', '_blank')}
              >
                📖 {t('settings.about.docs')}
              </button>
              <button 
                className="link-button"
                onClick={() => window.open('https://github.com/Mirix-AI/MIRIX/issues', '_blank')}
              >
                🐛 {t('settings.about.reportIssue')}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Local Model Modal */}
      <LocalModelModal
        isOpen={showLocalModelModal}
        onClose={() => {
          setShowLocalModelModal(false);
          setEditingModel(null);
        }}
        serverUrl={settings.serverUrl}
        editingModel={editingModel}
        onSuccess={(modelName) => {
          // Refresh custom models list and optionally switch to the new model
          fetchCustomModels();
          console.log(`Custom model '${modelName}' ${editingModel ? 'updated' : 'added'} successfully`);
          setEditingModel(null);
        }}
      />

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="modal-overlay">
          <div className="modal-content delete-confirm-modal">
            <div className="modal-header">
              <h3>{t('localModel.form.deleteModel')}</h3>
            </div>
            <div className="modal-body">
              <p>{t('localModel.form.confirmDelete')}</p>
              <p><strong>{modelToDelete}</strong></p>
            </div>
            <div className="modal-actions">
              <button
                className="cancel-button"
                onClick={cancelDeleteModel}
                disabled={isDeletingModel}
              >
                {t('localModel.form.cancel')}
              </button>
              <button
                className="delete-button"
                onClick={confirmDeleteModel}
                disabled={isDeletingModel}
              >
                {isDeletingModel ? t('settings.states.deleting') : t('localModel.form.deleteModel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Gmail Credentials Modal */}
      {showGmailModal && (
        <div className="modal-overlay">
          <div className="modal-content gmail-modal">
            <div className="modal-header">
              <h3>📧 {t('settings.modals.gmail.title')}</h3>
              <button className="modal-close-btn" onClick={handleGmailModalClose}>×</button>
            </div>
            <div className="modal-body">
              <p className="gmail-modal-description">
                {t('settings.modals.gmail.description')}
              </p>
              <div className="gmail-setup-steps">
                <ol>
                  <li>{t('settings.modals.gmail.step1')} <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noopener noreferrer">Google Cloud Console</a></li>
                  <li>{t('settings.modals.gmail.step2')}</li>
                  <li>{t('settings.modals.gmail.step3')}</li>
                  <li>{t('settings.modals.gmail.step4')}</li>
                </ol>
              </div>
              
              <div className="gmail-form">
                <div className="form-group">
                  <label htmlFor="gmail-client-id">{t('settings.modals.gmail.clientId')}</label>
                  <input
                    id="gmail-client-id"
                    type="text"
                    value={gmailCredentials.clientId}
                    onChange={(e) => setGmailCredentials(prev => ({...prev, clientId: e.target.value}))}
                    placeholder={t('settings.modals.gmail.clientIdPlaceholder')}
                    className="gmail-input"
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="gmail-client-secret">{t('settings.modals.gmail.clientSecret')}</label>
                  <input
                    id="gmail-client-secret"
                    type="password"
                    value={gmailCredentials.clientSecret}
                    onChange={(e) => setGmailCredentials(prev => ({...prev, clientSecret: e.target.value}))}
                    placeholder={t('settings.modals.gmail.clientSecretPlaceholder')}
                    className="gmail-input"
                  />
                </div>
              </div>
            </div>
            
            <div className="modal-footer">
              <button className="modal-btn secondary" onClick={handleGmailModalClose}>
                {t('settings.modals.gmail.cancel')}
              </button>
              <button 
                className="modal-btn primary" 
                onClick={handleGmailConnect}
                disabled={!gmailCredentials.clientId.trim() || !gmailCredentials.clientSecret.trim()}
              >
                {t('settings.modals.gmail.connectButton')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add User Modal */}
      {showAddUserModal && (
        <div className="modal-overlay">
          <div className="modal-content add-user-modal">
            <div className="modal-header">
              <h3>👤 {t('settings.modals.addUser.title')}</h3>
              <button className="modal-close-btn" onClick={() => setShowAddUserModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <p className="add-user-description">
                {t('settings.modals.addUser.description')}
              </p>

              <div className="add-user-form">
                <div className="form-group">
                  <label htmlFor="new-user-name">{t('settings.modals.addUser.userName')}</label>
                  <input
                    id="new-user-name"
                    type="text"
                    value={newUserName}
                    onChange={(e) => setNewUserName(e.target.value)}
                    placeholder={t('settings.modals.addUser.userNamePlaceholder')}
                    className="add-user-input"
                    autoFocus
                  />
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="modal-btn secondary" onClick={() => setShowAddUserModal(false)}>
                {t('settings.modals.addUser.cancel')}
              </button>
              <button
                className="modal-btn primary"
                onClick={handleCreateUser}
                disabled={!newUserName.trim()}
              >
                {t('settings.modals.addUser.createButton')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete User Confirmation Modal */}
      {showDeleteUserConfirm && (
        <div className="modal-overlay">
          <div className="modal-content delete-confirm-modal">
            <div className="modal-header">
              <h3>{t('settings.modals.deleteUser.title')}</h3>
            </div>
            <div className="modal-body">
              <p>{t('settings.modals.deleteUser.description')}</p>
              <p><strong>{userToDelete?.name}</strong></p>
              <p className="warning-text">{t('settings.modals.deleteUser.warning')}</p>
            </div>
            <div className="modal-actions">
              <button
                className="cancel-button"
                onClick={cancelDeleteUser}
                disabled={isDeletingUser}
              >
                {t('settings.modals.deleteUser.cancel')}
              </button>
              <button
                className="delete-button"
                onClick={confirmDeleteUser}
                disabled={isDeletingUser}
              >
                {isDeletingUser ? t('settings.states.deleting') : t('settings.modals.deleteUser.deleteButton')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPanel; 