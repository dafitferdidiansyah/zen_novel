import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from .models import Chapter
import os

def generate_chapters(novel_instance):
    if not novel_instance.epub_file: return
    file_path = novel_instance.epub_file.path
    
    try:
        # --- LOGIKA EPUB ---
        if file_path.endswith('.epub'):
            book = epub.read_epub(file_path)
            # Auto-fill judul jika kosong
            if novel_instance.title == "New Novel" or not novel_instance.title:
                try:
                    novel_instance.title = book.get_metadata('DC', 'title')[0][0]
                    novel_instance.save()
                except: pass

            order_count = 1
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    title_tag = soup.find(['h1', 'h2', 'h3'])
                    
                    if title_tag:
                        title_text = title_tag.get_text().strip()
                    else:
                        title_text = f"Chapter {order_count}"
                    
                    text_content = ""
                    for p in soup.find_all('p'):
                        text_content += str(p)
                    
                    if len(text_content) > 100:
                        Chapter.objects.create(novel=novel_instance, title=title_text, content=text_content, order=order_count)
                        order_count += 1
                        
        # --- LOGIKA TXT ---
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Split per paragraf (baris baru)
            paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
            chunk_size = 50 # 50 Paragraf per chapter
            
            for i in range(0, len(paragraphs), chunk_size):
                chunk = paragraphs[i:i+chunk_size]
                body = "".join([f"<p>{p}</p>" for p in chunk])
                chap_num = (i // chunk_size) + 1
                
                Chapter.objects.create(
                    novel=novel_instance, 
                    title=f"Part {chap_num}", 
                    content=body, 
                    order=chap_num
                )
    except Exception as e:
        print(f"Error parsing: {e}")