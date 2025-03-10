import React, { useState, useRef } from "react";
import axios from "axios";
import Switch from "./components/Switch";
import "./App.css";

function App() {
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [transcription, setTranscription] = useState("");
  const [sqlQueries, setSqlQueries] = useState([]); // Store multiple queries
  const [queryResults, setQueryResults] = useState([]); // Store multiple query results
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
      if (response.data?.sqlQueries) setSqlQueries(response.data.sqlQueries); // Set multiple queries
      if (response.data?.results) setQueryResults(response.data.results); // Store results per query
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
                "Upload and Transcribe"
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

        {sqlQueries.length > 0 && (
          <div className="result-card">
            <h3 className="result-title">Generated SQL Queries:</h3>
            <ul className="sql-query-list">
              {sqlQueries.map((query, index) => (
                <li key={index} className="sql-query">
                  <pre>{query}</pre>
                </li>
              ))}
            </ul>
          </div>
        )}

        {queryResults.length > 0 && (
          <div className="result-card">
            <h3 className="result-title">Query Results:</h3>
            {queryResults.map((result, index) => (
              <div key={index} className="query-result-container">
                <h4>Query {index + 1}:</h4>
                <pre className="sql-query">{result.query}</pre>
                {result.error ? (
                  <p className="error-text">{result.error}</p>
                ) : (
                  <table className="result-table">
                    <thead>
                      <tr>
                        {result.rows.length > 0 &&
                          Object.keys(result.rows[0]).map((key) => (
                            <th key={key}>{key}</th>
                          ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.rows.length > 0 ? (
                        result.rows.map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {Object.values(row).map((value, i) => (
                              <td key={i}>{value}</td>
                            ))}
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="100%">No results found.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
