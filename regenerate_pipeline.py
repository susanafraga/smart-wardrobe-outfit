#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regenerate_pipeline.py

Script para regenerar todo el pipeline de datos:
1. Regenera articles_final.csv con la nueva lógica de temporada mejorada
2. Regenera articles_final_clustered.csv con el clustering mejorado

Uso:
    python regenerate_pipeline.py
"""

import os
import subprocess
import sys

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_CSV = os.path.join(BASE_DIR, "data", "raw", "hm", "articles.csv")
ARTICLES_FINAL = os.path.join(BASE_DIR, "data", "raw", "hm", "articles_final.csv")
ARTICLES_CLUSTERED = os.path.join(BASE_DIR, "data", "raw", "hm", "articles_final_clustered.csv")
PREP_SCRIPT = os.path.join(BASE_DIR, "data", "raw", "hm", "prep_articles.py")
CLUSTER_SCRIPT = os.path.join(BASE_DIR, "src", "build_style_clusters.py")


def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"\n{'='*60}")
    print(f"[*] {description}")
    print(f"{'='*60}")
    print(f"Comando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=BASE_DIR
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error ejecutando: {description}")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"[ERROR] No se encontro el comando. Estas en el entorno virtual correcto?")
        return False


def main():
    print("[*] Regenerando pipeline completo de datos")
    print(f"Directorio base: {BASE_DIR}")
    
    # Verificar que existe articles.csv
    if not os.path.exists(ARTICLES_CSV):
        print(f"[ERROR] No se encuentra: {ARTICLES_CSV}")
        print("   Asegurate de que el archivo articles.csv existe.")
        sys.exit(1)
    
    # Paso 1: Regenerar articles_final.csv
    print(f"\n[PASO 1] Regenerando articles_final.csv")
    print(f"   Input: {ARTICLES_CSV}")
    print(f"   Output: {ARTICLES_FINAL}")
    
    cmd1 = [
        sys.executable,
        PREP_SCRIPT,
        "--input", ARTICLES_CSV,
        "--output", ARTICLES_FINAL
    ]
    
    if not run_command(cmd1, "Generando articles_final.csv con nueva logica de temporada"):
        print("[ERROR] Fallo la generacion de articles_final.csv")
        sys.exit(1)
    
    # Verificar que se creó
    if not os.path.exists(ARTICLES_FINAL):
        print(f"[ERROR] No se genero: {ARTICLES_FINAL}")
        sys.exit(1)
    
    print(f"[OK] articles_final.csv generado correctamente")
    
    # Paso 2: Regenerar articles_final_clustered.csv
    print(f"\n[PASO 2] Regenerando articles_final_clustered.csv")
    print(f"   Input: {ARTICLES_FINAL}")
    print(f"   Output: {ARTICLES_CLUSTERED}")
    
    cmd2 = [
        sys.executable,
        "-m", "src.build_style_clusters",
        "--input", ARTICLES_FINAL,
        "--output", ARTICLES_CLUSTERED,
        "--n_clusters", "5"
    ]
    
    if not run_command(cmd2, "Generando articles_final_clustered.csv con clustering mejorado"):
        print("[ERROR] Fallo la generacion de articles_final_clustered.csv")
        sys.exit(1)
    
    # Verificar que se creó
    if not os.path.exists(ARTICLES_CLUSTERED):
        print(f"[ERROR] No se genero: {ARTICLES_CLUSTERED}")
        sys.exit(1)
    
    print(f"[OK] articles_final_clustered.csv generado correctamente")
    
    # Resumen final
    print(f"\n{'='*60}")
    print("[OK] Pipeline regenerado completamente")
    print(f"{'='*60}")
    print(f"Archivos generados:")
    print(f"   - {ARTICLES_FINAL}")
    print(f"   - {ARTICLES_CLUSTERED}")
    print(f"\nMejoras aplicadas:")
    print(f"   - Temporada mejorada: invierno, otono, primavera, verano, neutra")
    print(f"   - Uso de tipo de tejido para determinar temporada")
    print(f"   - Clustering sin 'slot' (solo por estilo)")
    print(f"\n[OK] Listo para usar en la aplicacion!")


if __name__ == "__main__":
    main()
