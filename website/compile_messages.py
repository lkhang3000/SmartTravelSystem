#!/usr/bin/env python
"""
Compile Django .po files to .mo files using polib
"""
import os
import polib

def compile_po_files(locale_dir='locale'):
    """Compile all .po files in locale directory"""
    compiled = 0
    errors = 0
    
    # Walk through locale directory
    for root, dirs, files in os.walk(locale_dir):
        for filename in files:
            if filename.endswith('.po'):
                po_path = os.path.join(root, filename)
                mo_path = po_path[:-3] + '.mo'
                
                try:
                    # Load .po file and save as .mo
                    po = polib.pofile(po_path)
                    po.save_as_mofile(mo_path)
                    compiled += 1
                    print(f"✅ Compiled: {po_path} → {mo_path}")
                except Exception as e:
                    errors += 1
                    print(f"❌ Error compiling {po_path}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Compiled: {compiled} files")
    print(f"   Errors: {errors} files")
    
    if compiled > 0:
        print(f"\n✅ Translation files compiled successfully!")
        print(f"   Restart Django server to apply changes")

if __name__ == '__main__':
    compile_po_files()
