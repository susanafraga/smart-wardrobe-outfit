# Mejoras en la Lógica de Temporada

## Problema Identificado

La lógica original de temporada era muy básica:
- Solo buscaba palabras clave simples
- Solo tenía 3 temporadas: invierno, verano, neutra
- No consideraba el tipo de tejido
- Asignaba temporadas de forma poco precisa

## Mejoras Implementadas

### 1. **Nuevas Temporadas**
Ahora el sistema reconoce **5 temporadas**:
- **Invierno**: Prendas muy abrigadas (wool, cashmere, fur, velvet)
- **Otoño**: Prendas abrigadas pero no extremas (cardigans, sweaters, blazers)
- **Primavera**: Prendas ligeras pero no extremas (camisas, prendas de transición)
- **Verano**: Prendas muy ligeras (linen, chiffon, silk, shorts, tank tops)
- **Neutra**: Prendas que pueden usarse en cualquier temporada

### 2. **Lógica Mejorada Basada en Tejidos**

#### Tejidos por Temporada:

**Invierno/Otoño (muy abrigosos):**
- wool, cashmere, fur, velvet, suede, leather

**Verano/Primavera (ligeros):**
- linen, chiffon, silk

**Intermedios (primavera/otoño):**
- cotton, denim, viscose, polyester, nylon

### 3. **Sistema de Prioridades**

La función `temporada()` ahora usa un sistema de prioridades:

1. **Prioridad 1: Tejido muy específico**
   - Si es wool/cashmere/fur → invierno u otoño
   - Si es linen/chiffon/silk → verano o primavera

2. **Prioridad 2: Palabras clave muy específicas**
   - "coat", "parka", "puffer" → invierno
   - "shorts", "tank", "swim" → verano
   - "cardigan", "sweater", "knit" → otoño
   - "light", "breathable" → primavera

3. **Prioridad 3: Tejidos intermedios + contexto**
   - Cotton/denim con palabras "warm"/"cozy" → otoño
   - Cotton/denim con palabras "light"/"breathable" → primavera
   - Por defecto: primavera para tejidos intermedios

### 4. **Nivel de Abrigo Mejorado**

El `nivel_abrigo` ahora se calcula de forma más precisa:
- **Invierno**: 3 (muy abrigado)
- **Otoño**: 3 (abrigado, redondeado desde 2.5)
- **Primavera**: 2 (ligero, redondeado desde 1.5)
- **Verano**: 1 (muy ligero)
- **Neutra**: 2 (medio)

## Ejemplo de Funcionamiento

### Antes:
- Camiseta de algodón → "neutra" (impreciso)
- Jersey de lana → "invierno" (correcto pero limitado)

### Ahora:
- Camiseta de algodón ligero → "primavera" o "verano" (más preciso)
- Jersey de lana → "invierno" o "otoño" según contexto (más preciso)
- Cardigan de algodón → "otoño" (más preciso)
- Blazer de lino → "primavera" o "verano" (más preciso)

## Cómo Regenerar los Datos

### Opción 1: Script Automático (Recomendado)

```bash
python regenerate_pipeline.py
```

Este script:
1. Regenera `articles_final.csv` con la nueva lógica de temporada
2. Regenera `articles_final_clustered.csv` con el clustering mejorado

### Opción 2: Manual

```bash
# Paso 1: Regenerar articles_final.csv
python data/raw/hm/prep_articles.py \
    --input data/raw/hm/articles.csv \
    --output data/raw/hm/articles_final.csv

# Paso 2: Regenerar articles_final_clustered.csv
python -m src.build_style_clusters \
    --input data/raw/hm/articles_final.csv \
    --output data/raw/hm/articles_final_clustered.csv \
    --n_clusters 4
```

## Impacto en el Clustering

Con las nuevas temporadas (5 en lugar de 3), el clustering tendrá más granularidad:
- Los clusters podrán distinguir mejor entre estilos de otoño vs invierno
- Los clusters podrán distinguir mejor entre estilos de primavera vs verano
- Mejor agrupación por características de estilo reales

## Validación

Después de regenerar, puedes validar los resultados:

1. **Distribución de temporadas**:
   ```python
   import pandas as pd
   df = pd.read_csv("data/raw/hm/articles_final.csv")
   print(df["temporada"].value_counts())
   ```

2. **Verificar coherencia tejido-temporada**:
   ```python
   # Ver prendas de lana
   print(df[df["fabric_type"] == "wool"]["temporada"].value_counts())
   # Deberían ser principalmente invierno/otoño
   
   # Ver prendas de lino
   print(df[df["fabric_type"] == "linen"]["temporada"].value_counts())
   # Deberían ser principalmente verano/primavera
   ```

## Notas Técnicas

- La función `temporada()` ahora extrae el tejido inline para evitar dependencias circulares
- El orden de ejecución en `prep_articles.py` es importante: `fabric_type` se calcula antes de `temporada`
- El clustering sigue funcionando igual, solo que ahora tiene más información precisa en la variable `temporada`

