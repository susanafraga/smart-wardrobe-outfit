# Explicación del Modelo de Clustering de Estilos

## Resumen Ejecutivo

El sistema utiliza **K-Means clustering** (agrupación no supervisada) para agrupar automáticamente las prendas del catálogo en **4 clusters de estilo** basándose en características de diseño, formalidad, temporada y color.

---

## 1. Tipo de Clustering

### **K-Means Clustering**
- **Algoritmo**: K-Means (implementado con scikit-learn)
- **Tipo**: Clustering no supervisado (unsupervised learning)
- **Objetivo**: Agrupar prendas similares en clusters basándose en características de estilo
- **Número de clusters**: 4 (configurable mediante parámetro `--n_clusters`)

### ¿Por qué K-Means?
- **Eficiente** con grandes volúmenes de datos (105,542 prendas)
- **Interpretable**: cada cluster representa un "estilo" distinto
- **Rápido**: se ejecuta en segundos
- **Escalable**: funciona bien con datos categóricos y numéricos mezclados

---

## 2. Variables Utilizadas (Features)

El modelo utiliza **7 características** de cada prenda:

### Variables Categóricas (5):
1. **`slot`**: Tipo de prenda (top, bottom, dress, shoes, etc.)
2. **`formalidad`**: Nivel de formalidad (casual, intermedio, formal)
3. **`temporada`**: Temporada de uso (invierno, verano, neutra)
4. **`color_base`**: Color principal de la prenda
5. **`fabric_type`**: Tipo de tejido/material

### Variables Numéricas (2):
6. **`nivel_abrigo`**: Nivel de abrigo (1=ligero, 2=medio, 3=abrigado)
7. **`desc_length`**: Longitud de la descripción (proxy de detalle/complejidad)

---

## 3. Preprocesamiento de Datos

### Pipeline de Transformación:

```
Datos Originales → Preprocesamiento → K-Means → Clusters
```

### Paso 1: Manejo de Valores Faltantes (NaN)
- **Numéricas**: 
  - `nivel_abrigo`: se rellena con 2 (medio)
  - `desc_length`: se rellena con la mediana
- **Categóricas**: se rellenan con valores por defecto:
  - `slot` → "other"
  - `formalidad` → "intermedio"
  - `temporada` → "neutra"
  - `color_base` → "other"
  - `fabric_type` → "unknown"

### Paso 2: Transformación de Variables
Se utiliza un **ColumnTransformer** de scikit-learn:

- **Variables numéricas** (`nivel_abrigo`, `desc_length`):
  - **StandardScaler**: Normalización (media=0, desviación=1)
  - **Razón**: K-Means es sensible a la escala de las variables

- **Variables categóricas** (`slot`, `formalidad`, `temporada`, `color_base`, `fabric_type`):
  - **OneHotEncoder**: Codificación one-hot (cada categoría se convierte en una columna binaria)
  - **Ejemplo**: `formalidad` con valores ["casual", "intermedio", "formal"] se convierte en 3 columnas binarias
  - **Razón**: K-Means requiere datos numéricos

---

## 4. Algoritmo K-Means

### Parámetros Configurados:
- **`n_clusters=4`**: 4 grupos de estilo distintos
- **`random_state=42`**: Semilla fija para reproducibilidad
- **`n_init="auto"`**: Inicialización automática (evita warnings en sklearn moderno)

### Proceso:
1. **Inicialización**: Se eligen 4 centroides aleatorios (pero reproducibles)
2. **Asignación**: Cada prenda se asigna al cluster más cercano (distancia euclidiana)
3. **Actualización**: Se recalculan los centroides como la media de las prendas en cada cluster
4. **Iteración**: Se repiten los pasos 2-3 hasta convergencia (centroides estables)

### Resultado:
Cada prenda recibe una etiqueta `style_cluster` con valor 0, 1, 2 o 3.

---

## 5. Interpretación de los Clusters

Cada cluster agrupa prendas con características de estilo similares:

- **Cluster 0, 1, 2, 3**: Cada uno representa un "estilo" distinto
- Las prendas dentro del mismo cluster comparten:
  - Niveles similares de formalidad
  - Temporadas similares
  - Colores y tejidos relacionados
  - Tipos de prenda compatibles

### Ejemplo de Interpretación:
- **Cluster 0**: Podría ser "Estilo casual veraniego" (prendas ligeras, colores claros, casual)
- **Cluster 1**: Podría ser "Estilo formal invernal" (prendas abrigadas, formales, colores oscuros)
- **Cluster 2**: Podría ser "Estilo intermedio neutro" (prendas versátiles, temporada neutra)
- **Cluster 3**: Podría ser otro estilo distintivo

*(La interpretación exacta requiere análisis de los datos de cada cluster)*

---

## 6. Ventajas del Enfoque

✅ **Automatización**: No requiere etiquetado manual de estilos  
✅ **Escalabilidad**: Funciona con catálogos de cualquier tamaño  
✅ **Objetividad**: Basado en características medibles, no en opiniones subjetivas  
✅ **Flexibilidad**: Fácil cambiar el número de clusters o añadir nuevas variables  
✅ **Reproducibilidad**: Resultados consistentes gracias a `random_state=42`

---

## 7. Limitaciones y Consideraciones

⚠️ **Número de clusters fijo**: Requiere decidir cuántos estilos existen (4 en este caso)  
⚠️ **Interpretación manual**: Los clusters no tienen nombres automáticos, hay que analizarlos  
⚠️ **Dependencia de features**: La calidad depende de las variables seleccionadas  
⚠️ **K-Means asume clusters esféricos**: Puede no capturar relaciones complejas

---

## 8. Uso en la Aplicación

El clustering se ejecuta **una vez** para generar `articles_final_clustered.csv`:

```bash
python -m src.build_style_clusters \
    --input data/raw/hm/articles_final.csv \
    --output data/raw/hm/articles_final_clustered.csv \
    --n_clusters 4
```

Luego, la aplicación utiliza esta columna `style_cluster` para:
- Visualizar la distribución de prendas por estilo
- Analizar qué características definen cada estilo
- Mostrar ejemplos representativos de cada cluster

---

## 9. Referencias Técnicas

- **Librería**: scikit-learn (sklearn)
- **Módulos utilizados**:
  - `sklearn.cluster.KMeans`
  - `sklearn.preprocessing.StandardScaler`
  - `sklearn.preprocessing.OneHotEncoder`
  - `sklearn.compose.ColumnTransformer`
  - `sklearn.pipeline.Pipeline`

---

## Preguntas Frecuentes para el Profesor

**P: ¿Por qué 4 clusters?**  
R: Es un balance entre granularidad (más clusters = más detalle) y simplicidad (menos clusters = más fácil de interpretar). Se puede ajustar con `--n_clusters`.

**P: ¿Se podría usar otro algoritmo?**  
R: Sí, alternativas incluyen DBSCAN (clusters de forma irregular), Hierarchical Clustering (árbol de clusters), o GMM (Gaussian Mixture Models). K-Means fue elegido por su simplicidad y eficiencia.

**P: ¿Cómo se valida la calidad de los clusters?**  
R: Métricas como Silhouette Score o Inertia (suma de distancias al centroide) pueden evaluar la calidad. También se puede validar visualmente analizando si las prendas de un cluster tienen sentido estilísticamente.

**P: ¿Se actualiza automáticamente?**  
R: No, es un proceso batch. Si se añaden nuevas prendas al catálogo, hay que re-ejecutar el script para re-clusterizar todo el dataset.

