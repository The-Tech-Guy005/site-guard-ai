import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';

const CCTVViewer = () => {
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, completed, error
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [detections, setDetections] = useState([]);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [totalFrames, setTotalFrames] = useState(0);
  const [isPolling, setIsPolling] = useState(false);
  
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov)$/i)) {
      setError('Invalid file type. Please upload MP4, AVI, or MOV files.');
      setStatus('error');
      return;
    }

    setStatus('uploading');
    setError(null);

    try {
      await api.uploadVideo(file);
      setStatus('processing');
      startPolling();
    } catch (err) {
      setError(err.message || 'Failed to upload video');
      setStatus('error');
    }
  };

  const startPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    setIsPolling(true);
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const progressData = await api.getProgress();
        setProgress(progressData.progress || 0);
        setCurrentFrame(progressData.current_frame || 0);
        setTotalFrames(progressData.total_frames || 0);

        if (progressData.status === 'completed') {
          setStatus('completed');
          stopPolling();
        } else if (progressData.status === 'failed') {
          setError(progressData.error || 'Processing failed');
          setStatus('error');
          stopPolling();
        }

        // Fetch detections
        const detectionData = await api.getCurrentDetections();
        setDetections(detectionData.detections || []);
      } catch (err) {
        console.error('Polling error:', err);
        // Don't set error state on polling failures, just log
      }
    }, 1000); // Poll every second
  };

  const stopPolling = () => {
    setIsPolling(false);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const handleReset = () => {
    setStatus('idle');
    setError(null);
    setProgress(0);
    setDetections([]);
    setCurrentFrame(0);
    setTotalFrames(0);
    stopPolling();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

  // Draw detection overlays on canvas
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current || detections.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const video = videoRef.current;

    // Set canvas size to match video
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw detections
    detections.forEach((detection) => {
      const [xmin, ymin, xmax, ymax] = detection.bbox;
      
      // Draw bounding box
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 2;
      ctx.strokeRect(xmin, ymin, xmax - xmin, ymax - ymin);

      // Draw label background
      const label = `${detection.id} | ${detection.class} | ${Math.round(detection.confidence * 100)}%`;
      ctx.font = '14px Arial';
      const textWidth = ctx.measureText(label).width;
      ctx.fillStyle = '#00ff00';
      ctx.fillRect(xmin, ymin - 24, textWidth + 8, 24);

      // Draw label text
      ctx.fillStyle = '#000000';
      ctx.fillText(label, xmin + 4, ymin - 8);
    });
  }, [detections]);

  const getStatusColor = () => {
    switch (status) {
      case 'processing': return 'bg-yellow-500';
      case 'completed': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'idle': return 'No Video Selected';
      case 'uploading': return 'Uploading...';
      case 'processing': return `Processing: ${progress.toFixed(1)}%`;
      case 'completed': return 'Processing Complete';
      case 'error': return 'Error';
      default: return status;
    }
  };

  return (
    <div className="space-y-4">
      {/* Control Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/avi,video/quicktime,.mp4,.avi,.mov"
            onChange={handleFileSelect}
            disabled={status === 'uploading' || status === 'processing'}
            className="hidden"
            id="video-upload"
          />
          <label
            htmlFor="video-upload"
            className={`px-4 py-2 rounded-lg cursor-pointer transition-colors ${
              status === 'uploading' || status === 'processing'
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {status === 'idle' ? 'Upload Video' : 'Change Video'}
          </label>
          
          {status !== 'idle' && (
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Reset
            </button>
          )}
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()}`} />
          <span className="text-sm font-medium text-gray-700">{getStatusText()}</span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 font-medium">{error}</p>
        </div>
      )}

      {/* Video Viewer */}
      <div className="relative bg-gray-900 rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
        {status === 'idle' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">📹</div>
              <p className="text-gray-400 font-medium">No Video Selected</p>
              <p className="text-gray-500 text-sm mt-2">Upload a video to begin AI processing</p>
            </div>
          </div>
        )}

        {status === 'uploading' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400 font-medium">Uploading video...</p>
            </div>
          </div>
        )}

        {(status === 'processing' || status === 'completed') && (
          <div className="relative w-full h-full">
            <img
              ref={videoRef}
              src={api.getStreamUrl()}
              alt="Processed Video Stream"
              className="w-full h-full object-contain"
              onError={() => setError('Failed to load video stream')}
            />
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 w-full h-full pointer-events-none"
            />
            
            {/* Processing Progress Overlay */}
            {status === 'processing' && (
              <div className="absolute bottom-4 left-4 right-4 bg-black bg-opacity-70 rounded-lg p-3">
                <div className="flex items-center justify-between text-white text-sm mb-2">
                  <span>Processing Frame {currentFrame} of {totalFrames}</span>
                  <span>{progress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Detection Stats Overlay */}
            {detections.length > 0 && (
              <div className="absolute top-4 right-4 bg-black bg-opacity-70 rounded-lg p-3">
                <div className="text-white text-sm">
                  <div className="font-semibold mb-1">Active Detections</div>
                  <div>Objects: {detections.length}</div>
                  <div>Workers: {detections.filter(d => d.class === 'person').length}</div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Detection Info */}
      {detections.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Current Detections</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {detections.map((detection, index) => (
              <div key={index} className="bg-white p-3 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">{detection.id}</span>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {detection.class}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  <div>Confidence: {(detection.confidence * 100).toFixed(1)}%</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Position: [{detection.bbox[0]}, {detection.bbox[1]}, {detection.bbox[2]}, {detection.bbox[3]}]
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CCTVViewer;