import React, { useState, useRef } from 'react';
import queuedFetch from '../utils/requestQueue';
import './UploadExportModal.css';
import { useTranslation } from 'react-i18next';

function UploadExportModal({ isOpen, onClose, settings }) {
  const { t } = useTranslation();
  const fileInputRef = useRef(null);
  const [selectedMemoryTypes, setSelectedMemoryTypes] = useState({
    episodic: true,
    semantic: true,
    procedural: true,
    resource: true
  });
  const [exportPath, setExportPath] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [exportStatus, setExportStatus] = useState(null);
  
  // 上传相关状态
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const memoryTypes = [
    { key: 'episodic', label: t('uploadExport.memoryTypes.episodic'), icon: '📚', description: t('uploadExport.memoryTypeDescriptions.episodic') },
    { key: 'semantic', label: t('uploadExport.memoryTypes.semantic'), icon: '🧠', description: t('uploadExport.memoryTypeDescriptions.semantic') },
    { key: 'procedural', label: t('uploadExport.memoryTypes.procedural'), icon: '🔧', description: t('uploadExport.memoryTypeDescriptions.procedural') },
    { key: 'resource', label: t('uploadExport.memoryTypes.resource'), icon: '📁', description: t('uploadExport.memoryTypeDescriptions.resource') }
  ];

  const handleMemoryTypeToggle = (type) => {
    setSelectedMemoryTypes(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const handleBrowse = async () => {
    if (window.electronAPI && window.electronAPI.selectSavePath) {
      try {
        const result = await window.electronAPI.selectSavePath({
          title: t('uploadExport.descriptions.saveDialogTitle'),
          defaultName: t('uploadExport.descriptions.defaultFileName')
        });
        
        if (!result.canceled && result.filePath) {
          setExportPath(result.filePath);
        }
      } catch (error) {
        console.error('Error opening file dialog:', error);
        alert(t('uploadExport.alerts.browserFailed'));
      }
    } else {
      alert(t('uploadExport.alerts.browserUnavailable'));
    }
  };

  // 处理文件选择
  const handleFileSelect = async () => {
    // 检查是否在 Electron 环境中
    if (window.electronAPI && window.electronAPI.selectFiles) {
      // Electron 环境
      try {
        const result = await window.electronAPI.selectFiles({
          title: t('uploadExport.descriptions.selectFilesTitle'),
          filters: [
            { name: 'Document Files', extensions: ['md', 'txt', 'xlsx', 'xls', 'docx', 'pdf'] },
            { name: 'Markdown Files', extensions: ['md'] },
            { name: 'Text Files', extensions: ['txt'] },
            { name: 'Excel Files', extensions: ['xlsx', 'xls'] },
            { name: 'All Files', extensions: ['*'] }
          ],
          properties: ['openFile', 'multiSelections']
        });

        if (!result.canceled && result.filePaths && result.filePaths.length > 0) {
          setSelectedFiles(result.filePaths);
        }
      } catch (error) {
        console.error('Error opening file dialog:', error);
        alert(t('uploadExport.alerts.browserFailed'));
      }
    } else {
      // Web 环境 - 使用 HTML file input
      if (fileInputRef.current) {
        fileInputRef.current.click();
      }
    }
  };

  // 处理 Web 环境的文件选择
  const handleWebFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
      setSelectedFiles(files);
    }
    // 清空 input 值，以便可以重新选择相同文件
    event.target.value = '';
  };

  // 处理文件上传
  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      alert(t('uploadExport.alerts.noFilesSelected'));
      return;
    }

    setIsUploading(true);
    setUploadStatus({ success: [], failed: [] });

    for (const file of selectedFiles) {
      try {
        let fileContent;
        let fileName;
        
        // 检查是否在 Electron 环境中
        if (window.electronAPI && window.electronAPI.readFile) {
          // Electron 环境 - file 是文件路径字符串
          fileName = file.split(/[/\\]/).pop();
          fileContent = await window.electronAPI.readFile(file);
        } else {
          // Web 环境 - file 是 File 对象
          fileName = file.name;
          fileContent = await readFileAsBase64(file);
        }

        const response = await queuedFetch('/api/documents/upload', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            file_name: fileName,
            file_type: fileName.split('.').pop().toLowerCase(),
            content: fileContent,
            user_id: null
          }),
        });

        if (response.ok) {
          setUploadStatus(prev => ({
            ...prev,
            success: [...prev.success, fileName]
          }));
        } else {
          // 改进错误处理，处理非JSON响应
          let errorMessage = 'Unknown error';
          try {
            const errorData = await response.json();
            errorMessage = errorData.message || errorData.detail?.message || errorData.error || 'Unknown error';
          } catch (jsonError) {
            // 如果响应不是JSON格式，使用响应文本
            const errorText = await response.text();
            errorMessage = `Server error (${response.status}): ${errorText.substring(0, 100)}...`;
            console.error('Failed to parse error response as JSON:', jsonError);
            console.error('Raw error response:', errorText);
          }
          
          setUploadStatus(prev => ({
            ...prev,
            failed: [...prev.failed, { fileName, error: errorMessage }]
          }));
        }
      } catch (error) {
        console.error('Upload error:', error);
        // 改进错误处理，提供更详细的错误信息
        let errorMessage = 'Upload failed';
        if (error.name === 'SyntaxError' && error.message.includes('JSON')) {
          errorMessage = 'Server returned invalid response format';
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        const fileName = window.electronAPI && window.electronAPI.readFile 
          ? file.split(/[/\\]/).pop() 
          : file.name;
        setUploadStatus(prev => ({
          ...prev,
          failed: [...prev.failed, { fileName, error: errorMessage }]
        }));
      }
    }

    setIsUploading(false);
  };

  // Web 环境下读取文件为 Base64
  const readFileAsBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        // 移除 data:xxx;base64, 前缀
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleExport = async () => {
    if (!exportPath.trim()) {
      alert(t('uploadExport.alerts.pathRequired'));
      return;
    }

    const selectedTypes = Object.keys(selectedMemoryTypes).filter(
      type => selectedMemoryTypes[type]
    );

    if (selectedTypes.length === 0) {
      alert(t('uploadExport.alerts.selectTypes'));
      return;
    }

    setIsLoading(true);
    setExportStatus(null);

    try {
      const response = await queuedFetch(`${settings.serverUrl}/export/memories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: exportPath,
          memory_types: selectedTypes,
          include_embeddings: false
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setExportStatus({
          success: true,
          message: result.message,
          counts: result.exported_counts,
          total: result.total_exported
        });
      } else {
        const errorData = await response.json();
        const detail = String(errorData?.detail || '');
        const localized =
          detail.includes('At least one sheet must be visible') ? t('uploadExport.errors.atLeastOneSheetVisible') :
          detail.includes('No data') ? t('uploadExport.errors.noData') :
          detail.toLowerCase().includes('permission') ? t('uploadExport.errors.permissionDenied') :
          t('uploadExport.errors.unknown');

        setExportStatus({ success: false, message: localized });
      }
    } catch (error) {
      console.error('Export error:', error);
      setExportStatus({
        success: false,
        message: `${t('uploadExport.status.failed')}: ${error.message}`
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="upload-export-modal-overlay" onClick={onClose}>
      <div className="upload-export-modal" onClick={(e) => e.stopPropagation()}>
        <div className="upload-export-modal-header">
          <h2>📤 {t('uploadExport.title')}</h2>
          <button 
            className="upload-export-modal-close"
            onClick={onClose}
            title={t('uploadExport.form.close')}
          >
            ✕
          </button>
        </div>
        
        <div className="upload-export-modal-content">
          <div className="upload-export-modal-description">
            <p>{t('uploadExport.descriptions.modalDescription')}</p>
          </div>

          <div className="memory-types-section">
            <h3>{t('uploadExport.form.selectTypes')}</h3>
            <div className="memory-types-grid">
              {memoryTypes.map(type => (
                <div 
                  key={type.key}
                  className={`memory-type-card ${selectedMemoryTypes[type.key] ? 'selected' : ''}`}
                  onClick={() => handleMemoryTypeToggle(type.key)}
                >
                  <div className="memory-type-icon">{type.icon}</div>
                  <div className="memory-type-info">
                    <div className="memory-type-label">{type.label}</div>
                    <div className="memory-type-description">{type.description}</div>
                  </div>
                  <div className="memory-type-checkbox">
                    <input 
                      type="checkbox" 
                      checked={selectedMemoryTypes[type.key]}
                      onChange={() => {}}
                      readOnly
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="actions-section">
            <div className="upload-section">
              <h3>{t('uploadExport.sections.upload')}</h3>
              <p>{t('uploadExport.descriptions.uploadSection')}</p>
              
              {/* 文件选择区域 */}
              <div className="file-selection-area">
                {/* 隐藏的 file input 用于 Web 环境 */}
                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  multiple
                  accept=".md,.txt,.xlsx,.xls,.docx,.pdf"
                  onChange={handleWebFileSelect}
                />
                
                <button 
                  className="file-select-btn"
                  onClick={handleFileSelect}
                  disabled={isUploading}
                >
                  📁 选择文件
                </button>
                
                {selectedFiles.length > 0 && (
                  <div className="selected-files">
                    <h4>已选择的文件 ({selectedFiles.length}):</h4>
                    <div className="file-list">
                      {selectedFiles.map((file, index) => (
                        <div key={index} className="file-item">
                          <span className="file-name">
                            {window.electronAPI && window.electronAPI.readFile 
                              ? file.split(/[\\/]/).pop() 
                              : file.name}
                          </span>
                          <button 
                            className="remove-file-btn"
                            onClick={() => setSelectedFiles(files => files.filter((_, i) => i !== index))}
                            disabled={isUploading}
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <button 
                className="upload-btn"
                onClick={handleUpload}
                disabled={isUploading || selectedFiles.length === 0}
              >
                {isUploading ? `⏳ 上传中...` : `📤 ${t('uploadExport.form.upload')}`}
              </button>
              
              {/* 上传状态显示 */}
              {uploadStatus && (
                <div className={`upload-status ${uploadStatus.success ? 'success' : 'error'}`}>
                  <div className="status-message">{uploadStatus.message}</div>
                  {uploadStatus.results && (
                    <div className="upload-details">
                      {uploadStatus.results.map((result, index) => (
                        <div key={index} className={`file-result ${result.success ? 'success' : 'error'}`}>
                          <span className="file-name">{result.fileName}</span>
                          <span className="result-status">{result.success ? '✓' : '✗'}</span>
                          {!result.success && (
                            <span className="error-message">{result.message}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="export-section">
              <h3>{t('uploadExport.sections.export')}</h3>
              <p>{t('uploadExport.descriptions.exportSection')}</p>
              
              <div className="export-path-input">
                <label htmlFor="exportPath">{t('uploadExport.form.exportPath')}</label>
                <div className="path-input-group">
                  <input
                    id="exportPath"
                    type="text"
                    value={exportPath}
                    onChange={(e) => setExportPath(e.target.value)}
                    placeholder={t('uploadExport.form.pathPlaceholder')}
                    className="path-input"
                  />
                  <button 
                    type="button"
                    className="browse-btn"
                    onClick={handleBrowse}
                    title={t('uploadExport.form.browse')}
                  >
                    📁 {t('uploadExport.form.browse')}
                  </button>
                </div>
              </div>

              <button 
                className="export-btn"
                onClick={handleExport}
                disabled={isLoading}
              >
                {isLoading ? `⏳ ${t('uploadExport.form.exporting')}` : `📥 ${t('uploadExport.form.export')}`}
              </button>

              {exportStatus && (
                <div className={`export-status ${exportStatus.success ? 'success' : 'error'}`}>
                  <div className="status-message">{exportStatus.message}</div>
                  {exportStatus.success && exportStatus.counts && (
                    <div className="export-details">
                      <div className="total-exported">{t('uploadExport.status.exported', { total: exportStatus.total })}</div>
                      <div className="counts-breakdown">
                        {Object.entries(exportStatus.counts).map(([type, count]) => (
                          <span key={type} className="count-item">
                            {type === 'episodic' ? t('uploadExport.memoryTypes.episodic')
                              : type === 'semantic' ? t('uploadExport.memoryTypes.semantic')
                              : type === 'procedural' ? t('uploadExport.memoryTypes.procedural')
                              : type === 'resource' ? t('uploadExport.memoryTypes.resource')
                              : type}: {count}
                          </span>
                        ))}
                      </div>  
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UploadExportModal;