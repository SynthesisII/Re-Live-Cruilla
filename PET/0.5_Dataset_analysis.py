"""
📘 Análisis visual del dataset de usuarios musicales (100.000 vectores)

Este script explora un conjunto sintético de usuarios donde cada uno está representado 
por un vector de 18 números entre 0 y 1, indicando cuánto le gusta cada estilo musical.

Objetivos:
1. Visualizar la diversidad de usuarios generados.
2. Comprobar que los distintos perfiles están bien representados.
3. Observar cómo se agrupan los gustos similares y qué tan repartidos están los extremos, mezclados o casos raros.
4. Obtener intuiciones útiles para diseño de modelos de recomendación, clustering o personalización estética.

Se utilizan técnicas de reducción de dimensionalidad (PCA, UMAP) y visualizaciones estadísticas.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import umap

# -----------------------------
# Cargar datos
# -----------------------------
df = pd.read_csv("diverse_users_100k.csv")

# Lista de géneros (columnas de gusto)
GENRES = df.columns[1:19]
X = df[GENRES].values  # Matriz de vectores de usuarios

# -----------------------------
# Inferir tipo de usuario (por si no se guardó en el CSV)
# -----------------------------
# Clasificamos a cada usuario automáticamente según su perfil de gustos.
# Esto nos permite colorearlos más adelante en los gráficos.
# Lo hacemos a partir del número de gustos fuertes (>0.6) y no nulos (>0.05).

def infer_user_type(row):
    num_high = sum(row > 0.6)
    num_nonzero = sum(row > 0.05)
    if num_high == 1 and num_nonzero == 1:
        return 'Extreme'
    elif num_high == 1 and num_nonzero <= 3:
        return 'Semi-extreme'
    elif 2 <= num_high <= 4:
        return 'Combined'
    elif num_nonzero > 10:
        return 'Mixed'
    else:
        return 'Rare'

df['UserType'] = df[GENRES].apply(infer_user_type, axis=1)

# -----------------------------
# Reducción de dimensionalidad con PCA
# -----------------------------
# PCA transforma nuestros 18 gustos en solo 2 ejes que capturan la mayor parte
# de la variación entre usuarios. Nos permite ver si existen grupos naturales,
# si los usuarios extremos se alejan del resto, etc.

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # Escalamos los datos para igualar la influencia de cada género

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

df['PCA1'] = X_pca[:, 0]
df['PCA2'] = X_pca[:, 1]

# -----------------------------
# Visualización: PCA scatter
# -----------------------------
# Cada punto es un usuario. El color indica el tipo de perfil.
# Nos ayuda a ver si los tipos se mezclan, se agrupan, o se dispersan.

plt.figure(figsize=(10, 7))
sns.scatterplot(data=df, x='PCA1', y='PCA2', hue='UserType', alpha=0.5, s=10, palette="Set2")
plt.title("PCA - Distribución de usuarios por tipo")
plt.xlabel("Componente principal 1 (variación dominante)")
plt.ylabel("Componente principal 2 (variación secundaria)")
plt.grid(True)
plt.tight_layout()
plt.savefig("pca_usuarios.png", dpi=300)
plt.show()

# -----------------------------
# Reducción de dimensionalidad con UMAP
# -----------------------------
# UMAP es una técnica más moderna que PCA, y capta relaciones más complejas.
# Mientras PCA busca maximizar la varianza global, UMAP intenta mantener la 
# estructura de vecindad local. Es útil para ver "microgrupos" de usuarios 
# similares o detectar clústeres no lineales.

reducer = umap.UMAP(random_state=42)
X_umap = reducer.fit_transform(X_scaled)
df['UMAP1'] = X_umap[:, 0]
df['UMAP2'] = X_umap[:, 1]

# -----------------------------
# Visualización: UMAP scatter
# -----------------------------
# Cada punto sigue siendo un usuario, pero ahora agrupado según afinidades complejas.
# Ideal para entender la densidad, relaciones y casos "atípicos".

plt.figure(figsize=(10, 7))
sns.scatterplot(data=df, x='UMAP1', y='UMAP2', hue='UserType', alpha=0.5, s=10, palette="Set1")
plt.title("UMAP - Agrupaciones naturales de usuarios")
plt.xlabel("UMAP eje 1")
plt.ylabel("UMAP eje 2")
plt.grid(True)
plt.tight_layout()
plt.savefig("umap_usuarios.png", dpi=300)
plt.show()

# -----------------------------
# Histogramas por género
# -----------------------------
# Cada gráfico muestra cómo se distribuye el gusto por un género en la población.
# Sirve para ver si hay géneros dominantes, poco elegidos, o si hay perfiles muy variados.

plt.figure(figsize=(16, 10))
for i, genre in enumerate(GENRES):
    plt.subplot(5, 4, i+1)
    sns.histplot(df[genre], bins=30, kde=False)
    plt.title(genre)
    plt.xlabel("Afinidad")
    plt.ylabel("Usuarios")
    plt.tight_layout()
plt.suptitle("Distribución de afinidad por género musical", fontsize=16, y=1.02)
plt.savefig("histogramas_generos.png", dpi=300)
plt.show()

# -----------------------------
# Boxplots por tipo de usuario
# -----------------------------
# Este gráfico compara el rango de afinidades por género según el tipo de usuario.
# Nos permite ver, por ejemplo, si los 'Mixed' tienen más afinidad promedio en todo,
# o si los 'Rare' muestran patrones muy extremos.

plt.figure(figsize=(20, 8))
df_melted = df.melt(id_vars=['UserType'], value_vars=GENRES, var_name='Genre', value_name='Affinity')
sns.boxplot(data=df_melted, x='Genre', y='Affinity', hue='UserType')
plt.title("Distribución de afinidades por género y tipo de usuario")
plt.xticks(rotation=45)
plt.xlabel("Género musical")
plt.ylabel("Nivel de afinidad")
plt.legend(title="Tipo de usuario", bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()
plt.savefig("boxplot_por_tipo.png", dpi=300)
plt.show()

# -----------------------------
# ¿Qué interpretaciones puedo sacar?
# -----------------------------
# ¿Hay grupos de usuarios claramente separados? → Mira los clusters en PCA o UMAP.
# ¿Hay géneros dominantes o ignorados? → Revisa los histogramas.
# ¿Varía mucho el gusto entre tipos de usuario? → Observa los boxplots.
# ¿Los extremos realmente son únicos? → Mira su posición y densidad en los scatter plots.