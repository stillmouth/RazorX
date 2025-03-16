import sqlite3
import json
import os
from pathlib import Path

def get_schema_with_samples(database_path):
    try:
        # Check if database file exists
        db_path = Path(database_path)
        if not db_path.is_file():
            raise FileNotFoundError(f"Database file {database_path} not found")

        # Attempt read-only connection, fallback to normal with query_only
        try:
            conn = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
        except sqlite3.OperationalError:
            conn = sqlite3.connect(database_path)
            conn.execute("PRAGMA query_only = 1")  # Prevent modifications
        
        try:
            cursor = conn.cursor()

            # Retrieve table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            if not tables:
                raise Exception("No tables found in the database")

            schema = {}

            for table in tables:
                table_name = table[0]
                # Escape table name for SQL queries
                safe_table_name = table_name.replace('"', '""')

                # Get columns and data types
                cursor.execute(f'PRAGMA table_info("{safe_table_name}")')
                columns = cursor.fetchall()
                column_details = [{"name": col[1], "type": col[2]} for col in columns]

                # Get primary keys
                primary_keys = [col[1] for col in columns if col[5] == 1]

                # Get foreign key constraints
                cursor.execute(f'PRAGMA foreign_key_list("{safe_table_name}")')
                foreign_keys = cursor.fetchall()
                foreign_key_details = [
                    {"from_column": fk[3], "to_table": fk[2], "to_column": fk[4]} 
                    for fk in foreign_keys
                ]

                # Fetch sample rows (handle BLOBs and empty results)
                cursor.execute(f'SELECT * FROM "{safe_table_name}" LIMIT 3')
                sample_rows = cursor.fetchall()
                sample_data = []
                column_names = [col[1] for col in columns]

                for row in sample_rows:
                    row_data = {}
                    for name, value in zip(column_names, row):
                        if isinstance(value, bytes):
                            # Convert BLOB to hexadecimal representation
                            row_data[name] = f"0x{value.hex()}"
                        else:
                            row_data[name] = value
                    sample_data.append(row_data)

                # Save schema details
                schema[table_name] = {
                    "columns": column_details,
                    "primary_keys": primary_keys,
                    "foreign_keys": foreign_key_details,
                    "sample_data": sample_data
                }

            return json.dumps(schema, indent=2, default=str)

        finally:
            conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        print(f"Error: {e}")
        return json.dumps({"error": str(e)})

# For testing
if __name__ == "__main__":
    DATABASE_PATH = 'database.db'
    schema_json = get_schema_with_samples(DATABASE_PATH)
    if schema_json:
        print("Database Schema with Sample Data:\n", schema_json)