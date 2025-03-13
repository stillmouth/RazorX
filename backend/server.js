const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const cors = require('cors');
const { promisify } = require('util');
const { exec } = require('child_process');
const app = express();
require('dotenv').config();
const uploadsDir = path.join(__dirname, 'uploads');

const port = process.env.PORT || 5000;

// Load environment variables
require('dotenv').config();

// Use CORS to allow cross-origin requests
app.use(cors());

// Set up storage engine for Multer
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + path.extname(file.originalname));
  },
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('audio/')) {
      cb(null, true);
    } else {
      cb(new Error('Only audio files are allowed!'), false);
    }
  },
});

// Make sure the uploads folder exists
if (!fs.existsSync('uploads')) {
  fs.mkdirSync('uploads');
}

// Promisify the exec function for easier async/await usage
const execAsync = promisify(exec);

// Helper function to run Python scripts
async function runPythonScript(scriptPath, args) {
  const { stdout, stderr } = await execAsync(`python "${scriptPath}" "${args}"`);
  if (stderr) throw new Error(stderr);
  return stdout.trim();
}

// Handle the file upload endpoint
const sqlite3 = require('sqlite3').verbose();

// Handle the file upload endpoint
app.post('/upload', upload.single('audio'), async (req, res) => {
  try {
    const audioPath = req.file.path;
    console.log(`File uploaded: ${audioPath}`);

    const transcribeScriptPath = path.join(__dirname, 'whisper', 'transcribe.py');
    const getSchemaScriptPath = path.join(__dirname, 'get_schema.py');

    // Step 1: Transcribe the audio
    const transcription = await runPythonScript(transcribeScriptPath, audioPath);
    console.log(`Transcription from Python: ${transcription}`);

    // Step 2: Get the schema
    const schema = await runPythonScript(getSchemaScriptPath, 'database.db');

    // Step 3: Call Groq API to generate SQL queries
    const apiUrl = process.env.GROQ_API_URL || 'https://api.groq.com/openai/v1/chat/completions';
    const apiKey = process.env.GROQ_API_KEY;
    const headers = { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' };

    const payload = {
      model: 'qwen-2.5-32b',
      messages: [{
        role: 'user',
        content: `Given only the schema with sample values of a database:\n${schema}\n\nQuestion: ${transcription}\n\n
        Generate an SQLite3 (SQL) query to answer the given question and also generate relevant 
        SQLite3 (SQL) queries to provide context for your answer. Every SQL query must start with 'SQLQUERY:'.
        They must be useful for insights and reporting and must solve the question by visualization or report. 
        Ensure clarity in every table and use JOINs to form bigger tables wherever needed, for more clarity.
        Do NOT include explanations, only the queries. Do not use shorthands for anything including table names.
        In case of a query like a personal question, return only a 'REASON:' followed by the reason.
        You can return either a reason or an SQL query.`,
      }],
    };

    const apiResponse = await axios.post(apiUrl, payload, { headers });
    let sqlQueries = apiResponse.data.choices[0].message.content.trim();

    // Step 3.1: Check if response contains a reason instead of queries
    if (sqlQueries.startsWith('REASON:')) {
      const reason = sqlQueries.replace('REASON:', '').trim();
      console.warn('API returned a reason:', reason);
      return res.status(400).json({ error: 'Query not generated', reason });
    }

    // Step 3.2: Refine SQL queries
    const apiUrlRefining = process.env.GROQ_API_URL_REFINING || 'https://api.groq.com/openai/v1/chat/completions';
    const apiKeyRefining = process.env.GROQ_API_KEY_REFINING;
    const refineHeaders = { 'Authorization': `Bearer ${apiKeyRefining}`, 'Content-Type': 'application/json' };

    const payload_refining = {
      model: 'llama-3.3-70b-versatile',
      messages: [{
        role: 'user',
        content: `Check for any syntax errors in this: \n${sqlQueries}\n
        Return it in the exact same format after fixing. Do not add anything else in your response.`,
      }],
    };

    const apiResponseRefined = await axios.post(apiUrlRefining, payload_refining, { headers: refineHeaders });
    let sqlQueriesRefined = apiResponseRefined.data.choices[0].message.content.trim();

    // Extract queries
    let queries = sqlQueriesRefined
      .split("\n")
      .map(query => query.trim())
      .filter(query => query.startsWith("SQLQUERY:"))
      .map(query => query.replace(/^SQLQUERY:\s*/, ""));  // Ensures both "SQLQUERY: " and "SQLQUERY:" are handled

    // Step 4: Execute all SQL queries
    const db = new sqlite3.Database('database.db', sqlite3.OPEN_READWRITE, (err) => {
      if (err) {
        console.error('Database connection error:', err);
        return res.status(500).json({ error: 'Database connection failed' });
      }
    });

    try {
      let results = [];
      for (const query of queries) {
        try {
          const rows = await new Promise((resolve, reject) => {
            db.all(query, [], (err, rows) => {
              if (err) {
                console.error(`SQL Execution Error for query: ${query}`, err);
                reject(err);
              } else {
                resolve(rows);
              }
            });
          });
          results.push({ query, rows });
        } catch (queryError) {
          results.push({ query, error: queryError.message || 'SQL execution failed' });
        }
      }
      res.json({ transcription, sqlQueries: queries, results });
    } finally {
      db.close();
    }

    // Step 5: Clean up uploaded files
    fs.readdir(uploadsDir, (err, files) => {
      if (err) {
        console.error('Error reading uploads directory:', err);
        return;
      }
      for (const file of files) {
        fs.unlink(path.join(uploadsDir, file), (err) => {
          if (err) {
            console.error(`Error deleting file ${file}:`, err);
          }
        });
      }
    });

  } catch (error) {
    console.error('Error in /upload endpoint:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});




// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: err.message || 'Internal Server Error' });
});

// Start the server
app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});