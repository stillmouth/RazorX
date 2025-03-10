import sqlite3
import json

def get_schema_with_samples(database_path):
    try:
        # Connect to the SQLite database in read-only mode
        conn = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        # Retrieve table names from the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            raise Exception("No tables found in the database")

        schema = {}

        for table in tables:
            table_name = table[0]

            # Retrieve column info for each table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            # Get primary key columns
            primary_key_columns = [col[1] for col in columns if col[5] == 1]  # col[5] indicates primary key

            # Get foreign key information
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            foreign_keys = cursor.fetchall()

            # Fetch a few example rows (LIMIT 3)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            sample_rows = cursor.fetchall()

            # Save schema details
            schema[table_name] = {
                'columns': [(col[1], col[2]) for col in columns],  # (column_name, type)
                'primary_keys': primary_key_columns,
                'foreign_keys': [(fk[3], fk[4], fk[5]) for fk in foreign_keys],  # (from_column, to_table, to_column)
                'sample_data': sample_rows  # Add sample rows for AI context
            }

        conn.close()

        if not schema:
            raise Exception("Schema is empty")

        # Convert schema to a readable JSON format
        return json.dumps(schema, indent=2)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# For testing
if __name__ == "__main__":
    DATABASE_PATH = 'database.db'  # Adjust path as needed
    schema_json = get_schema_with_samples(DATABASE_PATH)
    if schema_json:
        print("Database Schema with Sample Data:\n", schema_json)
