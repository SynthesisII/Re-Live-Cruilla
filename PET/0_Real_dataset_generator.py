"""
Script para generar un conjunto sintético de usuarios con la máxima diversidad de gustos musicales posible.

Cada usuario está representado por un vector de 18 dimensiones (una por género/estilo musical), 
con valores entre 0 y 1 que indican la afinidad hacia ese estilo. 
El objetivo es cubrir todos los perfiles de usuario posibles: desde los que tienen un único gusto dominante 
hasta aquellos con combinaciones caóticas o repartidas.

Se generan 100.000 usuarios divididos en 5 tipos distintos:

1. Extremos puros (2%): un solo estilo al 100%, el resto a 0.
2. Semi-extremos (13%): un estilo dominante al 100%, y algunos secundarios bajos (0.1-0.3).
3. Combinados medios (25%): 2-4 estilos dominantes con valores entre 0.3 y 0.8.
4. Mezclados suaves (50%): afinidad repartida entre muchos estilos, valores entre 0.1 y 0.9.
5. Raros o caóticos (10%): combinaciones inusuales de 5 estilos con valores entre 0.2 y 1.0.

Los vectores no están normalizados ni tienen que sumar 1, para reflejar mejor la naturaleza libre 
de los perfiles de usuario reales.

El resultado se guarda en un archivo CSV llamado 'diverse_users_100k.csv'.

"""

import numpy as np
import pandas as pd
from typing import List

# --- Configuración global ---

NUM_USERS = 100_000
GENRES = [
    'Comedy', 'Art', 'Chill', 'Food', 'Social', 'Rock', 'Pop',
    'Soul', 'Jazz', 'Electronic', 'Folk', 'Reggae', 'Hip-hop',
    'Punk', 'Rap', 'Classical', 'Indie', 'Other'
]

# Porcentajes por tipo de usuario (suma 100%)
PROFILE_DISTRIBUTION = {
    'extreme': 0.02,
    'semi_extreme': 0.13,
    'combined': 0.25,
    'mixed': 0.50,
    'rare': 0.10
}

np.random.seed(42)  # Reproducibilidad


# --- Funciones generadoras de cada tipo de usuario ---

def generate_extreme_user() -> List[float]:
    """Usuario con solo un estilo al 100%."""
    vec = np.zeros(len(GENRES))
    vec[np.random.randint(0, len(GENRES))] = 1.0
    return vec.tolist()


def generate_semi_extreme_user() -> List[float]:
    """Usuario con un estilo dominante y algunos secundarios bajos."""
    vec = np.random.uniform(0, 0.3, len(GENRES))
    main_genre = np.random.randint(0, len(GENRES))
    vec[main_genre] = 1.0
    return vec.tolist()


def generate_combined_user() -> List[float]:
    """Usuario con 2–4 estilos dominantes."""
    vec = np.zeros(len(GENRES))
    indices = np.random.choice(len(GENRES), size=np.random.randint(2, 5), replace=False)
    values = np.random.uniform(0.3, 0.8, len(indices))
    vec[indices] = values
    return vec.tolist()


def generate_mixed_user() -> List[float]:
    """Usuario con afinidades repartidas en muchos estilos."""
    vec = np.random.uniform(0.1, 0.9, len(GENRES))
    return vec.tolist()


def generate_rare_user() -> List[float]:
    """Usuario con combinaciones caóticas e inesperadas."""
    vec = np.zeros(len(GENRES))
    indices = np.random.choice(len(GENRES), size=5, replace=False)
    values = np.random.uniform(0.2, 1.0, len(indices))
    vec[indices] = values
    return vec.tolist()


# --- Función principal para generar todos los usuarios ---

def generate_all_users(num_users: int) -> pd.DataFrame:
    """Genera el conjunto completo de usuarios según las proporciones y los tipos definidos."""
    users = []
    generators = {
        'extreme': generate_extreme_user,
        'semi_extreme': generate_semi_extreme_user,
        'combined': generate_combined_user,
        'mixed': generate_mixed_user,
        'rare': generate_rare_user
    }

    for profile_type, fraction in PROFILE_DISTRIBUTION.items():
        count = int(num_users * fraction)
        print(f"Generating {count} '{profile_type}' users...")
        for _ in range(count):
            users.append(generators[profile_type]())

    df = pd.DataFrame(users, columns=GENRES)
    df.insert(0, 'UserID', [f"user_{i+1}" for i in range(len(users))])
    return df


# --- Ejecutar y guardar el resultado ---

if __name__ == "__main__":
    df_users = generate_all_users(NUM_USERS)
    df_users.to_csv("Diverse_users_100k.csv", index=False)
    print("✅ Archivo 'diverse_users_100k.csv' generado con éxito.")
