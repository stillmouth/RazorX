import sqlite3

def get_schema(database_path):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Retrieve table names from the sqlite_master
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

            # Get the primary key for the table
            cursor.execute(f"PRAGMA table_info({table_name});")
            primary_key_columns = [col[1] for col in columns if col[5] == 1]  # col[5] indicates primary key

            # Get foreign key information for the table
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            foreign_keys = cursor.fetchall()

            # Save column names, types, primary keys, and foreign keys
            schema[table_name] = {
                'columns': [(col[1], col[2]) for col in columns],  # Column name and type
                'primary_keys': primary_key_columns,
                'foreign_keys': [(fk[3], fk[4], fk[5]) for fk in foreign_keys]  # (from_column, to_table, to_column)
            }

        conn.close()

        if not schema:
            raise Exception("Schema is empty")

        # Create a schema string with table name, columns, primary keys, and foreign keys
        schema_str = ""
        for table, details in schema.items():
            schema_str += f"Table: {table}\n"
            
            # Columns and their types
            for col_name, col_type in details['columns']:
                schema_str += f"  - {col_name} ({col_type})\n"
            
            # Primary keys
            if details['primary_keys']:
                schema_str += f"  Primary Key(s): {', '.join(details['primary_keys'])}\n"
            
            # Foreign keys
            if details['foreign_keys']:
                for fk in details['foreign_keys']:
                    schema_str += f"  Foreign Key: {fk[0]} references {fk[1]}({fk[2]})\n"
        
        return schema_str

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# For testing
if __name__ == "__main__":
    DATABASE_PATH = 'database.db'  # Path to your database
    schema = get_schema(DATABASE_PATH)
    if schema:
        print("Schema:\n", schema)