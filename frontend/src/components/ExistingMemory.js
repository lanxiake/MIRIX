import React, { useState, useEffect } from 'react';
import './ExistingMemory.css';
import MemoryTreeVisualization from './MemoryTreeVisualization';
import UploadExportModal from './UploadExportModal';
import queuedFetch from '../utils/requestQueue';
import { useTranslation } from 'react-i18next';

const ExistingMemory = ({ settings, currentUser }) => {
  const { t } = useTranslation();
  const [activeSubTab, setActiveSubTab] = useState('past-events');
  const [memoryData, setMemoryData] = useState({
    'past-events': [],
    'semantic': [],
    'procedural': [],
    'docs-files': [],
    'core-understanding': [],
    'credentials': []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedItems, setExpandedItems] = useState(new Set());
  // State for memory view modes (list or tree) for each memory type
  const [viewModes, setViewModes] = useState({
    'past-events': 'list',
    'semantic': 'list', 
    'procedural': 'list',
    'docs-files': 'list'
  });
  // State for Upload & Export modal
  const [showUploadExportModal, setShowUploadExportModal] = useState(false);
  
  // State for Reflexion processing
  const [isReflexionProcessing, setIsReflexionProcessing] = useState(false);
  const [reflexionMessage, setReflexionMessage] = useState('');
  const [reflexionSuccess, setReflexionSuccess] = useState(null);
  
  // State for tracking edits to core memories
  const [editingCoreMemories, setEditingCoreMemories] = useState(new Set());
  const [editedCoreMemories, setEditedCoreMemories] = useState({});
  const [savingBlocks, setSavingBlocks] = useState(new Set());
  const [saveErrors, setSaveErrors] = useState({});
  const [saveSuccesses, setSaveSuccesses] = useState({});

  // State for memory management (delete and edit)
  const [selectedMemories, setSelectedMemories] = useState(new Set());
  const [editingMemory, setEditingMemory] = useState(null);
  const [editingMemoryData, setEditingMemoryData] = useState({});
  
  // State for memory deletion confirmation
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [memoriesToDelete, setMemoriesToDelete] = useState({ type: '', ids: [] });
  const [deletingMemories, setDeletingMemories] = useState(new Set());

  // Helper function to get view mode for current tab
  const getCurrentViewMode = () => viewModes[activeSubTab] || 'list';
  
  // Helper function to set view mode for current tab
  const setCurrentViewMode = (mode) => {
    setViewModes(prev => ({
      ...prev,
      [activeSubTab]: mode
    }));
  };

  // Function to highlight matching text
  const highlightText = (text, query) => {
    if (!text || !query.trim()) {
      return text;
    }

    const searchTerm = query.trim();
    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) => 
      regex.test(part) ? (
        <span key={index} className="search-highlight">{part}</span>
      ) : part
    );
  };

  // Function to render text with preserved newlines
  const renderTextWithNewlines = (text, query) => {
    if (!text) return text;
    
    // Split by newlines first
    const lines = text.split('\n');
    
    return lines.map((line, index) => (
      <React.Fragment key={index}>
        {query && query.trim() ? highlightText(line, query) : line}
        {index < lines.length - 1 && <br />}
      </React.Fragment>
    ));
  };

  // Fetch memory data for each type
  const fetchMemoryData = async (memoryType) => {
    try {
      setLoading(true);
      setError(null);

      let endpoint = '';
      switch (memoryType) {
        case 'past-events':
          endpoint = '/memory/episodic';
          break;
        case 'semantic':
          endpoint = '/memory/semantic';
          break;
        case 'procedural':
          endpoint = '/memory/procedural';
          break;
        case 'docs-files':
          endpoint = '/memory/resources';
          break;
        case 'core-understanding':
          endpoint = '/memory/core';
          break;
        case 'credentials':
          endpoint = '/memory/credentials';
          break;
        default:
          return;
      }

      const response = await queuedFetch(`${settings.serverUrl}${endpoint}${currentUser ? `?user_id=${currentUser.id}` : ''}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${memoryType}: ${response.statusText}`);
      }

      const data = await response.json();
      setMemoryData(prev => ({
        ...prev,
        [memoryType]: data
      }));
    } catch (err) {
      console.error(`Error fetching ${memoryType}:`, err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Filter memories based on search query
  const filterMemories = (memories, query) => {
    if (!query.trim()) {
      return memories;
    }

    const searchTerm = query.toLowerCase();
    
    return memories.filter(item => {
      // Search in different fields depending on memory type
      const searchableText = [
        item.content,
        item.description,
        item.title,
        item.name,
        item.filename,
        item.service,
        item.aspect,
        item.category,
        item.understanding,
        item.context,
        item.summary,
        item.details,
        item.event_type,
        item.type,
        item.caption,
        item.entry_type,
        item.source,
        item.sensitivity,
        // Search in tags if they exist
        ...(item.tags || []),
        // Search in emotions if they exist
        ...(item.emotions || [])
      ]
        .filter(Boolean) // Remove null/undefined values
        .join(' ')
        .toLowerCase();

      return searchableText.includes(searchTerm);
    });
  };

  // Toggle expand/collapse for semantic memory details
  const toggleExpanded = (itemId) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  // Check if search query matches in details for auto-expansion
  const shouldAutoExpand = (item, query) => {
    if (!query.trim() || !item.details) return false;
    
    const searchTerm = query.toLowerCase();
    const detailsText = item.details.toLowerCase();
    
    return detailsText.includes(searchTerm);
  };

  // Auto-expand items when search query matches their details
  useEffect(() => {
    if ((activeSubTab === 'semantic' || activeSubTab === 'past-events') && searchQuery.trim()) {
      const currentData = memoryData[activeSubTab] || [];
      const itemsToExpand = new Set();
      
      currentData.forEach((item, index) => {
        if (shouldAutoExpand(item, searchQuery)) {
          if (activeSubTab === 'semantic') {
            itemsToExpand.add(`semantic-${index}`);
          } else if (activeSubTab === 'past-events') {
            itemsToExpand.add(`episodic-${index}`);
          }
        }
      });
      
      setExpandedItems(itemsToExpand);
    } else if (!searchQuery.trim()) {
      // Clear expanded items when search is cleared
      setExpandedItems(new Set());
    }
  }, [searchQuery, memoryData, activeSubTab]);

  // Fetch data when component mounts or active tab changes
  useEffect(() => {
    fetchMemoryData(activeSubTab);
    // Clear expanded items when switching tabs
    setExpandedItems(new Set());
    // Clear edited core memories when switching away from core-understanding
    if (activeSubTab !== 'core-understanding') {
      setEditingCoreMemories(new Set());
      setEditedCoreMemories({});
      setSavingBlocks(new Set());
      setSaveErrors({});
      setSaveSuccesses({});
    }
  }, [activeSubTab, settings.serverUrl]);

  // Refresh data when backend reconnects
  useEffect(() => {
    if (settings.lastBackendRefresh && settings.serverUrl) {
      console.log('ExistingMemory: backend reconnected, refreshing data');
      fetchMemoryData(activeSubTab);
    }
  }, [settings.lastBackendRefresh, settings.serverUrl, activeSubTab]);

  // Memory management functions
  const handleDeleteMemory = async (memoryType, memoryId) => {
    /**
     * 删除单个记忆
     */
    try {
      setDeletingMemories(prev => new Set([...prev, memoryId]));
      
      const response = await queuedFetch(`${settings.serverUrl}/memory/${memoryType}/${memoryId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // 刷新记忆数据
          fetchMemoryData(activeSubTab);
          // 显示成功消息
          console.log('记忆删除成功:', result.message);
        } else {
          console.error('删除记忆失败:', result.message);
        }
      } else {
        console.error('删除记忆请求失败:', response.statusText);
      }
    } catch (error) {
      console.error('删除记忆时发生错误:', error);
    } finally {
      setDeletingMemories(prev => {
        const newSet = new Set(prev);
        newSet.delete(memoryId);
        return newSet;
      });
    }
  };

  const handleEditMemory = async (memoryType, memoryId, updates) => {
    /**
     * 更新记忆内容
     */
    try {
      const response = await queuedFetch(`${settings.serverUrl}/memory/${memoryType}/${memoryId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          memory_type: memoryType,
          memory_id: memoryId,
          updates: updates
        })
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // 刷新记忆数据
          fetchMemoryData(activeSubTab);
                   // 清空编辑状态
         setEditingMemory(null);
         setEditingMemoryData({});
          // 显示成功消息
          console.log('记忆更新成功:', result.message);
        } else {
          console.error('更新记忆失败:', result.message);
        }
      } else {
        console.error('更新记忆请求失败:', response.statusText);
      }
    } catch (error) {
      console.error('更新记忆时发生错误:', error);
    }
  };

     const startEditMemory = (memoryId, currentData) => {
     /**
      * 开始编辑记忆
      */
     setEditingMemory(memoryId);
     setEditingMemoryData(currentData);
   };

   const cancelEditMemory = () => {
     /**
      * 取消编辑记忆
      */
     setEditingMemory(null);
     setEditingMemoryData({});
   };

  const confirmDeleteMemory = (memoryType, memoryId) => {
    /**
     * 显示删除确认对话框
     */
    setMemoriesToDelete({ type: memoryType, ids: [memoryId] });
    setShowDeleteConfirm(true);
  };

  const executeDelete = () => {
    /**
     * 执行删除操作
     */
    const { type, ids } = memoriesToDelete;
    if (ids.length === 1) {
      handleDeleteMemory(type, ids[0]);
    }
    setShowDeleteConfirm(false);
    setMemoriesToDelete({ type: '', ids: [] });
  };

  const renderMemoryContent = () => {
    const currentViewMode = getCurrentViewMode();
    
    // Handle tree view for memory types that support it
    if (currentViewMode === 'tree') {
      const treeMemoryTypes = ['past-events', 'semantic', 'procedural', 'docs-files'];
      
      if (treeMemoryTypes.includes(activeSubTab)) {
        // Use generic tree visualization for all memory types
        const memoryTypeMap = {
          'past-events': 'episodic',
          'semantic': 'semantic',
          'procedural': 'procedural', 
          'docs-files': 'resource'
        };
        
        const memoryType = memoryTypeMap[activeSubTab];
        
        return (
          <MemoryTreeVisualization 
            memoryType={memoryType}
            serverUrl={settings.serverUrl}
            getItemTitle={(item) => {
              switch (memoryType) {
                case 'episodic':
                  return item.summary || 'Episodic Event';
                case 'semantic':
                  return item.title || item.name || item.summary || 'Semantic Item';
                case 'procedural': 
                  return item.summary || item.title || 'Procedure';
                case 'resource':
                  return item.filename || item.name || 'Resource';
                default:
                  return item.title || item.name || 'Memory Item';
              }
            }}
            getItemDetails={(item) => {
              return {
                summary: item.summary,
                details: item.details || item.content
              };
            }}
          />
        );
      }
    }

    const currentData = memoryData[activeSubTab] || [];
    const filteredData = filterMemories(currentData, searchQuery);

    if (loading) {
      return (
        <div className="memory-loading">
          <div className="loading-spinner"></div>
          <p>{t('memory.states.loading')}</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="memory-error">
          <p>{t('memory.states.error', { error })}</p>
          <button onClick={() => fetchMemoryData(activeSubTab)} className="retry-button">
            {t('memory.actions.retry')}
          </button>
        </div>
      );
    }

    if (currentData.length === 0) {
      return (
        <div className="memory-empty">
          <p>{t('memory.states.empty', { type: getMemoryTypeLabel(activeSubTab).toLowerCase() })}</p>
        </div>
      );
    }

    if (filteredData.length === 0 && searchQuery.trim()) {
      return (
        <div className="memory-empty">
          <p>{t('memory.search.noResults', { type: getMemoryTypeLabel(activeSubTab).toLowerCase(), query: searchQuery })}</p>
          <p>{t('memory.search.tryDifferent')}</p>
        </div>
      );
    }

    return (
      <div className="memory-items">
        {filteredData.map((item, index) => (
          activeSubTab === 'core-understanding' ? (
            // For core memory, don't add extra wrapper to avoid double containers
            <div key={index}>
              {renderMemoryItem(item, activeSubTab, index)}
            </div>
          ) : (
            // For other memory types, keep the wrapper
            <div key={index} className="memory-item">
              {renderMemoryItem(item, activeSubTab, index)}
            </div>
          )
        ))}
      </div>
    );
  };

  const renderMemoryItem = (item, type, index) => {
    switch (type) {
      case 'past-events':
        const episodicItemId = `episodic-${index}`;
        const isEpisodicExpanded = expandedItems.has(episodicItemId);
        const isEditingEpisodic = editingMemory === item.id;
        
        return (
          <div className="episodic-memory">
            <div className="memory-header">
              <div className="memory-timestamp">
                {item.timestamp ? new Date(item.timestamp).toLocaleString() : t('memory.details.unknownTime')}
              </div>
              <div className="memory-actions">
                <button 
                  className="edit-memory-btn"
                  onClick={() => startEditMemory(item.id, item)}
                  title="编辑记忆"
                >
                  ✏️
                </button>
                <button 
                  className="delete-memory-btn"
                  onClick={() => confirmDeleteMemory('episodic', item.id)}
                  disabled={deletingMemories.has(item.id)}
                  title="删除记忆"
                >
                  {deletingMemories.has(item.id) ? '⏳' : '🗑️'}
                </button>
              </div>
            </div>
            
            {isEditingEpisodic ? (
              <div className="memory-edit-form">
                <textarea
                  value={editingMemoryData.summary || ''}
                  onChange={(e) => setEditingMemoryData({...editingMemoryData, summary: e.target.value})}
                  className="edit-summary-input"
                  placeholder="编辑摘要..."
                />
                <div className="edit-actions">
                  <button 
                    className="save-edit-btn"
                    onClick={() => handleEditMemory('episodic', item.id, {summary: editingMemoryData.summary})}
                  >
                    保存
                  </button>
                  <button 
                    className="cancel-edit-btn"
                    onClick={cancelEditMemory}
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <div className="memory-content">{highlightText(item.summary, searchQuery)}</div>
            )}
            
            {item.details && (
              <div className="memory-details-section">
                <button 
                  className="expand-toggle-button"
                  onClick={() => toggleExpanded(episodicItemId)}
                  title={isEpisodicExpanded ? t('memory.actions.expandDetails') : t('memory.actions.collapseDetails')}
                >
                  {isEpisodicExpanded ? `▼ ${t('memory.actions.hideDetails')}` : `▶ ${t('memory.actions.showDetails')}`}
                </button>
                {isEpisodicExpanded && (
                  <div className="memory-details">{highlightText(item.details, searchQuery)}</div>
                )}
              </div>
            )}
          </div>
        );
      
      case 'semantic':
        const itemId = `semantic-${index}`;
        const isExpanded = expandedItems.has(itemId);
        const isEditingSemantic = editingMemory === item.id;
        
        return (
          <div className="semantic-memory">
            <div className="memory-header">
              <div className="memory-title">{highlightText(item.title || item.name, searchQuery)}</div>
              <div className="memory-actions">
                <button 
                  className="edit-memory-btn"
                  onClick={() => startEditMemory(item.id, item)}
                  title="编辑记忆"
                >
                  ✏️
                </button>
                <button 
                  className="delete-memory-btn"
                  onClick={() => confirmDeleteMemory('semantic', item.id)}
                  disabled={deletingMemories.has(item.id)}
                  title="删除记忆"
                >
                  {deletingMemories.has(item.id) ? '⏳' : '🗑️'}
                </button>
              </div>
            </div>
            
            {isEditingSemantic ? (
              <div className="memory-edit-form">
                <div className="edit-field">
                  <label>标题:</label>
                  <input
                    type="text"
                    value={editingMemoryData.title || editingMemoryData.name || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, title: e.target.value})}
                    className="edit-title-input"
                  />
                </div>
                <div className="edit-field">
                  <label>摘要:</label>
                  <textarea
                    value={editingMemoryData.summary || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, summary: e.target.value})}
                    className="edit-summary-input"
                    rows="3"
                  />
                </div>
                <div className="edit-field">
                  <label>详细内容:</label>
                  <textarea
                    value={editingMemoryData.details || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, details: e.target.value})}
                    className="edit-details-input"
                    rows="5"
                  />
                </div>
                <div className="edit-actions">
                  <button 
                    className="save-edit-btn"
                    onClick={() => handleEditMemory('semantic', item.id, {
                      title: editingMemoryData.title || editingMemoryData.name,
                      summary: editingMemoryData.summary,
                      details: editingMemoryData.details
                    })}
                  >
                    保存
                  </button>
                  <button 
                    className="cancel-edit-btn"
                    onClick={cancelEditMemory}
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <>
                {item.summary && <div className="memory-summary">{highlightText(item.summary, searchQuery)}</div>}
                {item.details && (
                  <div className="memory-details-section">
                    <button 
                      className="expand-toggle-button"
                      onClick={() => toggleExpanded(itemId)}
                      title={isExpanded ? t('memory.actions.expandDetails') : t('memory.actions.collapseDetails')}
                    >
                      {isExpanded ? `▼ ${t('memory.actions.hideDetails')}` : `▶ ${t('memory.actions.showDetails')}`}
                    </button>
                    {isExpanded && (
                      <div className="memory-details">{highlightText(item.details, searchQuery)}</div>
                    )}
                  </div>
                )}
                {item.last_updated && <div className="memory-updated">{t('memory.details.updated', { date: new Date(item.last_updated).toLocaleString() })}</div>}
                {item.tags && (
                  <div className="memory-tags">
                    {item.tags.map((tag, i) => (
                      <span key={i} className="memory-tag">{highlightText(tag, searchQuery)}</span>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        );

      case 'procedural':
        const isEditingProcedural = editingMemory === item.id;
        
        return (
          <div className="procedural-memory">
            <div className="memory-header">
              <div className="memory-title">{highlightText(item.summary, searchQuery)}</div>
              <div className="memory-actions">
                <button 
                  className="edit-memory-btn"
                  onClick={() => startEditMemory(item.id, item)}
                  title="编辑记忆"
                >
                  ✏️
                </button>
                <button 
                  className="delete-memory-btn"
                  onClick={() => confirmDeleteMemory('procedural', item.id)}
                  disabled={deletingMemories.has(item.id)}
                  title="删除记忆"
                >
                  {deletingMemories.has(item.id) ? '⏳' : '🗑️'}
                </button>
              </div>
            </div>
            
            {isEditingProcedural ? (
              <div className="memory-edit-form">
                <div className="edit-field">
                  <label>摘要:</label>
                  <input
                    type="text"
                    value={editingMemoryData.summary || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, summary: e.target.value})}
                    className="edit-title-input"
                  />
                </div>
                <div className="edit-field">
                  <label>内容/描述:</label>
                  <textarea
                    value={editingMemoryData.content || editingMemoryData.description || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, content: e.target.value})}
                    className="edit-summary-input"
                    rows="4"
                  />
                </div>
                <div className="edit-field">
                  <label>步骤 (每行一个步骤):</label>
                  <textarea
                    value={editingMemoryData.steps ? editingMemoryData.steps.join('\n') : ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, steps: e.target.value.split('\n').filter(step => step.trim())})}
                    className="edit-details-input"
                    rows="6"
                    placeholder="第一步&#10;第二步&#10;第三步..."
                  />
                </div>
                <div className="edit-actions">
                  <button 
                    className="save-edit-btn"
                    onClick={() => handleEditMemory('procedural', item.id, {
                      summary: editingMemoryData.summary,
                      content: editingMemoryData.content || editingMemoryData.description,
                      steps: editingMemoryData.steps
                    })}
                  >
                    保存
                  </button>
                  <button 
                    className="cancel-edit-btn"
                    onClick={cancelEditMemory}
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="memory-content">
                  {item.steps && item.steps.length > 0 ? (
                    <div className="memory-steps">
                      <strong>🎯 {t('memory.details.stepByStepGuide')}</strong>
                      <ol>
                        {item.steps.map((step, i) => (
                          <li key={i}>{highlightText(step, searchQuery)}</li>
                        ))}
                      </ol>
                    </div>
                  ) : (
                    <div>{highlightText(item.content || item.description || t('memory.details.noStepsAvailable'), searchQuery)}</div>
                  )}
                </div>
                {item.proficiency && <div className="memory-proficiency">{t('memory.details.proficiency', { value: highlightText(item.proficiency, searchQuery) })}</div>}
                {item.difficulty && <div className="memory-difficulty">{t('memory.details.difficulty', { value: highlightText(item.difficulty, searchQuery) })}</div>}
                {item.success_rate && <div className="memory-success-rate">{t('memory.details.successRate', { value: highlightText(item.success_rate, searchQuery) })}</div>}
                {item.time_to_complete && <div className="memory-time">{t('memory.details.timeToComplete', { value: highlightText(item.time_to_complete, searchQuery) })}</div>}
                {item.last_practiced && <div className="memory-practiced">{t('memory.details.lastPracticed', { date: new Date(item.last_practiced).toLocaleString() })}</div>}
                {item.prerequisites && item.prerequisites.length > 0 && (
                  <div className="memory-prerequisites">
                    {t('memory.details.prerequisites', { list: item.prerequisites.map(prereq => highlightText(prereq, searchQuery)).join(', ') })}
                  </div>
                )}
                {item.last_updated && <div className="memory-updated">{t('memory.details.updated', { date: new Date(item.last_updated).toLocaleString() })}</div>}
                {item.tags && (
                  <div className="memory-tags">
                    {item.tags.map((tag, i) => (
                      <span key={i} className="memory-tag">{highlightText(tag, searchQuery)}</span>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        );

      case 'docs-files':
        const isEditingResource = editingMemory === item.id;
        
        return (
          <div className="resource-memory">
            <div className="memory-header">
              <div className="memory-filename">{highlightText(item.filename || item.name, searchQuery)}</div>
              <div className="memory-actions">
                <button 
                  className="edit-memory-btn"
                  onClick={() => startEditMemory(item.id, item)}
                  title="编辑记忆"
                >
                  ✏️
                </button>
                <button 
                  className="delete-memory-btn"
                  onClick={() => confirmDeleteMemory('resource', item.id)}
                  disabled={deletingMemories.has(item.id)}
                  title="删除记忆"
                >
                  {deletingMemories.has(item.id) ? '⏳' : '🗑️'}
                </button>
              </div>
            </div>
            
            {isEditingResource ? (
              <div className="memory-edit-form">
                <div className="edit-field">
                  <label>文件名:</label>
                  <input
                    type="text"
                    value={editingMemoryData.filename || editingMemoryData.name || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, filename: e.target.value})}
                    className="edit-title-input"
                  />
                </div>
                <div className="edit-field">
                  <label>文件类型:</label>
                  <input
                    type="text"
                    value={editingMemoryData.type || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, type: e.target.value})}
                    className="edit-title-input"
                  />
                </div>
                <div className="edit-field">
                  <label>摘要/内容:</label>
                  <textarea
                    value={editingMemoryData.summary || editingMemoryData.content || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, summary: e.target.value})}
                    className="edit-summary-input"
                    rows="5"
                  />
                </div>
                <div className="edit-actions">
                  <button 
                    className="save-edit-btn"
                    onClick={() => handleEditMemory('resource', item.id, {
                      filename: editingMemoryData.filename || editingMemoryData.name,
                      type: editingMemoryData.type,
                      summary: editingMemoryData.summary || editingMemoryData.content
                    })}
                  >
                    保存
                  </button>
                  <button 
                    className="cancel-edit-btn"
                    onClick={cancelEditMemory}
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="memory-file-type">{highlightText(item.type || t('memory.details.unknownType'), searchQuery)}</div>
                <div className="memory-summary">{highlightText(item.summary || item.content, searchQuery)}</div>
                {item.last_accessed && (
                  <div className="memory-accessed">{t('memory.details.lastAccessed', { date: new Date(item.last_accessed).toLocaleString() })}</div>
                )}
                {item.size && <div className="memory-size">{t('memory.details.size', { size: item.size })}</div>}
              </>
            )}
          </div>
        );

      case 'core-understanding':
        const isCoreEditing = isCoreMemoryEditing(index);
        const currentContent = getCoreMemoryContent(item, index);
        const isSaving = savingBlocks.has(index);
        const saveError = saveErrors[index];
        const saveSuccess = saveSuccesses[index];
        
        return (
          <div className="core-memory">
            <div className="memory-aspect-header">
              <div className="memory-aspect">
                {highlightText(item.aspect || item.category, searchQuery)}
                {item.total_characters && item.max_characters && (
                  <span className="character-count-inline"> ({t('memory.details.characterCount', { current: currentContent.length, max: item.max_characters })})</span>
                )}
                {isCoreEditing && <span className="edited-indicator"> • {t('memory.details.editing')}</span>}
              </div>
              {!isCoreEditing && (
                <button
                  onClick={() => startEditingCoreMemory(index)}
                  className="edit-memory-button"
                >
                  ✏️ {t('memory.actions.edit')}
                </button>
              )}
            </div>
            
            {isCoreEditing ? (
              <div className="memory-understanding-editable">
                <textarea
                  value={currentContent}
                  onChange={(e) => handleCoreMemoryEdit(index, e.target.value)}
                  className="core-memory-textarea"
                  rows={Math.max(3, Math.ceil(currentContent.length / 80))}
                  placeholder={t('memory.details.enterCoreUnderstanding')}
                />
                <div className="core-memory-actions">
                  <button
                    onClick={() => saveCoreMemoryBlock(index, item)}
                    className="save-memory-button"
                    disabled={isSaving}
                  >
                    {isSaving ? `💾 ${t('memory.actions.saving')}` : `💾 ${t('memory.actions.save')}`}
                  </button>
                  <button
                    onClick={() => cancelEditingCoreMemory(index)}
                    className="cancel-memory-button"
                    disabled={isSaving}
                  >
                    ❌ {t('memory.actions.cancel')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="memory-understanding-display">
                <div className="memory-understanding">
                  {renderTextWithNewlines(item.understanding || item.content, searchQuery)}
                </div>
              </div>
            )}
            
            {/* Status messages for individual blocks */}
            {saveSuccess && (
              <div className="block-save-status success">
                ✅ {t('memory.reflexion.success')}
              </div>
            )}
            {saveError && (
              <div className="block-save-status error">
                ❌ {t('memory.states.error', { error: saveError })}
              </div>
            )}
            
            {item.last_updated && (
              <div className="memory-updated">{t('memory.details.updated', { date: new Date(item.last_updated).toLocaleString() })}</div>
            )}
          </div>
        );

      case 'credentials':
        const isEditingCredentials = editingMemory === item.id;
        
        return (
          <div className="credential-memory">
            <div className="memory-header">
              <div className="memory-credential-name">{highlightText(item.caption, searchQuery)}</div>
              <div className="memory-actions">
                <button 
                  className="edit-memory-btn"
                  onClick={() => startEditMemory(item.id, item)}
                  title="编辑记忆"
                >
                  ✏️
                </button>
                <button 
                  className="delete-memory-btn"
                  onClick={() => confirmDeleteMemory('credentials', item.id)}
                  disabled={deletingMemories.has(item.id)}
                  title="删除记忆"
                >
                  {deletingMemories.has(item.id) ? '⏳' : '🗑️'}
                </button>
              </div>
            </div>
            
            {isEditingCredentials ? (
              <div className="memory-edit-form">
                <div className="edit-field">
                  <label>标题:</label>
                  <input
                    type="text"
                    value={editingMemoryData.caption || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, caption: e.target.value})}
                    className="edit-title-input"
                  />
                </div>
                <div className="edit-field">
                  <label>类型:</label>
                  <input
                    type="text"
                    value={editingMemoryData.entry_type || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, entry_type: e.target.value})}
                    className="edit-title-input"
                  />
                </div>
                <div className="edit-field">
                  <label>内容:</label>
                  <textarea
                    value={editingMemoryData.content || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, content: e.target.value})}
                    className="edit-summary-input"
                    rows="3"
                    placeholder="注意：这是敏感信息"
                  />
                </div>
                <div className="edit-field">
                  <label>来源:</label>
                  <input
                    type="text"
                    value={editingMemoryData.source || ''}
                    onChange={(e) => setEditingMemoryData({...editingMemoryData, source: e.target.value})}
                    className="edit-title-input"
                  />
                </div>
                <div className="edit-actions">
                  <button 
                    className="save-edit-btn"
                    onClick={() => handleEditMemory('credentials', item.id, {
                      caption: editingMemoryData.caption,
                      entry_type: editingMemoryData.entry_type,
                      content: editingMemoryData.content,
                      source: editingMemoryData.source
                    })}
                  >
                    保存
                  </button>
                  <button 
                    className="cancel-edit-btn"
                    onClick={cancelEditMemory}
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="memory-credential-type">{highlightText(item.entry_type || t('memory.details.credentialType'), searchQuery)}</div>
                <div className="memory-credential-content">
                  {item.content || t('memory.details.credentialMasked')}
                </div>
                {item.source && (
                  <div className="memory-credential-source">{t('memory.details.source', { source: highlightText(item.source, searchQuery) })}</div>
                )}
                {item.sensitivity && (
                  <div className="memory-credential-sensitivity">
                    <span className={`sensitivity-badge sensitivity-${item.sensitivity}`}>
                      {t('memory.details.sensitivity', { level: item.sensitivity.charAt(0).toUpperCase() + item.sensitivity.slice(1) })}
                    </span>
                  </div>
                )}
              </>
            )}
          </div>
        );

      default:
        return <div className="memory-content">{JSON.stringify(item, null, 2)}</div>;
    }
  };

  const getMemoryTypeLabel = (type) => {
    switch (type) {
      case 'past-events': return t('memory.types.episodic');
      case 'semantic': return t('memory.types.semantic');
      case 'procedural': return t('memory.types.procedural');
      case 'docs-files': return t('memory.types.resource');
      case 'core-understanding': return t('memory.types.core');
      case 'credentials': return t('memory.types.credentials');
      default: return 'Memory';
    }
  };

  const getMemoryTypeIcon = (type) => {
    switch (type) {
      case 'past-events': return '📅';
      case 'semantic': return '🧠';
      case 'procedural': return '🛠️';
      case 'docs-files': return '📁';
      case 'core-understanding': return '💡';
      case 'credentials': return '🔐';
      default: return '💭';
    }
  };

  // Helper functions for core memory editing
  const startEditingCoreMemory = (index) => {
    setEditingCoreMemories(prev => new Set([...prev, index]));
    // Clear any previous save states for this block
    setSaveErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[index];
      return newErrors;
    });
    setSaveSuccesses(prev => {
      const newSuccesses = { ...prev };
      delete newSuccesses[index];
      return newSuccesses;
    });
  };

  const cancelEditingCoreMemory = (index) => {
    setEditingCoreMemories(prev => {
      const newSet = new Set(prev);
      newSet.delete(index);
      return newSet;
    });
    // Clear any edits for this block
    setEditedCoreMemories(prev => {
      const newEdited = { ...prev };
      delete newEdited[index];
      return newEdited;
    });
  };

  const handleCoreMemoryEdit = (index, newContent) => {
    setEditedCoreMemories(prev => ({
      ...prev,
      [index]: newContent
    }));
  };

  // Check if core memory is being edited
  const isCoreMemoryEditing = (index) => {
    return editingCoreMemories.has(index);
  };

  // Get the current content for a core memory (edited or original)
  const getCoreMemoryContent = (item, index) => {
    if (editedCoreMemories.hasOwnProperty(index)) {
      return editedCoreMemories[index];
    }
    return item.understanding || item.content || '';
  };

  // Save individual core memory block
  const saveCoreMemoryBlock = async (index, item) => {
    try {
      setSavingBlocks(prev => new Set([...prev, index]));
      setSaveErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[index];
        return newErrors;
      });
      setSaveSuccesses(prev => {
        const newSuccesses = { ...prev };
        delete newSuccesses[index];
        return newSuccesses;
      });

      const newContent = getCoreMemoryContent(item, index);
      const originalContent = item.understanding || item.content || '';

      if (newContent === originalContent) {
        // No changes, just exit edit mode
        setEditingCoreMemories(prev => {
          const newSet = new Set(prev);
          newSet.delete(index);
          return newSet;
        });
        return;
      }

      // Send update to server
      const response = await queuedFetch(`${settings.serverUrl}/core_memory/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          label: item.aspect || item.category,
          text: newContent
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to update core memory: ${response.statusText}`);
      }

      // Success - clear edit state and refresh data
      setEditingCoreMemories(prev => {
        const newSet = new Set(prev);
        newSet.delete(index);
        return newSet;
      });
      setEditedCoreMemories(prev => {
        const newEdited = { ...prev };
        delete newEdited[index];
        return newEdited;
      });
      
      setSaveSuccesses(prev => ({ ...prev, [index]: true }));
      setTimeout(() => {
        setSaveSuccesses(prev => {
          const newSuccesses = { ...prev };
          delete newSuccesses[index];
          return newSuccesses;
        });
      }, 3000);

      // Refresh the data to show updated content
      await fetchMemoryData('core-understanding');

    } catch (err) {
      console.error('Error saving core memory block:', err);
      setSaveErrors(prev => ({ ...prev, [index]: err.message }));
    } finally {
      setSavingBlocks(prev => {
        const newSet = new Set(prev);
        newSet.delete(index);
        return newSet;
      });
    }
  };

  // Handle reflexion request
  const handleReflexion = async () => {
    if (isReflexionProcessing) return; // Prevent multiple simultaneous requests
    
    try {
      setIsReflexionProcessing(true);
      setReflexionMessage('');
      setReflexionSuccess(null);
      
      console.log('Starting reflexion process...');
      
      const response = await queuedFetch(`${settings.serverUrl}/reflexion`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger reflexion: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success) {
        setReflexionSuccess(true);
        setReflexionMessage(result.message);
        console.log('Reflexion completed successfully:', result.message);
        
        // Optionally refresh memory data after reflexion
        // You can uncomment this if you want to refresh the current tab's data
        // await fetchMemoryData(activeSubTab);
      } else {
        setReflexionSuccess(false);
        setReflexionMessage(result.message || 'Reflexion failed');
        console.error('Reflexion failed:', result.message);
      }
      
    } catch (err) {
      console.error('Error triggering reflexion:', err);
      setReflexionSuccess(false);
      setReflexionMessage(err.message || 'Failed to trigger reflexion');
    } finally {
      setIsReflexionProcessing(false);
      
      // Clear the message after 5 seconds
      setTimeout(() => {
        setReflexionMessage('');
        setReflexionSuccess(null);
      }, 5000);
    }
  };

  return (
    <div className="existing-memory">
      <div className="memory-header">
        <div className="memory-subtabs">
          <div className="memory-subtabs-left">
            {['past-events', 'semantic', 'procedural', 'docs-files', 'core-understanding', 'credentials'].map(subTab => (
              <button
                key={subTab}
                className={`memory-subtab ${activeSubTab === subTab ? 'active' : ''}`}
                onClick={() => setActiveSubTab(subTab)}
              >
                <span className="subtab-icon">{getMemoryTypeIcon(subTab)}</span>
                <span className="subtab-label">{getMemoryTypeLabel(subTab)}</span>
              </button>
            ))}
          </div>
          <div className="memory-subtabs-right">
            <button
              className="memory-subtab upload-export-btn"
              onClick={() => setShowUploadExportModal(true)}
              title={t('memory.tooltips.uploadExport')}
            >
              <span className="subtab-icon">📤</span>
                              <span className="subtab-label">{t('memory.actions.uploadExport')}</span>
            </button>
            <button
              className="memory-subtab reflexion-btn"
              onClick={handleReflexion}
              disabled={isReflexionProcessing}
              title={t('memory.tooltips.reflexion')}
            >
              <span className="subtab-icon">
                {isReflexionProcessing ? '⏳' : '🧠'}
              </span>
              <span className="subtab-label">
                {isReflexionProcessing ? t('memory.actions.processing') : t('memory.actions.reflexion')}
              </span>
            </button>
          </div>
        </div>
      </div>
      
      <div className="memory-content">
        <div className="memory-search-and-actions">
          <div className="search-input-container">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder={t('memory.search.placeholder', { type: getMemoryTypeLabel(activeSubTab).toLowerCase() })}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
              disabled={getCurrentViewMode() === 'tree'}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="clear-search-button"
                title={t('memory.actions.clearSearch')}
              >
                ✕
              </button>
            )}
          </div>
          
          
          {['past-events', 'semantic', 'procedural', 'docs-files'].includes(activeSubTab) && (
            <div className="view-mode-toggle">
              <button
                onClick={() => setCurrentViewMode('list')}
                className={`view-mode-button ${getCurrentViewMode() === 'list' ? 'active' : ''}`}
                title={t('memory.tooltips.listView')}
              >
                📋 {t('memory.view.listView')}
              </button>
              <button
                onClick={() => setCurrentViewMode('tree')}
                className={`view-mode-button ${getCurrentViewMode() === 'tree' ? 'active' : ''}`}
                title={t('memory.tooltips.treeView')}
              >
                🌳 {t('memory.view.treeView')}
              </button>
            </div>
          )}
          

          
          <button 
            onClick={() => fetchMemoryData(activeSubTab)} 
            className="refresh-button"
            disabled={loading}
          >
            🔄 {t('memory.actions.refresh')}
          </button>
        </div>
        
        {/* Reflexion Status Message */}
        {reflexionMessage && (
          <div className={`reflexion-status ${reflexionSuccess ? 'success' : 'error'}`}>
            <span className="status-icon">
              {reflexionSuccess ? '✅' : '❌'}
            </span>
            <span className="status-message">{reflexionMessage}</span>
          </div>
        )}

        
        {renderMemoryContent()}
      </div>

      {/* Upload & Export Modal */}
      <UploadExportModal
        isOpen={showUploadExportModal}
        onClose={() => setShowUploadExportModal(false)}
        settings={settings}
        currentUser={currentUser}
      />

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>确认删除</h3>
            <p>
              您确定要删除这{memoriesToDelete.ids.length > 1 ? '些' : '个'}记忆吗？此操作无法撤销。
            </p>
            <div className="modal-actions">
              <button 
                className="cancel-button"
                onClick={() => setShowDeleteConfirm(false)}
              >
                取消
              </button>
              <button 
                className="delete-button"
                onClick={executeDelete}
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExistingMemory; 