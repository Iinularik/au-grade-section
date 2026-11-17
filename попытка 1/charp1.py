import pandas as pd
import numpy as np
import pyvista as pv
from scipy.interpolate import griddata

# ============================================================
# 1. ЗАГРУЗКА И ПАРАМЕТРЫ
# ============================================================
ore = pd.read_csv("../ore_intervals.csv")
ore = ore.rename(columns={"AVG_AU": "GRADE"})

# Сортируем на всякий случай
ore = ore.sort_values(["BHID", "FROM"]).reset_index(drop=True)

BORT_GRADE = 1.0  # Бортовое содержание
MIN_WIDTH = 3.0  # Минимальная мощность

collars = {
    "C130": (1000, 1000), "C131": (1050, 1000), "C132": (1100, 1000),
    "C133": (1150, 1000), "C134": (1200, 1000), "C135": (1250, 1000),
    "C136": (1300, 1000), "C137": (1350, 1000), "C138": (1400, 1000),
    "C139": (1450, 1000),
}

# Фильтрация по заданию
ore = ore[(ore["GRADE"] >= BORT_GRADE) & ((ore["TO"] - ore["FROM"]) >= MIN_WIDTH)].copy()

# Переводим глубину в координаты Z (ось Z смотрит вверх, поэтому 500 - глубина)
ore["Z_TOP"] = 500 - ore["FROM"]
ore["Z_BOT"] = 500 - ore["TO"]
ore["X"] = ore["BHID"].map(lambda b: collars[b][0])
ore["Y"] = ore["BHID"].map(lambda b: collars[b][1])

# ============================================================
# 2. СОЗДАНИЕ 3D-СЕТКИ (ВОКСЕЛЕЙ)
# ============================================================
# Задаем границы нашей модели
min_x, max_x = 950, 1500
min_y, max_y = 950, 1050
min_z, max_z = 500 - ore["TO"].max() - 10, 500 - ore["FROM"].min() + 10

# Разрешение сетки (шаг в метрах). Чем меньше, тем глаже, но дольше считается.
step = 5.0

x_edges = np.arange(min_x, max_x + step, step)
y_edges = np.arange(min_y, max_y + step, step)
z_edges = np.arange(min_z, max_z + step, step)

X, Y, Z = np.meshgrid(x_edges, y_edges, z_edges, indexing='ij')

# ============================================================
# 3. ИНТЕРПОЛЯЦИЯ (ЗАПОЛНЕНИЕ СЕТКИ)
# ============================================================
# Для каждой ячейки сетки вычисляем "вероятность" наличия руды.
# 1.0 = руда, 0.0 = пустая порода.

# Создаем массив, где изначально везде 0 (пусто)
grid_values = np.zeros_like(X)

# Собираем координаты центров рудных интервалов из скважин
points = []
values = []

for _, row in ore.iterrows():
    # Берем центр интервала по Z
    z_mid = (row["Z_TOP"] + row["Z_BOT"]) / 2

    # Добавляем точки "кровли" и "подошвы" как границы руды
    points.append([row["X"], row["Y"], row["Z_TOP"]])
    values.append(1.0)
    points.append([row["X"], row["Y"], row["Z_BOT"]])
    values.append(1.0)

    # Добавляем точку чуть выше и чуть ниже (чтобы интерполятор знал, где кончается руда)
    points.append([row["X"], row["Y"], row["Z_TOP"] + 5])
    values.append(0.0)
    points.append([row["X"], row["Y"], row["Z_BOT"] - 5])
    values.append(0.0)

points = np.array(points)
values = np.array(values)

# Используем линейную интерполяцию по ближайшим соседям
print("Идет интерполяция, подождите...")
grid_interp = griddata(points, values, (X, Y, Z), method='linear', fill_value=0)

# Превращаем "вероятность" в жесткую маску (0 или 1)
ore_mask = grid_interp >= 0.5

# ============================================================
# 4. ВИЗУАЛИЗАЦИЯ
# ============================================================
plotter = pv.Plotter()

# Создаем 3D-структуру из нашей маски
grid = pv.StructuredGrid(X, Y, Z)

# Добавляем данные в сетку (True = есть руда)
grid["ore"] = ore_mask.flatten(order='F')

# Извлекаем из сетки только те блоки, где есть руда (True)
# И строим по ним гладкую поверхность (contour)
print("Построение 3D-поверхности...")
ore_surface = grid.contour([0.5], scalars="ore")

if ore_surface.n_points > 0:
    plotter.add_mesh(ore_surface, color="red", opacity=0.6, smooth_shading=True, show_edges=False)
else:
    print("Внимание: рудных тел не найдено или сетка слишком мелкая.")

# --- Отрисовка скважин для ориентира ---
for bhid, (x, y) in collars.items():
    # Рисуем ствол скважины от 0 до 150 метров
    plotter.add_mesh(pv.Line((x, y, 500), (x, y, 500 - 150)).tube(radius=0.5), color="black")

# --- Отрисовка рудных интервалов (трубок) ---
for _, row in ore.iterrows():
    z1 = 500 - row["FROM"]
    z2 = 500 - row["TO"]
    plotter.add_mesh(pv.Line((row["X"], row["Y"], z1), (row["X"], row["Y"], z2)).tube(radius=2), color="blue")

# Настройка камеры
plotter.camera_position = "xy"
plotter.add_axes()
plotter.show_grid()
plotter.show()