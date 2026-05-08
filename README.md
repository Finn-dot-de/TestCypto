```python
import zipfile
import os

def bloat_docx(file_path, megabytes_to_add):
    dummy_data = os.urandom(megabytes_to_add * 1024 * 1024)
    
    # Öffne das .docx im Append-Modus ('a')
    with zipfile.ZipFile(file_path, 'a') as docx_zip:
        docx_zip.writestr("hidden_bloat.dat", dummy_data, compress_type=zipfile.ZIP_STORED)
        
    print(f"Erfolgreich echte {megabytes_to_add} MB in {file_path} gepumpt!")

bloat_docx("dein_dokument.docx", 10)
```
