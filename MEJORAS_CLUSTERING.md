# Mejoras al Modelo de Clustering

## Análisis del Problema

### Problema Identificado
El modelo original agrupaba prendas por **tipo de prenda** (`slot`) en lugar de por **estilo**. Esto significa que un vestido casual veraniego y una camiseta casual veraniega estarían en clusters diferentes, cuando deberían estar juntas porque comparten el mismo estilo.

### ¿Por qué `prep_articles.py` tiene sentido?

**✅ SÍ, `prep_articles.py` es muy útil y debe mantenerse** porque:

1. **Normalización de datos**: Los datos originales de H&M son inconsistentes
   - Colores con variaciones: "grey" vs "gray", "turquoise" → normalizado a "blue"
   - Textos con mayúsculas/minúsculas inconsistentes

2. **Extracción de información semántica**:
   - **Temporada**: Extrae de descripciones (busca palabras como "coat", "jacket" → invierno)
   - **Formalidad**: Identifica de nombres de producto (busca "blazer", "suit" → formal)
   - **Tipo de tejido**: Extrae de descripciones (busca "cotton", "wool", "linen")
   - **Nivel de abrigo**: Calcula a partir de temporada

3. **Limpieza de datos**:
   - Normaliza textos
   - Elimina caracteres especiales
   - Maneja valores faltantes

**Conclusión**: `prep_articles.py` es esencial. Sin él, tendríamos datos inconsistentes y no podríamos extraer características de estilo de forma confiable.

---

## Mejoras Implementadas

### 1. **Eliminación de Variables No Relevantes para Estilo**

#### ❌ Variables ELIMINADAS:
- **`slot`** (tipo de prenda): No queremos agrupar por tipo, sino por estilo
  - Ejemplo: Un vestido casual veraniego y una camiseta casual veraniega deberían estar juntas
- **`desc_length`**: Longitud de descripción no es relevante para estilo

#### ✅ Variables MANTENIDAS (características de ESTILO):
- **`formalidad`**: casual, intermedio, formal
- **`temporada`**: invierno, verano, neutra
- **`nivel_abrigo`**: 1=ligero, 2=medio, 3=abrigado
- **`color_base`**: black, white, blue, etc.
- **`fabric_type`**: cotton, wool, linen, etc.

### 2. **Evaluación de Calidad del Clustering**

Añadidas métricas para evaluar la calidad:

- **Silhouette Score**: Mide qué tan bien separados están los clusters
  - Rango: -1 a 1
  - Más alto = mejor
  - Valores > 0.3 indican clusters razonablemente bien definidos

- **Inertia**: Suma de distancias al centroide
  - Más bajo = mejor
  - Indica qué tan compactos son los clusters

### 3. **Búsqueda Automática del Número Óptimo de Clusters**

Nuevo parámetro `--find_optimal` que:
- Evalúa diferentes valores de k (2 a max_clusters)
- Calcula Silhouette Score para cada k
- Sugiere el mejor k automáticamente
- Aplica Elbow Method para validación adicional

### 4. **Análisis Detallado de Clusters**

El script ahora muestra:
- Distribución de prendas por cluster
- Características dominantes de cada cluster:
  - Formalidad más común
  - Temporada más común
  - Color más común
  - Tejido más común
  - Nivel de abrigo promedio

---

## Comparación: Modelo Original vs Mejorado

| Aspecto | Modelo Original | Modelo Mejorado |
|---------|----------------|-----------------|
| **Variables** | 7 (incluye `slot`, `desc_length`) | 5 (solo características de estilo) |
| **Agrupación** | Por tipo de prenda + estilo | Solo por estilo |
| **Evaluación** | Ninguna | Silhouette Score + Inertia |
| **Optimización** | Manual (k fijo) | Automática (`--find_optimal`) |
| **Análisis** | Básico (solo conteos) | Detallado (características dominantes) |

---

## Uso del Modelo Mejorado

### Uso Básico (k fijo):
```bash
python -m src.build_style_clusters_improved \
    --input data/raw/hm/articles_final.csv \
    --output data/raw/hm/articles_final_clustered.csv \
    --n_clusters 4
```

### Uso con Optimización Automática:
```bash
python -m src.build_style_clusters_improved \
    --input data/raw/hm/articles_final.csv \
    --output data/raw/hm/articles_final_clustered.csv \
    --find_optimal \
    --max_clusters 10
```

---

## Resultados Esperados

Con el modelo mejorado, los clusters deberían agrupar prendas por:

1. **Estilo casual veraniego**: Camisetas, vestidos, shorts - colores claros, tejidos ligeros (linen, cotton)
2. **Estilo formal invernal**: Blazers, abrigos, pantalones formales - colores oscuros, tejidos pesados (wool)
3. **Estilo intermedio neutro**: Prendas versátiles, temporada neutra, colores neutros
4. **Estilo casual invernal**: Sudaderas, jerséis, pantalones cómodos - tejidos cálidos

**Nota**: Los clusters exactos dependerán de los datos, pero ahora agruparán por características de estilo, no por tipo de prenda.

---

## Próximos Pasos Recomendados

1. **Ejecutar el modelo mejorado** con `--find_optimal` para encontrar el mejor k
2. **Analizar los clusters resultantes** para verificar que tienen sentido estilísticamente
3. **Ajustar k manualmente** si es necesario según interpretación de negocio
4. **Validar visualmente** revisando ejemplos de prendas en cada cluster

---

## Preguntas Frecuentes

**P: ¿Por qué no usar los datos originales sin prep_articles.py?**  
R: Los datos originales son inconsistentes (colores variados, textos sin normalizar). `prep_articles.py` extrae y normaliza características de estilo que son esenciales para el clustering.

**P: ¿Por qué quitar `slot` si es una característica de la prenda?**  
R: Queremos agrupar por **estilo**, no por tipo. Un vestido y una camiseta pueden tener el mismo estilo (casual, veraniego, algodón, color claro) y deberían estar juntas.

**P: ¿Cómo sé si el clustering es bueno?**  
R: El Silhouette Score te da una métrica objetiva. Valores > 0.3 son razonables. También puedes revisar manualmente si las prendas de cada cluster tienen sentido estilísticamente.

**P: ¿Cuántos clusters debería usar?**  
R: Usa `--find_optimal` para encontrar el mejor k automáticamente. Generalmente, 3-6 clusters funcionan bien para estilos de ropa.

