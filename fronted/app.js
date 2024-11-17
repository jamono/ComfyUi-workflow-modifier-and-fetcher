import React, { useState, useEffect } from 'react';
import { Plus, Folder, Download, Trash2, Upload, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [instances, setInstances] = useState([]);
  const [apiKeys, setApiKeys] = useState({
    huggingface: localStorage.getItem('hf_key') || '',
    civitai: localStorage.getItem('civitai_key') || ''
  });
  const [downloadProgress, setDownloadProgress] = useState({});
  const [error, setError] = useState(null);
  const [newInstanceId, setNewInstanceId] = useState('');

  // Pobieranie listy instancji
  useEffect(() => {
    fetchInstances();
    const interval = setInterval(fetchDownloadProgress, 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchInstances = async () => {
    try {
      const response = await fetch(`${API_URL}/instances`);
      const data = await response.json();
      setInstances(data);
    } catch (err) {
      setError('Failed to fetch instances');
    }
  };

  const fetchDownloadProgress = async () => {
    try {
      for (const instance of instances) {
        const response = await fetch(`${API_URL}/instances/${instance.id}/download-progress`);
        const progress = await response.json();
        setDownloadProgress(prev => ({
          ...prev,
          [instance.id]: progress
        }));
      }
    } catch (err) {
      console.error('Failed to fetch progress:', err);
    }
  };

  const handleCreateInstance = async () => {
    try {
      const response = await fetch(`${API_URL}/instances`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instance_id: newInstanceId })
      });
      
      if (!response.ok) throw new Error('Failed to create instance');
      
      setNewInstanceId('');
      fetchInstances();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteInstance = async (instanceId) => {
    try {
      await fetch(`${API_URL}/instances/${instanceId}`, {
        method: 'DELETE'
      });
      fetchInstances();
    } catch (err) {
      setError('Failed to delete instance');
    }
  };

  const handleWorkflowUpload = async (instanceId, file) => {
    try {
      const formData = new FormData();
      formData.append('workflow', file);

      const response = await fetch(`${API_URL}/instances/${instanceId}/analyze-workflow`, {
        method: 'POST',
        body: formData
      });

      const { required_models } = await response.json();

      // Rozpocznij pobieranie modeli
      await fetch(`${API_URL}/instances/${instanceId}/download-models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_keys: apiKeys,
          models: required_models
        })
      });
    } catch (err) {
      setError('Failed to process workflow');
    }
  };

  const handleApiKeyChange = (key, value) => {
    setApiKeys(prev => ({
      ...prev,
      [key]: value
    }));
    localStorage.setItem(`${key}_key`, value);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* API Keys Section */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">HuggingFace API Key</label>
                <Input
                  type="password"
                  value={apiKeys.huggingface}
                  onChange={(e) => handleApiKeyChange('huggingface', e.target.value)}
                  placeholder="Enter HuggingFace API key"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Civitai API Key</label>
                <Input
                  type="password"
                  value={apiKeys.civitai}
                  onChange={(e) => handleApiKeyChange('civitai', e.target.value)}
                  placeholder="Enter Civitai API key"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Create Instance Section */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <Input
                value={newInstanceId}
                onChange={(e) => setNewInstanceId(e.target.value)}
                placeholder="Enter instance ID"
              />
              <Button
                onClick={handleCreateInstance}
                disabled={!newInstanceId}
                className="flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Create Instance
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Instances List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {instances.map((instance) => (
            <Card key={instance.id}>
              <CardHeader>
                <CardTitle className="flex justify-between items-center">
                  <span>Instance {instance.id}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteInstance(instance.id)}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm">
                    <Folder className="w-4 h-4" />
                    {instance.path}
                  </div>

                  {/* Upload Workflow Button */}
                  <div className="flex gap-2">
                    <input
                      type="file"
                      id={`workflow-${instance.id}`}
                      className="hidden"
                      accept=".json"
                      onChange={(e) => handleWorkflowUpload(instance.id, e.target.files[0])}
                    />
                    <Button
                      onClick={() => document.getElementById(`workflow-${instance.id}`).click()}
                      className="w-full flex items-center justify-center gap-2"
                    >
                      <Upload className="w-4 h-4" />
                      Upload Workflow
                    </Button>
                  </div>

                  {/* Download Progress */}
                  {downloadProgress[instance.id] && Object.entries(downloadProgress[instance.id]).map(([modelName, progress]) => (
                    <div key={modelName} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>{modelName}</span>
                        <span>{progress.status}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${progress.progress}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Error Alert */}
        {error && (
          <Alert className="mt-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
}

export default App;