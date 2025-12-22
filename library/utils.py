import os
import re
import json
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from .models import Chapter

# =====================================================
# METADATA HELPER
# =====================================================
def get_epub_metadata(epub_path):
    metadata = {'title': None, 'author': "Unknown", 'synopsis': None, 'genre': "General"}
    try:
        book = epub.read_epub(epub_path)
        if book.get_metadata('DC', 'title'): metadata['title'] = book.get_metadata('DC', 'title')[0][0]
        if book.get_metadata('DC', 'creator'):
            raw = book.get_metadata('DC', 'creator')[0][0]
            if str(raw).strip() != "0": metadata['author'] = raw
        if book.get_metadata('DC', 'description'):
            metadata['synopsis'] = re.sub('<[^<]+?>', '', book.get_metadata('DC', 'description')[0][0])
        subjects = book.get_metadata('DC', 'subject')
        if subjects: metadata['genre'] = ", ".join(s[0] for s in subjects)[:100]
        return metadata
    except: return metadata

# =====================================================
# UTILS UTAMA
# =====================================================
def generate_chapters(novel_instance):
    if not novel_instance.epub_file: return
    file_path = novel_instance.epub_file.path

    try:
        # === PROSES EPUB ===
        if file_path.endswith('.epub'):
            book = epub.read_epub(file_path)

            # Setup Judul Novel jika baru
            if not novel_instance.title or novel_instance.title == "New Novel":
                meta = get_epub_metadata(file_path)
                if meta['title']:
                    novel_instance.title = meta['title']
                    novel_instance.alternative_title = meta['title']
                    novel_instance.save()

            order_count = 1

            for item in book.get_items():
                if item.get_type() != ebooklib.ITEM_DOCUMENT: continue

                # 1. Parse HTML
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                full_text_raw = soup.get_text(strip=True, separator='\n')
                raw_filename = item.get_name().lower()

                # -----------------------------------------------------------
                # FILTER 1: JUDUL FILE (BLACKLIST)
                # -----------------------------------------------------------
                blacklist_filenames = [
                    'table of contents', 'contents', 'index', 'copyright', 
                    'intro', 'front page', 'title page', 'acknowledgments', 
                    'nav', 'menu', 'cover', 'daftar isi', 'indeks', 
                    'pendahuluan', 'halaman judul'
                ]
                
                # Cek blacklist
                if any(x in raw_filename for x in blacklist_filenames):
                    # Pengecualian: Jika judul file mengandung kata 'chapter' atau 'bab', JANGAN skip
                    if 'chapter' not in raw_filename and 'bab' not in raw_filename:
                        print(f"[SKIP BLACKLIST] File: {item.get_name()}")
                        continue

                # -----------------------------------------------------------
                # FILTER 2: DETEKSI TOC (DILONGGARKAN)
                # -----------------------------------------------------------
                lines = [l.strip() for l in full_text_raw.split('\n') if l.strip()]
                
                # Regex mendeteksi baris yang terlihat seperti list chapter
                regex_toc = re.compile(r'^(chapter|bab|vol|volume|part|episode|bagian)\s*\d+', re.IGNORECASE)
                
                chapter_line_count = 0
                check_limit = min(len(lines), 100) 

                for i in range(check_limit):
                    if regex_toc.match(lines[i]):
                        chapter_line_count += 1
                
                # REVISI: Batas dinaikkan jadi 50. 
                # (Sebelumnya 10, yang membuat chapter dengan banyak "Part X" ikut terhapus)
                if chapter_line_count > 50:
                    print(f"[SKIP TOC CONTENT] File: {item.get_name()} (Found {chapter_line_count} chapter lines)")
                    continue

                # -----------------------------------------------------------
                # CLEANING SERVICE
                # -----------------------------------------------------------
                for s in soup(['script', 'style', 'meta', 'link']): s.decompose()
                
                # Hapus elemen sampah crawler
                for div in soup.find_all('div', id=['intro', 'footer', 'nav']): div.decompose()
                for div in soup.find_all('div', class_=['footer', 'synopsis', 'nav']): div.decompose()
                
                # Hapus Navigasi Link (Prev/Next)
                for a in soup.find_all('a'):
                    txt = a.get_text().strip().lower()
                    if txt in ['prev', 'next', 'previous', 'contents', 'daftar isi', 'index']:
                        a.decompose()

                # -----------------------------------------------------------
                # HAPUS JUDUL GANDA (HEADER & PARAGRAF)
                # -----------------------------------------------------------
                final_title = ""

                # A. Ambil & Hapus Header
                header_tag = soup.find(['h1', 'h2', 'h3', 'title'])
                if header_tag:
                    final_title = header_tag.get_text(strip=True)
                    header_tag.decompose()

                # B. Ambil & Hapus Paragraf Judul (<p>Chapter X...)
                regex_chapter_title = re.compile(r'^(chapter|bab|episode|part|bagian|vol|volume)\s*\d+', re.IGNORECASE)

                for p in soup.find_all('p', limit=10):
                    text = p.get_text(strip=True)
                    if not text: continue

                    if regex_chapter_title.match(text):
                        if not final_title:
                            final_title = text
                        p.decompose() # Hapus dari body agar tidak dobel

                # Fallback Title
                if not final_title:
                    final_title = item.get_name()

                # Filter Akhir: Judul Blacklist
                if any(x in final_title.lower() for x in blacklist_filenames):
                     # Pengecualian lagi untuk 'Chapter'
                    if 'chapter' not in final_title.lower():
                        continue
                
                if final_title.strip().lower() == novel_instance.title.strip().lower():
                    continue

                # -----------------------------------------------------------
                # SIMPAN
                # -----------------------------------------------------------
                body = soup.find('body')
                content_html = body.decode_contents() if body else str(soup)
                content_html = content_html.strip()

                # Cek Konten Kosong (Batas diturunkan jadi 20 char)
                if len(BeautifulSoup(content_html, "html.parser").get_text(strip=True)) < 20:
                    print(f"[SKIP EMPTY] File: {item.get_name()} (Content too short)")
                    continue

                # Indexing
                match = re.search(r'(?:chapter|bab|ep|part)\s*(\d+(\.\d+)?)', final_title, re.IGNORECASE)
                chapter_index = float(match.group(1)) if match else order_count
                
                if any(x in final_title.lower() for x in ["prologue", "intro", "pendahuluan"]): 
                    chapter_index = 0

                Chapter.objects.create(
                    novel=novel_instance,
                    title=final_title,
                    content=content_html,
                    order=order_count,
                    chapter_index=chapter_index
                )
                order_count += 1

        # === PROSES TXT ===
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            parts = [p for p in content.split('\n\n') if p.strip()]
            chunk_size = 30
            for i in range(0, len(parts), chunk_size):
                body = "".join(f"<p>{line.strip()}</p>" for line in parts[i:i+chunk_size])
                chap = (i // chunk_size) + 1
                Chapter.objects.create(novel=novel_instance, title=f"Part {chap}", content=body, order=chap, chapter_index=chap)

        novel_instance.save()

    except Exception as e:
        print(f"Error processing: {e}")