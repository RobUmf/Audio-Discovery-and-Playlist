import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = "audio_database.db"
TABLE_NAME = "tracks"

def backup_database():
    if not os.path.exists(DB_PATH):
        return
    
    choice = prompt_str("   -> Do you want to create a database backup before starting? (y/N): ")
    if choice and choice.lower() == 'y':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"audio_database_backup_{timestamp}.db"
        shutil.copy2(DB_PATH, backup_name)
        print(f"   📦 Backup created successfully: {backup_name}")
    else:
        print("   ⏩ Skipping database backup.")

def prompt_str(prompt_text):
    val = input(prompt_text).strip()
    return val if val else None

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at '{DB_PATH}'")
        return

    print("\n" + "=" * 60)
    print("🔍 Interactive Audio Database Record Manager")
    print("=" * 60)
    
    # Prompt option for backup on startup
    backup_database()

    while True:
        print("\n" + "-" * 60)
        search_term = prompt_str("   -> Enter search term (ID, song title, artist, album, or path) [or type 'exit' to quit]: ")
        if not search_term or search_term.lower() == 'exit':
            print("Exiting. Goodbye!")
            break

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if search_term.isdigit():
            cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (search_term,))
        else:
            query = f"""
                SELECT * FROM {TABLE_NAME} 
                WHERE title LIKE ? OR artist LIKE ? OR file_path LIKE ? OR album_artist LIKE ? OR album LIKE ?
            """
            pattern = f"%{search_term}%"
            cursor.execute(query, (pattern, pattern, pattern, pattern, pattern))

        rows = cursor.fetchall()
        if not rows:
            print(f"\n❌ No records found matching: '{search_term}'")
            conn.close()
            continue

        print(f"\n   Found {len(rows)} matching record(s):")
        print("-" * 60)

        for row in rows:
            row_dict = dict(row)
            title = row_dict.get('title', 'Unknown')
            artist = row_dict.get('artist') or row_dict.get('album_artist', 'Unknown')
            album = row_dict.get('album', 'Unknown')
            row_id = row_dict.get('id', 'N/A')

            print(f"\nTARGET ({title}) [ID: {row_id}] | Album: {album}")
            for key, val in row_dict.items():
                print(f"  - {key}: {val}")
            print("-" * 60)

            action = prompt_str(f"   -> Action for ID {row_id}? ([d]elete / [s]kip / [q]uit): ")
            if action and action.lower() == 'd':
                confirm = prompt_str(f"      ⚠️ Are you sure you want to delete ID {row_id} ({title})? (y/N): ")
                if confirm and confirm.lower() == 'y':
                    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (row_id,))
                    conn.commit()
                    print(f"      🗑️ Deleted record ID {row_id} from database.")
                else:
                    print("      Skipped deletion.")
            elif action and action.lower() == 'q':
                conn.close()
                print("Exiting. Goodbye!")
                return

        conn.close()

if __name__ == "__main__":
    main()
