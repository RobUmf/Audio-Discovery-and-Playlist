import sqlite3
import os

DB_PATH = "audio_database.db"
TABLE_NAME = "tracks"

def prompt_str(prompt_text):
    val = input(prompt_text).strip()
    return val if val else None

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at '{DB_PATH}'")
        return

    while True:
        print("\n" + "=" * 60)
        print("🔍 Audio Database Record Dumper")
        print("=" * 60)
        
        search_term = prompt_str("   -> Enter search term (ID, song, artist) [or type 'exit' to quit]: ")
        if not search_term or search_term.lower() in ('exit', 'q'):
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
                WHERE title LIKE ? OR artist LIKE ? OR file_path LIKE ? OR album_artist LIKE ?
            """
            pattern = f"%{search_term}%"
            cursor.execute(query, (pattern, pattern, pattern, pattern))

        rows = cursor.fetchall()
        if not rows:
            print(f"\n❌ No records found matching: '{search_term}'")
            conn.close()
            continue

        print(f"\n   Found {len(rows)} matching record(s):")
        print("-" * 60)
        for row in rows:
            r_id = row['id']
            title = row['title'] or 'Unknown'
            artist = row['artist'] or row['album_artist'] or 'Unknown'
            print(f"   [ID: {r_id}] {artist} - {title}")
        print("-" * 60)

        # Prompt to select an ID for full record dump
        choice = prompt_str("   -> Enter ID to dump full record (or type 'q' / press Enter to search again): ")
        if not choice:
            conn.close()
            continue
        
        if choice.lower() in ('q', 'exit'):
            print("Exiting. Goodbye!")
            conn.close()
            break
        
        if choice.isdigit():
            cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (choice,))
            target_row = cursor.fetchone()
            if target_row:
                row_dict = dict(target_row)
                title = row_dict.get('title', 'Unknown')
                artist = row_dict.get('artist', 'Unknown')
                grouping = row_dict.get('grouping', 'Unknown')
                row_id = row_dict.get('id', 'N/A')

                print(f"\nTARGET ({title}) [ID: {row_id}] {artist} - {grouping} - {title}")
                for key, val in row_dict.items():
                    print(f"  - {key}: {val}")
                print("-" * 50)
                
                next_action = prompt_str("   -> Press [Enter] to search again, or type 'q' to quit: ")
                if next_action and next_action.lower() in ('q', 'exit'):
                    print("Exiting. Goodbye!")
                    conn.close()
                    break
            else:
                print(f"❌ No record found with ID {choice}")

        conn.close()

if __name__ == "__main__":
    main()
