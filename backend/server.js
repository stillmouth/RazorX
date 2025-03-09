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
app.post('/upload', upload.single('audio'), async (req, res) => {
  try {
    const audioPath = req.file.path;
    console.log(`File uploaded: ${audioPath}`);

    // Paths to Python scripts
    const transcribeScriptPath = path.join(__dirname, 'whisper', 'transcribe.py');
    const getSchemaScriptPath = path.join(__dirname, 'get_schema.py');

    // Step 1: Transcribe the audio
    const transcription = await runPythonScript(transcribeScriptPath, audioPath);
    console.log(`Transcription from Python: ${transcription}`);

    // Step 2: Get the schema
    const schema = await runPythonScript(getSchemaScriptPath, 'database.db');
    console.log(`Schema from Python: ${schema}`);

    // Step 3: Call Groq API to generate SQL
    const apiUrl = process.env.GROQ_API_URL || 'https://api.groq.com/openai/v1/chat/completions';
    const apiKey = process.env.GROQ_API_KEY;
    const headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    };

    const payload = {
      model: 'llama-3.3-70b-versatile', // Model to use
      messages: [{
        role: 'user',
        content: `Given the schema:\n${schema}\n\nQuestion: ${transcription}\n\nGenerate and return ONLY the SQL (SQLITE3) query. If you are forced to assume some information, just return "ERROR"`,
      }],
    };

    // Make the API request
    const apiResponse = await axios.post(apiUrl, payload, { headers });
    let sqlQuery = apiResponse.data.choices[0].message.content.trim();

    // Clean up the SQL query by removing backticks and 'sql' keyword
    sqlQuery = sqlQuery.replace(/^```sql\n/, '').replace(/\n```$/, '').trim();
    console.log(`Generated SQL Query: ${sqlQuery}`);

    // Send response to the client
    res.json({ transcription, sqlQuery });
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