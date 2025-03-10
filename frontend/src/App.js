import React, { useState, useRef } from "react";
import axios from "axios";
import Switch from "./components/Switch"; // Import the Switch component
import "./App.css";

function App() {
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [transcription, setTranscription] = useState("");
  const [sqlQuery, setSqlQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setAudioBlob(audioBlob);
        audioChunksRef.current = [];
      };

      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  

  const handleRecordingToggle = () => {
    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
    setRecording(!recording);
  };
  

  const handleUpload = async () => {
    if (!audioBlob) return;

    setIsLoading(true);
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");

    try {
      const response = await axios.post("http://localhost:5000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data?.transcription) setTranscription(response.data.transcription);
      if (response.data?.sqlQuery) setSqlQuery(response.data.sqlQuery);
    } catch (error) {
      console.error("Error uploading audio:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="main-container">
        <h1 className="app-title">Voice Command to SQL</h1>

        <div className="button-container">
          <div className="button-group">
            {/* Replace the old buttons with the Switch component */}
            <div onClick={handleRecordingToggle}>
            <Switch checked={recording} onChange={handleRecordingToggle} isLoading={isLoading} />
            </div>
          </div>

          {audioBlob && (
            <button
              onClick={handleUpload}
              disabled={isLoading}
              className="button upload-button"
            >
              {isLoading ? (
                <>
                  <div className="loading-spinner"></div>
                  Processing...
                </>
              ) : (
                'Upload and Transcribe'
              )}
            </button>
          )}
        </div>

        {transcription && (
          <div className="result-card">
            <h3 className="result-title">Transcription:</h3>
            <p className="transcription-text">{transcription}</p>
          </div>
        )}

        {sqlQuery && (
          <div className="result-card">
            <h3 className="result-title">Generated SQL Query:</h3>
            <pre className="sql-query">{sqlQuery}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;