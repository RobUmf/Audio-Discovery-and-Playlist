import sqlite3
import re
import sys
import yt_dlp
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100

def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info and info['entries']:
                entry = info['entries'][0]
                
                # Extract description, flatten newlines for terminal display, and cap at 512 chars
                raw_desc = entry.get('description') or "No description available."
                clean_desc = raw_desc.replace('\n', ' | ').strip()
                trunc_desc = clean_desc[:512] + "..." if len(clean_desc) > 512 else clean_desc

                return {
                    'title': entry.get('title'),
                    'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                    'id': entry.get('id'),
                    'description': trunc_desc
                }
    except Exception:
        pass
    return None

def main():
    db_path = 'audio_database.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check table structure for primary key / rowid and album column
    cursor.execute("PRAGMA table_info(tracks);")
    columns = [col[1] for col in cursor.fetchall()]
    id_col = 'id' if 'id' in columns else 'rowid'
    
    # Check for 'album' or fallback to 'grouping' based on metadata schema
    album_col = 'album' if 'album' in columns else 'grouping' if 'grouping' in columns else 'NULL'
    
    cursor.execute(f"SELECT {id_col}, title, artist, {album_col} FROM tracks WHERE youtube_url IS NULL OR youtube_url = '' OR youtube_url = 'None'")
    remaining = cursor.fetchall()
    
    print(f"\nFound {len(remaining)} unmapped tracks to review interactively.\n")
    
    for row_id, title, artist, album in remaining:
        # Fallbacks for empty fields
        title = title or "Unknown Title"
        artist = artist or "Unknown Artist"
        album_display = album if album else "Unknown Album"
        
        print("=" * 60)
        print(f"🎵 Track: {artist} - {title}")
        print(f"💿 Album: {album_display}")
        print("=" * 60)
        
        # Build tiered queries
        clean_title = re.sub(r'[^\w\s]', ' ', title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        base_title = re.sub(r'\(feat\..*?\)', '', title, flags=re.IGNORECASE).strip()
        base_title = re.sub(r'\[feat\..*?\]', '', base_title, flags=re.IGNORECASE).strip()
        
        queries = [
            f"{artist} - {title}",
            f"{artist} - {title} - Topic",
            f"{title} feat. {artist}"
        ]
        
        if album and album.strip():
            queries.append(f"{album} {title}")
            
        if clean_title != title:
            queries.append(f"{artist} - {clean_title}")
            queries.append(f"{artist} - {clean_title} - Topic")
        if base_title != title:
            queries.append(f"{artist} - {base_title}")
            queries.append(f"{artist} - {base_title} - Topic")
            
        # Deduplicate while preserving query order
        queries = list(dict.fromkeys(queries))
        
        track_handled = False
        
        for i, q in enumerate(queries):
            print(f"   Searching: {q} ...")
            res = search_youtube(q)
            
            if res:
                score = similar(f"{artist} - {title}", res['title'])
                print(f"   ✅ Found via query: '{q}'")
                print(f"      Result: {res['title']}")
                print(f"      URL:    {res['url']} (Sim: {score:.1f}%)")
                print(f"      Desc:   {res['description']}")
                
                is_last = (i == len(queries) - 1)
                
                while True:
                    if not is_last:
                        prompt = "   [y] Accept | [m] Manual URL | [t] Try next query | [s] Skip | [q] Quit: "
                    else:
                        prompt = "   [y] Accept | [m] Manual URL | [s] Skip | [q] Quit: "
                        
                    choice = input(prompt).strip().lower()
                    
                    if choice == 'y':
                        cursor.execute(f"UPDATE tracks SET youtube_url = ? WHERE {id_col} = ?", (res['url'], row_id))
                        conn.commit()
                        print("   💾 Saved to database.")
                        track_handled = True
                        break
                    elif choice == 'm':
                        custom_url = input("   Paste YouTube URL: ").strip()
                        if custom_url:
                            cursor.execute(f"UPDATE tracks SET youtube_url = ? WHERE {id_col} = ?", (custom_url, row_id))
                            conn.commit()
                            print("   💾 Manual URL saved.")
                        else:
                            print("   ⏭️ Skipped.")
                        track_handled = True
                        break
                    elif choice == 't' and not is_last:
                        print("")
                        break
                    elif choice == 's':
                        print("   ⏭️ Skipped.")
                        track_handled = True
                        break
                    elif choice == 'q':
                        print("\n👋 Exiting interactive session.")
                        conn.close()
                        sys.exit(0)
                    else:
                        print("   ⚠️ Invalid choice. Please try again.")
                
                if track_handled:
                    break
            else:
                print("   ⚠️ No results found.")
                
        if not track_handled:
            print("   ⚠️ No acceptable match found across all fallback tiers.")
            choice = input("   [m] Manual URL | [s] Skip | [q] Quit: ").strip().lower()
            if choice == 'm':
                custom_url = input("   Paste YouTube URL: ").strip()
                if custom_url:
                    cursor.execute(f"UPDATE tracks SET youtube_url = ? WHERE {id_col} = ?", (custom_url, row_id))
                    conn.commit()
                    print("   💾 Manual URL saved.")
            elif choice == 'q':
                print("\n👋 Exiting interactive session.")
                conn.close()
                sys.exit(0)
            else:
                print("   ⏭️ Skipped.")
                
    conn.close()
    print("\n🎉 Interactive review session complete!")

if __name__ == '__main__':
    main()    columns = [col[1] for col in cursor.fetchall()]
    id_col = 'id' if 'id' in columns else 'rowid'
    
    # Check for 'album' or fallback to 'grouping' based on your metadata schema
    album_col = 'album' if 'album' in columns else 'grouping' if 'grouping' in columns else 'NULL'
    
    cursor.execute(f"SELECT {id_col}, title, artist, {album_col} FROM tracks WHERE youtube_url IS NULL OR youtube_url = '' OR youtube_url = 'None'")
    remaining = cursor.fetchall()
    
    print(f"\nFound {len(remaining)} unmapped tracks to review interactively.\n")
    
    for row_id, title, artist, album in remaining:
        # Fallbacks for empty fields
        title = title or "Unknown Title"
        artist = artist or "Unknown Artist"
        album_display = album if album else "Unknown Album"
        
        print("=" * 60)
        print(f"🎵 Track: {artist} - {title}")
        print(f"💿 Album: {album_display}")
        print("=" * 60)
        
        # Build tiered queries
        clean_title = re.sub(r'[^\w\s]', ' ', title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        base_title = re.sub(r'\(feat\..*?\)', '', title, flags=re.IGNORECASE).strip()
        base_title = re.sub(r'\[feat\..*?\]', '', base_title, flags=re.IGNORECASE).strip()
        
        queries = [
            f"{artist} - {title}",
            f"{artist} - {title} - Topic",
            f"{title} feat. {artist}"     # New: Song feat. Artist
        ]
        
        # New: Album song
        if album and album.strip():
            queries.append(f"{album} {title}")
            
        if clean_title != title:
            queries.append(f"{artist} - {clean_title}")
            queries.append(f"{artist} - {clean_title} - Topic")
        if base_title != title:
            queries.append(f"{artist} - {base_title}")
            queries.append(f"{artist} - {base_title} - Topic")
            
        # Deduplicate
        queries = list(dict.fromkeys(queries))
        
        track_handled = False
        
        for i, q in enumerate(queries):
            print(f"   Searching: {q} ...")
            res = search_youtube(q)
            
            if res:
                score = similar(f"{artist} - {title}", res['title'])
                print(f"   ✅ Found via query: '{q}'")
                print(f"      Result: {res['title']}")
                print(f"      URL:    {res['url']} (Sim: {score:.1f}%)")
                
                is_last = (i == len(queries) - 1)
                
                # Input validation loop
                while True:
                    if not is_last:
                        prompt = "   [y] Accept | [m] Enter URL manually | [t] Try again | [s] Skip: "
                    else:
                        prompt = "   [y] Accept | [m] Enter URL manually | [s] Skip: "
                        
                    choice = input(prompt).strip().lower()
                    
                    if choice == 'y':
                        cursor.execute(f"UPDATE tracks SET youtube_url = ? WHERE {id_col} = ?", (res['url'], row_id))
                        conn.commit()
                        print("   💾 Saved to database.")
                        track_handled = True
                        break
                    elif choice == 'm':
                        custom_url = input("   Paste YouTube URL: ").strip()
                        if custom_url:
                            cursor.execute(f"UPDATE tracks SET youtube_url = ? WHERE {id_col} = ?", (custom_url, row_id))
                            conn.commit()
                            print("   💾 Manual URL saved.")
                        else:
                            print("   ⏭️ Skipped.")
                        track_handled = True
                        break
                    elif choice == 't' and not is_last:
                        print("") # Formatting break before next search
                        break # Break input loop to continue query loop
                    elif choice == 's':
                        print("   ⏭️ Skipped.")
                        track_handled = True
                        break
                    else:
                        print("   ⚠️ Invalid choice. Please try again.")
                
                if track_handled:
                    break # Break query loop to move to the next track
            else:
                print("   ⚠️ No results found.")
                
        # Triggered if all queries are exhausted and the user never made a terminal choice (y/m/s)
        if not track_handled:
            print("   ⚠️ No acceptable match found across all fallback tiers.")
            choice = input("   [m] Enter URL manually | [s] Skip: ").strip().lower()
            if choice == 'm':
                custom_url = input("   Paste YouTube URL: ").strip()
                if custom_url:
                    cursor.execute(f"UPDATE tracks SET youtube_url = ? WHERE {id_col} = ?", (custom_url, row_id))
                    conn.commit()
                    print("   💾 Manual URL saved.")
            else:
                print("   ⏭️ Skipped.")
                
    conn.close()
    print("\n🎉 Interactive review session complete!")

if __name__ == '__main__':
    main()
