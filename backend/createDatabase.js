const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./database.db');  // Path to the SQLite DB

// Create the sales table
db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS sales (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      date TEXT,
      amount REAL,
      region TEXT
    )
  `);

  // Insert some sample data
  const stmt = db.prepare("INSERT INTO sales (date, amount, region) VALUES (?, ?, ?)");
  stmt.run('2025-02-15', 1000, 'North');
  stmt.run('2025-02-20', 1500, 'South');
  stmt.run('2025-02-25', 2000, 'East');
  stmt.run('2025-03-01', 2500, 'West');
  stmt.finalize();

  console.log("Database created and sample data inserted.");
});

db.close();
