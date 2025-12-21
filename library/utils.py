import os
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from .models import Chapter

def get_epub_metadata(epub_path):
    """
    Fungsi All-in-One untuk mengambil Metadata:
    - Judul, Penulis, Sinopsis (Description), Genre (Subject)
    """
    metadata = {
        'title': None,
        'author': "Unknown",
        'synopsis': None,
        'genre': "General"
    }

    try:
        book = epub.read_epub(epub_path)
        
        # 1. Ambil Judul
        if book.get_metadata('DC', 'title'):
            metadata['title'] = book.get_metadata('DC', 'title')[0][0]
            
        # 2. Ambil Penulis
        if book.get_metadata('DC', 'creator'):
            raw_author = book.get_metadata('DC', 'creator')[0][0]
            if raw_author and str(raw_author).strip() != "0":
                metadata['author'] = raw_author

        # 3. Ambil Sinopsis (Description) & Bersihkan HTML
        if book.get_metadata('DC', 'description'):
            raw_desc = book.get_metadata('DC', 'description')[0][0]
            # Bersihkan tag HTML sederhana (<p>, <br>, <div>) agar rapi di database
            clean_desc = re.sub('<[^<]+?>', '', raw_desc)
            metadata['synopsis'] = clean_desc

        # 4. Ambil Genre (Subject)
        subjects = book.get_metadata('DC', 'subject')
        if subjects:
            # Gabung list genre jadi string koma: "Fantasy, Magic, Action"
            genre_list = [s[0] for s in subjects]
            genre_str = ", ".join(genre_list)
            
            # Potong jika kepanjangan (Database max 100 char)
            if len(genre_str) > 100:
                genre_str = genre_str[:97] + "..."
            
            metadata['genre'] = genre_str

        return metadata
    
    except Exception as e:
        print(f"Gagal ekstrak metadata: {e}")
        return metadata

def generate_chapters(novel_instance):
    if not novel_instance.epub_file: return
    file_path = novel_instance.epub_file.path
    
    try:
        # --- LOGIKA EPUB ---
        if file_path.endswith('.epub'):
            book = epub.read_epub(file_path)
            
            # Auto-fill judul novel jika masih default
            if not novel_instance.title or novel_instance.title == "New Novel":
                meta = get_epub_metadata(file_path)
                if meta['title']:
                    novel_instance.title = meta['title']
                    novel_instance.save()

            order_count = 1 # Untuk urutan navigasi (1, 2, 3...)
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # Cari Judul Chapter
                    title_tag = soup.find(['h1', 'h2', 'h3', 'title'])
                    if title_tag:
                        title_text = title_tag.get_text().strip()
                    else:
                        title_text = item.get_name() # Fallback nama file
                    
                    # Ambil Isi Konten
                    body_content = soup.find('body')
                    content_html = str(body_content) if body_content else str(soup)

                    # --- FITUR BARU: REGEX CHAPTER INDEX ---
                    # Mencari angka di judul: "Chapter 590", "Ch.590", "590"
                    match = re.search(r'(?:Chapter|Ch\.?|Episode|^)\s*(\d+(?:\.\d+)?)', title_text, re.IGNORECASE)
                    
                    real_index = 0
                    if match:
                        try:
                            real_index = float(match.group(1))
                        except:
                            real_index = order_count # Gagal parse? Pakai urutan file
                    else:
                        # Fallback: Kalau judul "Prologue", set index 0
                        if "prologue" in title_text.lower() or "intro" in title_text.lower():
                            real_index = 0
                        else:
                            # Kalau judul gak ada angka (Side Story), pakai urutan file
                            real_index = order_count

                    # Filter: Jangan simpan chapter kosong (kurang dari 50 karakter)
                    # Ini berguna untuk membuang halaman Copyright/Cover yang ikut ke-scan
                    if len(soup.get_text()) > 50:
                        Chapter.objects.create(
                            novel=novel_instance, 
                            title=title_text, 
                            content=content_html, 
                            order=order_count,       # Urutan Navigasi (1, 2, 3...)
                            chapter_index=real_index # Angka Asli (590, 591...)
                        )
                        order_count += 1
                        
        # --- LOGIKA TXT (Opsional, jika upload file .txt) ---
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
            chunk_size = 50 
            
            for i in range(0, len(paragraphs), chunk_size):
                chunk = paragraphs[i:i+chunk_size]
                body = "".join([f"<p>{p}</p>" for p in chunk])
                chap_num = (i // chunk_size) + 1
                
                Chapter.objects.create(
                    novel=novel_instance, 
                    title=f"Part {chap_num}", 
                    content=body, 
                    order=chap_num,
                    chapter_index=chap_num # Untuk TXT, index sama dengan urutan
                )

    except Exception as e:
        print(f"Error parsing file: {e}")