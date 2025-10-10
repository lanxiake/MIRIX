import React, { useState, useEffect } from 'react';
import queuedFetch from '../utils/requestQueue';
import './LocalModelModal.css';
import { useTranslation } from 'react-i18next';

function LocalModelModal({ isOpen, onClose, serverUrl, onSuccess, editingModel = null }) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    model_name: '',
    model_endpoint: '',
    api_key: '',
    model_provider: 'openai-compatible',
    temperature: 0.7,
    max_tokens: 4096,
    maximum_length: 32768
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [originalModelId, setOriginalModelId] = useState(null);
  
  const isEditMode = !!editingModel;

  // 加载编辑模式的数据
  useEffect(() => {
    if (isEditMode && editingModel && isOpen) {
      // 从模型名称生成模型ID
      const modelId = editingModel.replace(/[^a-zA-Z0-9_.-]/g, '_');
      setOriginalModelId(modelId);
      
      // 获取模型详细配置
      const fetchModelDetail = async () => {
        try {
          const response = await queuedFetch(`${serverUrl}/models/custom/${modelId}`);
          if (response.ok) {
            const result = await response.json();
            if (result.success && result.config) {
              const config = result.config;
              setFormData({
                model_name: config.model_name || '',
                model_endpoint: config.model_endpoint || '',
                api_key: config.api_key || '',
                model_provider: config.model_provider || 'openai-compatible',
                temperature: config.generation_config?.temperature || 0.7,
                max_tokens: config.generation_config?.max_tokens || 4096,
                maximum_length: config.generation_config?.context_window || 32768
              });
            }
          }
        } catch (error) {
          console.error('Error fetching model detail:', error);
          setError('获取模型配置失败');
        }
      };
      
      fetchModelDetail();
    } else if (!isEditMode) {
      // 重置表单为添加模式
      setFormData({
        model_name: '',
        model_endpoint: '',
        api_key: '',
        model_provider: 'openai-compatible',
        temperature: 0.7,
        max_tokens: 4096,
        maximum_length: 32768
      });
      setOriginalModelId(null);
    }
  }, [isEditMode, editingModel, isOpen, serverUrl]);

  // 模型提供商预设配置
  const providerPresets = {
    'openai-compatible': {
      baseUrl: '',
      placeholder: 'https://api.openai.com/v1',
      temperature: 0.7,
      max_tokens: 4096,
      maximum_length: 32768,
      requiresApiKey: true
    },
    'ollama-local': {
      baseUrl: 'http://localhost:11434/v1',
      placeholder: 'http://localhost:11434/v1',
      temperature: 0.8,
      max_tokens: 2048,
      maximum_length: 8192,
      requiresApiKey: false
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'temperature' ? parseFloat(value) || 0 : 
              name === 'max_tokens' || name === 'maximum_length' ? parseInt(value) || 0 : value
    }));
  };

  // 处理模型提供商变更
  const handleProviderChange = (e) => {
    const provider = e.target.value;
    const preset = providerPresets[provider];
    
    setFormData(prev => ({
      ...prev,
      model_provider: provider,
      model_endpoint: preset.baseUrl,
      api_key: preset.requiresApiKey ? prev.api_key : 'EMPTY',
      temperature: preset.temperature,
      max_tokens: preset.max_tokens,
      maximum_length: preset.maximum_length
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.model_name.trim()) {
      setError(t('localModel.errors.modelNameRequired'));
      return;
    }
    if (!formData.model_endpoint.trim()) {
      setError(t('localModel.errors.endpointRequired'));
      return;
    }
    // 只有在需要API密钥的提供商时才验证API密钥
    const preset = providerPresets[formData.model_provider];
    if (preset.requiresApiKey && !formData.api_key.trim()) {
      setError(t('localModel.errors.apiKeyRequired'));
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const url = isEditMode 
        ? `${serverUrl}/models/custom/${originalModelId}`
        : `${serverUrl}/models/custom/add`;
      const method = isEditMode ? 'PUT' : 'POST';
      
      const response = await queuedFetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Reset form
          setFormData({
            model_name: '',
            model_endpoint: '',
            api_key: '',
            model_provider: 'openai-compatible',
            temperature: 0.7,
            max_tokens: 4096,
            maximum_length: 32768
          });
          
          // Call success callback
          if (onSuccess) {
            onSuccess(formData.model_name);
          }
          
          onClose();
        } else {
          setError(result.message || 'Failed to add custom model');
        }
      } else {
        const errorData = await response.text();
        setError(`Failed to add custom model: ${errorData}`);
      }
    } catch (error) {
      console.error('Error adding custom model:', error);
      setError('Error adding custom model. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    // Reset form when closing
    setFormData({
      model_name: '',
      model_endpoint: '',
      api_key: '',
      model_provider: 'openai-compatible',
      temperature: 0.7,
      max_tokens: 4096,
      maximum_length: 32768
    });
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="local-model-modal">
        <div className="modal-header">
          <h3>{isEditMode ? t('localModel.form.editModel') : t('localModel.title')}</h3>
          <button className="close-button" onClick={handleClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="model_provider">
              {t('localModel.form.modelProvider')} <span className="required">{t('localModel.form.required')}</span>
            </label>
            <select
              id="model_provider"
              name="model_provider"
              value={formData.model_provider}
              onChange={handleProviderChange}
              disabled={isLoading}
              required
            >
              <option value="openai-compatible">{t('localModel.form.providerOpenAI')}</option>
              <option value="ollama-local">{t('localModel.form.providerOllama')}</option>
            </select>
            <small className="field-description">
              {t('localModel.form.modelProviderDescription')}
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="model_name">
              {t('localModel.form.modelName')} <span className="required">{t('localModel.form.required')}</span>
            </label>
            <input
              type="text"
              id="model_name"
              name="model_name"
              value={formData.model_name}
              onChange={handleInputChange}
              placeholder={t('localModel.form.modelNamePlaceholder')}
              disabled={isLoading}
              required
            />
            <small className="field-description">
              {t('localModel.form.modelNameDescription')}
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="model_endpoint">
              {t('localModel.form.baseUrl')} <span className="required">{t('localModel.form.required')}</span>
            </label>
            <input
              type="url"
              id="model_endpoint"
              name="model_endpoint"
              value={formData.model_endpoint}
              onChange={handleInputChange}
              placeholder={providerPresets[formData.model_provider].placeholder}
              disabled={isLoading}
              required
            />
            <small className="field-description">
              {t('localModel.form.baseUrlDescription')}
            </small>
          </div>

          {providerPresets[formData.model_provider].requiresApiKey && (
            <div className="form-group">
              <label htmlFor="api_key">
                {t('localModel.form.apiKey')} <span className="required">{t('localModel.form.required')}</span>
              </label>
              <input
                type="password"
                id="api_key"
                name="api_key"
                value={formData.api_key}
                onChange={handleInputChange}
                placeholder={t('localModel.form.apiKeyPlaceholder')}
                disabled={isLoading}
                required
              />
              <small className="field-description">
                {t('localModel.form.apiKeyDescription')}
              </small>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="temperature">
              {t('localModel.form.temperature')}
            </label>
            <input
              type="number"
              id="temperature"
              name="temperature"
              value={formData.temperature}
              onChange={handleInputChange}
              min="0"
              max="2"
              step="0.1"
              disabled={isLoading}
            />
            <small className="field-description">
              {t('localModel.form.temperatureDescription')}
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="max_tokens">
              {t('localModel.form.maxTokens')}
            </label>
            <input
              type="number"
              id="max_tokens"
              name="max_tokens"
              value={formData.max_tokens}
              onChange={handleInputChange}
              min="1"
              max="100000"
              disabled={isLoading}
            />
            <small className="field-description">
              {t('localModel.form.maxTokensDescription')}
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="maximum_length">
              {t('localModel.form.maximumLength')}
            </label>
            <input
              type="number"
              id="maximum_length"
              name="maximum_length"
              value={formData.maximum_length}
              onChange={handleInputChange}
              min="1"
              max="200000"
              disabled={isLoading}
            />
            <small className="field-description">
              {t('localModel.form.maximumLengthDescription')}
            </small>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="modal-actions">
            <button
              type="button"
              onClick={handleClose}
              className="cancel-button"
              disabled={isLoading}
            >
              {t('localModel.form.cancel')}
            </button>
            <button
              type="submit"
              className="submit-button"
              disabled={isLoading}
            >
              {isLoading 
                ? (isEditMode ? t('localModel.form.updating') : t('localModel.form.adding'))
                : (isEditMode ? t('localModel.form.editModel') : t('localModel.form.addModel'))
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default LocalModelModal; 