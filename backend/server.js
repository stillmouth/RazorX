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
const { GoogleGenerativeAI } = require("@google/generative-ai");

const port = process.env.PORT || 5000;

// Load environment variables
require('dotenv').config();

// Use CORS to allow cross-origin requests
app.use(cors());
app.use(express.json()); // Add this to parse JSON request bodies

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
    const allowedTypes = [
      "audio/", // Allow all audio types
      "application/x-sqlite3", // SQLite database MIME type
      "application/octet-stream", // Generic binary files
      "application/vnd.sqlite3" // Alternative SQLite type
    ];

    if (allowedTypes.some(type => file.mimetype.startsWith(type)) || file.originalname.endsWith(".db")) {
      cb(null, true);
    } else {
      cb(new Error("Only audio or .db files are allowed!"), false);
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

//Handle Database.db replace and uploads
// Route to replace database.db
app.post('/replacedatabase', upload.single('database'), (req, res) => {
  if (!req.file) {
      return res.status(400).send('No file uploaded.');
  }

  const oldDbPath = path.join(__dirname, 'database.db');
  const newDbPath = req.file.path; // Temporary file path from multer

  // Replace the old database file
  fs.rename(newDbPath, oldDbPath, (err) => {
      if (err) {
          return res.status(500).send('Error replacing database: ' + err.message);
      }
      res.send('Database replaced successfully.');
  });
});

// Handle the file upload endpoint
app.post('/upload', upload.single('audio'), async (req, res) => {
  try {
    const audioPath = req.file.path;
    console.log(`File uploaded: ${audioPath}`);

    const transcribeScriptPath = path.join(__dirname, 'whisper', 'transcribe.py');

    // Step 1: Transcribe the audio
    const transcription = await runPythonScript(transcribeScriptPath, audioPath);
    console.log(`Transcription from Python: ${transcription}`);

    // Step 2: Return the transcription to the client
    res.json({ transcription });

    // Step 3: Clean up uploaded files
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

// New endpoint to handle execution of edited transcription
app.post('/execute', async (req, res) => {
  try {
    const { transcription } = req.body;

    // Step 1: Get the schema
    const getSchemaScriptPath = path.join(__dirname, 'get_schema.py');
    const schema = await runPythonScript(getSchemaScriptPath, 'database.db');

    // Step 2: Call Groq API to generate SQL queries
    const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-thinking-exp-01-21" });

    const prompt = `Given only the schema with sample values of my database:\n${schema}\n\n
                    Question: ${transcription}\n\n
                    Generate multiple SQLite3 (SQL) queries to directly answer the given question and provide additional context for insights and reporting.
                    Every SQL query must start with 'SQLQUERY:'.\n
                    - The queries must help in visualization or reporting.\n
                    - Ensure clarity in table structures by using JOINs where necessary.\n
                    - Do NOT include explanations, comments, or metadata in your response.\n
                    - If the input question is personal or inappropriate, return only 'REASON:' followed by the reason.\n
                    - If the question is too vague, generate contextual SQL queries that help understand the subject.\n
                    - Do NOT mix 'REASON:' with 'SQLQUERY:'. Return only one type of response.\n
                    - Prioritize providing at least some relevant SQL queries for vague questions instead of returning a reason.\n
                    - Adhere strictly to the provided schema.
                    - Avoid giving queries that might return the same result.\n`;


    const apiResponse = await model.generateContent(prompt);
    const sqlQueries = await apiResponse.response.text(); // Extract text
    //console.log(sqlQueries);
    // Step 2.1: Check if response contains a reason instead of queries
    if (sqlQueries.startsWith('REASON:')) {
      const reason = sqlQueries.replace('REASON:', '').trim();
      console.warn('API returned a reason:', reason);
      return res.status(400).json({ error: 'Query not generated', reason });
    }

    // Step 2.2: Refine SQL queries
    const refinePrompt = `Check for any syntax and logical errors in this: \n${sqlQueries}\n for the question \n${transcription}\n\n
        Given the schema: \n${schema}\n
        Ensure it is supported by SQLite3. If not, fix it to adhere to SQLite3. Remove any incomplete queries if you cannot find the context.
        Return the SQLQueries in the exact same format after fixing. Do not add anything else in your response.
        Ensure each query adheres strictly to the schema.`;


    const apiResponseRefined = await model.generateContent(refinePrompt);
    let sqlQueriesRefined = await apiResponseRefined.response.text();
    //console.log(sqlQueriesRefined);
    // Extract queries
    let queries = sqlQueriesRefined
      .split("\n")
      .map(query => query.trim())
      .filter(query => query.startsWith("SQLQUERY:"))
      .map(query => query.replace(/^SQLQUERY:\s*/, ""));  // Ensures both "SQLQUERY: " and "SQLQUERY:" are handled

    // Step 3: Execute all SQL queries
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
      // Save SQL results as JSON
      fs.writeFileSync("sql_results.json", JSON.stringify(results, null, 2));

      // Call Python script to generate graphs
      exec("python GenerateGraph.py", (error, stdout, stderr) => {
          if (error) {
              console.error(`Graph generation error: ${error.message}`);
          }
          if (stderr) {
              console.error(`Graph generation stderr: ${stderr}`);
          }
          console.log(`Graph generation stdout: ${stdout}`);
      });
      res.json({ transcription, sqlQueries: queries, results });
    } finally {
      db.close();
    }
  } catch (error) {
    console.error('Error in /execute endpoint:', error);
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