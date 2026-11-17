import gempy as gp
import pandas as pd

# =====================================================
# ЧТЕНИЕ ДАННЫХ
# =====================================================

surface_points = pd.read_csv("../surface_points.csv")
orientations = pd.read_csv("../orientations.csv")

print("\nКонтактные точки:")
print(surface_points.head())

print("\nОриентировки:")
print(orientations.head())

# =====================================================
# СОЗДАНИЕ СТРУКТУРЫ
# =====================================================

structural_frame = gp.data.StructuralFrame.initialize_default_structure()

print("\nСтруктурный фрейм создан")

# =====================================================
# СОЗДАНИЕ МОДЕЛИ
# =====================================================

geo_model = gp.create_geomodel(
    project_name="gold_model",
    extent=[900, 1600, 900, 1100, 350, 550],
    resolution=[50, 20, 50],
    structural_frame=structural_frame
)

print("Модель создана")

# =====================================================
# ДОБАВЛЯЕМ КОНТАКТНЫЕ ТОЧКИ
# =====================================================

gp.add_surface_points(
    geo_model,
    x=surface_points["X"].tolist(),
    y=surface_points["Y"].tolist(),
    z=surface_points["Z"].tolist(),
    elements_names=["surface1"] * len(surface_points)
)

print("Контактные точки добавлены")

# =====================================================
# ГОТОВИМ ВЕКТОРЫ ОРИЕНТАЦИЙ
# =====================================================

pole_vectors = [
    [gx, gy, gz]
    for gx, gy, gz in zip(
        orientations["G_x"],
        orientations["G_y"],
        orientations["G_z"]
    )
]

print(f"Количество ориентировок: {len(pole_vectors)}")

# =====================================================
# ДОБАВЛЯЕМ ОРИЕНТАЦИИ
# =====================================================

gp.add_orientations(
    geo_model,
    x=orientations["X"].tolist(),
    y=orientations["Y"].tolist(),
    z=orientations["Z"].tolist(),
    pole_vector=pole_vectors,
    elements_names=["surface1"] * len(orientations)
)

print("Ориентировки добавлены")

# =====================================================
# РАСЧЕТ МОДЕЛИ
# =====================================================

print("Запуск расчета...")

gp.compute_model(geo_model)

print("Модель успешно рассчитана")

# =====================================================
# СОХРАНЕНИЕ
# =====================================================

gp.save_model(
    geo_model,
    path="gold_model"
)

print("Модель сохранена")