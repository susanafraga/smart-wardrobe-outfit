# Explicación de la aplicación Smart Wardrobe
## Render Link
https://smart-wardrobe-outfit.onrender.com/


## Índice
1. [Visión General](#visión-general)
2. [Modelo de Clustering](#modelo-de-clustering)
3. [Sistema de Recomendación y Scores](#sistema-de-recomendación-y-scores)
4. [Programación por Restricciones](#programación-por-restricciones)
5. [Flujo de la Aplicación](#flujo-de-la-aplicación)
6. [Arquitectura Técnica](#arquitectura-técnica)

---

## Visión General

La aplicación **Smart Wardrobe** es un sistema de recomendación de outfits que combina:
- **Clustering no supervisado (K-Means)** para agrupar prendas por estilo
- **Programación por restricciones** para generar combinaciones válidas
- **Sistema de scoring multi-criterio** para evaluar y rankear outfits
- **Integración con APIs meteorológicas** para adaptar recomendaciones al clima

El objetivo es generar 3 outfits personalizados que se adapten a:
- Condiciones meteorológicas (temperatura, lluvia)
- Tipo de evento (formalidad requerida)
- Preferencias de estilo (coherencia de clusters)
- Restricciones de color y tejido según el evento

---

## Preprocesamiento de Datos (prep_articles.py)

Antes de aplicar el clustering, es necesario **extraer y estructurar características** de las prendas desde los datos raw. Este proceso se realiza en `prep_articles.py`.

### Objetivo

Transformar `articles.csv` (datos raw) en `articles_final.csv` (datos estructurados con features extraídas).

### Características Extraídas

#### 1. **Temporada** (`temporada`)

Se determina mediante un sistema de prioridades basado en:
- **Tipo de tejido**: Tejidos específicos indican temporada (ej: lana → invierno, lino → verano)
- **Palabras clave en descripción**: Términos como "winter", "summer", "beach", etc.
- **Fabric type**: Algodón, poliéster, etc. ayudan a determinar temporada

**Lógica de 5 temporadas:**
- `invierno`: Tejidos abrigados (wool, fleece) o keywords de invierno
- `otoño`: Tejidos intermedios (corduroy, tweed) o keywords de otoño
- `primavera`: Tejidos ligeros (cotton, linen) o keywords de primavera
- `verano`: Tejidos muy ligeros (linen, chiffon) o keywords de verano
- `neutra`: Si no se puede determinar claramente

#### 2. **Formalidad** (`formalidad`)

Se extrae de la descripción y tipo de prenda:
- **`formal`**: Palabras clave como "elegant", "suit", "dress", tejidos formales (silk, satin, velvet)
- **`casual`**: Palabras clave como "casual", "sport", "denim", "cotton"
- **`intermedio`**: Caso por defecto o prendas versátiles

#### 3. **Nivel de Abrigo** (`nivel_abrigo`)

Mapeo de temporada a nivel numérico:
- `invierno` → 3 (muy abrigado)
- `otoño` → 2.5 (abrigado)
- `primavera` → 1.5 (ligero)
- `verano` → 1 (muy ligero)
- `neutra` → 2 (medio)

#### 4. **Color Base** (`color_base`)

Extracción del color principal desde:
- Campo `colour_group_name` del CSV original
- Normalización a colores base (black, white, red, blue, etc.)
- Manejo de colores compuestos y variaciones

#### 5. **Tipo de Tejido** (`fabric_type`)

Extracción desde:
- Campo `detail_desc` (descripción detallada)
- Búsqueda de keywords: "cotton", "polyester", "denim", "silk", "wool", "linen", etc.
- Normalización y categorización

### Pipeline de Preprocesamiento

```
articles.csv (raw)
    ↓
1. Extracción de temporada (función temporada())
    ↓
2. Extracción de formalidad (función formalidad())
    ↓
3. Cálculo de nivel_abrigo (función nivel_abrigo_from_temp())
    ↓
4. Extracción de color_base (normalización)
    ↓
5. Extracción de fabric_type (búsqueda en descripción)
    ↓
articles_final.csv (con todas las features)
```

### Importancia del Preprocesamiento

Este paso es **crítico** porque:
- **Estructura los datos**: Convierte texto libre en características estructuradas
- **Normaliza valores**: Unifica diferentes formas de expresar lo mismo
- **Extrae información implícita**: La temporada no está explícita, se infiere
- **Prepara para ML**: Crea features numéricas y categóricas listas para clustering

**Sin este preprocesamiento**, el clustering no tendría features útiles para agrupar por estilo.

---

## Modelo de Clustering

### Tipo de Clustering: K-Means

Se utiliza **K-Means clustering**, un algoritmo de aprendizaje no supervisado que agrupa datos en K clusters basándose en la similitud de sus características.

### Características Utilizadas para Clustering

El clustering se realiza sobre las siguientes características **ya extraídas en prep_articles.py**:

1. **Formalidad** (one-hot encoded): `casual`, `intermedio`, `formal`
2. **Temporada** (one-hot encoded): `invierno`, `otoño`, `primavera`, `verano`, `neutra`
3. **Color base** (one-hot encoded): colores principales de la prenda
4. **Tipo de tejido** (one-hot encoded): `cotton`, `polyester`, `denim`, `silk`, etc.
5. **Nivel de abrigo** (numérico, normalizado): escala 1-3 (ligero, medio, abrigado)

**Características excluidas del clustering:**
- `slot` (tipo de prenda): No relevante para agrupar por estilo
- `desc_length`: No aporta información de estilo

### Preprocesamiento

1. **One-Hot Encoding**: Variables categóricas convertidas a variables binarias
2. **StandardScaler**: Normalización de variables numéricas (nivel_abrigo)
3. **Pipeline de scikit-learn**: Preprocesamiento automático y consistente

### Número de Clusters

Se utilizan **5 clusters** fijos, determinados mediante:
- Análisis de silhouette score
- Evaluación de coherencia interna de clusters
- Balance entre granularidad y utilidad práctica

### Resultado

Cada prenda recibe un `style_cluster` (0-4) que indica a qué grupo de estilo pertenece. Los clusters agrupan prendas con características similares (misma formalidad, temporada, colores y tejidos afines).

---

## Sistema de Recomendación y Scores

### Arquitectura del Sistema de Scoring

El sistema utiliza un **modelo de scoring multi-criterio** que combina varios factores:

#### 1. Score Base por Prenda (`_score_prenda`)

Para cada prenda individual, se calcula un score que considera:

- **Adecuación a la temperatura**: Bonus/penalización según el `nivel_abrigo` vs temperatura objetivo
- **Adecuación a la lluvia**: Penalización si la prenda tiene tejidos sensibles a la lluvia (seda, lino, etc.)
- **Adecuación a la formalidad**: Bonus si la formalidad de la prenda coincide con la requerida
- **Preferencias del evento**:
  - **Colores preferidos**: Bonus si el color coincide con preferencias del evento (ej: negro para "Noche")
  - **Colores a evitar**: Penalización si el color no es adecuado (ej: colores muy vivos para "Oficina")
  - **Tejidos preferidos/evitados**: Bonus/penalización según tejido (ej: evitar denim en eventos formales)

#### 2. Score de Combinación de Colores (`_color_combo_score`)

Evalúa la armonía cromática del outfit:
- Bonus si los colores son neutros y combinables
- Penalización si hay demasiados colores contrastantes
- Considera paletas de colores complementarios

#### 3. Score de Coherencia de Clusters (`_cluster_coherence_score`)

- **Bonus por coherencia**: Si todas las prendas pertenecen al mismo cluster → multiplicador 1.2
- **Bonus moderado**: Si hay 2 clusters → multiplicador 1.1
- **Sin bonus**: Si hay 3+ clusters diferentes → multiplicador 1.0

Esto promueve outfits con estilo coherente.

#### 4. Score de Match con Cluster Objetivo (`_cluster_match_score`)

Si se especifica un cluster objetivo:
- Bonus adicional (multiplicador 1.15) si las prendas pertenecen al cluster objetivo

#### 5. Score Final del Outfit

```
score_outfit = (score_promedio_prendas) × (color_combo_score) × (cluster_coherence) × (cluster_match)
```

### Ejemplo de Cálculo

Para un outfit con 3 prendas:
1. Score individual de cada prenda: 0.8, 0.9, 0.85 → promedio = 0.85
2. Color combo score: 1.1 (colores bien combinados)
3. Cluster coherence: 1.2 (todas del mismo cluster)
4. Score final: 0.85 × 1.1 × 1.2 = **1.122**

---

## Programación por Restricciones

### Restricciones Implementadas

El sistema genera outfits válidos aplicando las siguientes restricciones:

#### 1. Restricciones de Completitud

- **Outfit tipo "conjunto"**: Debe tener `top` + `bottom` + `shoes`
- **Outfit tipo "vestido"**: Debe tener `dress` + `shoes`
- No se permiten outfits incompletos

#### 2. Restricciones de Disjunción

- Los 3 outfits seleccionados **no pueden compartir prendas**
- Se utiliza un algoritmo greedy que selecciona outfits disjuntos:
  1. Ordena todos los outfits por score descendente
  2. Selecciona el mejor outfit
  3. Marca sus prendas como "usadas"
  4. Continúa con el siguiente outfit que no use prendas ya seleccionadas

#### 3. Restricciones de Heurísticas (`_passes_heuristics`)

Heurísticas que descartan outfits inválidos:

- **Lluvia + tejidos sensibles**: Si llueve y hay tejidos como seda, lino, chiffon → descartar
- **Formal + denim**: Si es evento formal y hay denim → descartar
- **Formal + tejidos formales**: Si es formal, al menos la mitad de las prendas deben ser de tejidos formales (satin, silk, lace, velvet, crepe, chiffon)
- **Frío extremo**: Si temp ≤ 10°C y el nivel de abrigo promedio es muy bajo → descartar
- **Formal + colores fuertes**: Si es formal y hay más de 2 colores muy vivos → descartar

#### 4. Restricciones de Evento

Cada tipo de evento tiene restricciones específicas:

**Ejemplo: "Noche"**
- Preferencia: Color negro (bonus)
- Evitar: Colores muy claros (penalización)

**Ejemplo: "Oficina"**
- Preferencia: Colores neutros (negro, gris, beige, blanco)
- Evitar: Colores muy vivos, denim (penalización fuerte)

**Ejemplo: "Cita / Restaurante"**
- Formalidad: `formal`
- Preferencia: Colores elegantes, tejidos formales

### Algoritmo de Generación

```
1. Filtrar prendas por segmento (mujer/hombre/niño)
2. Generar TODAS las combinaciones válidas posibles:
   - Para cada vestido → combinar con zapatos
   - Para cada top → combinar con cada bottom → combinar con zapatos
3. Para cada combinación:
   - Aplicar heurísticas (descartar si no pasa)
   - Calcular score completo
4. Ordenar todos los outfits por score descendente
5. Seleccionar top 20 para análisis
6. Seleccionar top 3 disjuntos (sin compartir prendas)
```

---

## Flujo de la Aplicación

### 1. Entrada del Usuario

El usuario proporciona:
- **Ciudad**: Para obtener condiciones meteorológicas
- **Fecha**: Para previsión meteorológica
- **Tipo de evento**: `Casual`, `Oficina`, `Noche`, `Deporte`, `Cita / Restaurante`, `Evento formal`
- **Perfil**: `Mujer`, `Hombre`, `Niño/a`, `Cualquiera`

### 2. Obtención de Datos Meteorológicos

- Se utiliza la API de **Open-Meteo** para obtener:
  - Temperatura en °C
  - Probabilidad de lluvia
- Si la API falla, se usan valores por defecto (20°C, sin lluvia)

### 3. Mapeo de Evento a Formalidad

```
Casual → formalidad: "casual"
Oficina → formalidad: "formal"
Noche → formalidad: "intermedio"
Deporte → formalidad: "casual"
Cita / Restaurante → formalidad: "formal"
Evento formal → formalidad: "formal"
```

### 4. Obtención de Preferencias del Evento

Cada evento tiene preferencias específicas almacenadas en `get_event_preferences()`:
- Colores preferidos (bonus)
- Colores a evitar (penalización)
- Tejidos preferidos/evitados

### 5. Generación de Outfits

1. **Filtrado inicial**: Filtrar catálogo por perfil seleccionado
2. **Generación de combinaciones**: Crear todas las combinaciones válidas
3. **Evaluación**: Calcular score para cada outfit
4. **Filtrado por heurísticas**: Descartar outfits que no pasan las heurísticas
5. **Ordenamiento**: Ordenar por score descendente
6. **Selección**: Elegir top 3 disjuntos

### 6. Visualización

- **Pestaña "Outfits recomendados"**: Muestra los 3 outfits seleccionados con imágenes y detalles
- **Pestaña "Análisis (gráficos)"**: Muestra análisis detallado:
  - Distribución de colores
  - Top 20 outfits evaluados con scores
  - Distribución de clusters en los outfits

---

## Arquitectura Técnica

### Stack Tecnológico

- **Backend**: Python 3.x
- **Framework Web**: Dash (Plotly)
- **UI Components**: Dash Bootstrap Components
- **Machine Learning**: scikit-learn (KMeans, preprocessing)
- **Data Processing**: pandas, numpy
- **APIs Externas**: Open-Meteo (clima)

### Estructura de Archivos

```
app.py                          # Aplicación principal Dash
src/
  ├── model.py                  # Lógica de recomendación y scoring
  ├── graphics.py              # Visualizaciones de análisis
  ├── catalog_graphics.py      # Visualizaciones del catálogo
  ├── build_style_clusters.py  # Script de clustering
  ├── weather_api.py           # Integración con API meteorológica
data/
  └── raw/hm/
      ├── articles_final.csv              # Datos preprocesados
      ├── articles_final_clustered.csv   # Datos con clusters
      └── prep_articles.py               # Script de preprocesamiento
```

### Flujo de Datos

```
articles.csv (raw)
    ↓
prep_articles.py
    ↓
articles_final.csv (con features: temporada, formalidad, nivel_abrigo, etc.)
    ↓
build_style_clusters.py
    ↓
articles_final_clustered.csv (con style_cluster)
    ↓
model.py (carga datos y genera recomendaciones)
    ↓
app.py (muestra resultados)
```

### Almacenamiento de Datos

- **CSV files**: Datos persistentes de prendas y clusters
- **Dash Stores**: Almacenamiento en memoria del navegador:
  - `recommendation-store`: Almacena la recomendación generada
  - `cart-store`: Almacena items del carrito (si se implementa)

---

## Ejemplo Completo de Funcionamiento

### Caso de Uso: "Oficina en Madrid, 15°C, sin lluvia"

1. **Input**: Ciudad=Madrid, Fecha=27/11/2025, Evento=Oficina, Perfil=Mujer

2. **Procesamiento**:
   - API clima: 15°C, sin lluvia
   - Formalidad objetivo: `formal`
   - Preferencias: Colores neutros (bonus), evitar denim (penalización fuerte)

3. **Generación**:
   - Se generan ~500 combinaciones posibles
   - Se descartan ~200 por heurísticas (denim en formal, etc.)
   - Se evalúan ~300 outfits con scores

4. **Scores ejemplo**:
   - Outfit A: Score 1.211 (todas prendas Cluster 3, colores neutros, formal)
   - Outfit B: Score 1.208 (Cluster 3, pero menos coherente)
   - Outfit C: Score 1.205 (mezcla de clusters)

5. **Selección**:
   - Top 3 outfits disjuntos seleccionados
   - Todos del Cluster 3 (estilo coherente)
   - Colores neutros predominantes
   - Adecuados para 15°C

---

## Ventajas del Enfoque

1. **Clustering**: Agrupa prendas por estilo, permitiendo outfits coherentes
2. **Scoring multi-criterio**: Balancea múltiples factores (clima, formalidad, estilo, colores)
3. **Restricciones**: Garantiza outfits válidos y prácticos
4. **Personalización**: Se adapta a evento, clima y perfil del usuario
5. **Transparencia**: Los gráficos muestran por qué se seleccionaron los outfits

---

## Limitaciones y Mejoras Futuras

### Limitaciones Actuales

1. **Número fijo de clusters**: 5 clusters pueden no ser óptimos para todos los casos
2. **Heurísticas fijas**: Las reglas están hardcodeadas
3. **Sin aprendizaje**: No aprende de preferencias del usuario
4. **Generación exhaustiva**: Puede ser lenta con catálogos muy grandes

### Mejoras Posibles

1. **Clustering adaptativo**: Determinar número óptimo de clusters automáticamente
2. **Machine Learning**: Modelo que aprenda de interacciones del usuario
3. **Optimización**: Algoritmos más eficientes para catálogos grandes
4. **Más restricciones**: Tallas, presupuesto, etc.

---

## Conclusión

La aplicación combina técnicas de **Machine Learning no supervisado** (clustering) con **programación por restricciones** y **sistemas de scoring multi-criterio** para generar recomendaciones personalizadas de outfits que se adaptan al contexto del usuario (clima, evento, estilo).

El sistema es **transparente** (muestra análisis detallado), **robusto** (aplica restricciones para garantizar validez) y **personalizable** (se adapta a diferentes eventos y preferencias).

