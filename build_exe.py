"""
Crée un .exe standalone avec PyInstaller
Utilisation : python build_exe.py
"""

import PyInstaller.__main__
import sys
import os

# Cherche le fichier calculatrice
calc_file = "calculatrice_3eme.py"

if not os.path.exists(calc_file):
    print(f"❌ Erreur : {calc_file} non trouvé !")
    sys.exit(1)

print("🔨 Compilation du .exe en cours...")

PyInstaller.__main__.run([
    calc_file,
    '--onefile',                          # Un seul .exe
    '--windowed',                         # Pas de console noire
    '--name=Calculatrice_3eme',           # Nom du .exe
    '--hidden-import=matplotlib.backends.backend_tkagg',
    '--hidden-import=sympy',
    '--hidden-import=PIL',
    '--distpath=./dist',
    '--workpath=./build',
])

print("\n✅ .exe créé dans le dossier ./dist/")
