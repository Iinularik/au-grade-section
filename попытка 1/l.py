import pandas as pd
import numpy as np
import pyvista as pv

# ============================================================
# 1. ЗАГРУЗКА ДАННЫХ
# ============================================================
csv_data = """BHID,FROM,TO,THICKNESS,AVG_AU,GRAM_METERS
C130,44,49,5,1.89,9.45
C131,25,43,18,2.074,37.34
C131,59,64,5,1.566,7.83
C131,86,102,16,1.606,25.69
C131,106,112,6,3.043,18.26
C132,11,33,22,1.841,40.5
C132,38,44,6,1.37,8.22
C132,50,63,13,1.132,14.71
C132,68,82,14,1.476,20.67
C132,86,97,11,1.885,20.73
C132,102,104,2,2.885,5.77
C132,109,119,10,1.243,12.43
C133,0,7,7,2.273,15.91
C133,12,52,40,2.773,110.91
C133,56,83,27,2.258,60.96
C133,87,103,16,1.446,23.14
C134,8,21,13,2.845,36.98
C134,27,77,50,2.746,137.28
C134,82,86,4,10.098,40.39
C134,91,117,26,1.311,34.08
C135,0,34,34,4.618,157.02
C135,41,51,10,1.425,14.25
C135,55,88,33,1.425,47.04
C135,92,110,18,1.077,19.39
C135,114,120,6,5.622,33.73
C136,0,25,25,2.322,58.06
C136,43,52,9,1.523,13.71
C136,60,62,2,1.85,3.7
C136,73,74,1,31.5,31.5
C136,86,107,21,4.945,103.85
C136,111,118,7,2.421,16.95
C137,2,11,9,1.607,14.46
C137,20,69,49,3.09,151.4
C137,73,78,5,1.126,5.63
C137,86,103,17,2.821,47.95
C137,107,111,4,1.318,5.27
C138,2,3,1,3.4,3.4
C138,8,10,2,2.015,4.03
C138,66,68,2,3.33,6.66
C138,87,100,13,1.651,21.46
C139,36,39,3,1.297,3.89"""

from io import StringIO
ore = pd.read_csv(StringIO(csv_data))

collars = {
    "C130": (1000, 1000), "C131": (1050, 1000), "C132": (1100, 1000),
    "C133": (1150, 1000), "C134": (1200, 1000), "C135": (1250, 1000),
    "C136": (1300, 1000), "C137": (1350, 1000), "C138": (1400, 1000),
    "C139": (1450, 1000),
}

ore["X"] = ore["BHID"].map(lambda b: collars[b][0])
ore["Y"] = ore["BHID"].map(lambda b: collars[b][1])
ore["Z_TOP"] = 500 - ore["FROM"]
ore["Z_BOT"] = 500 - ore["TO"]

# ============================================================
# 2. ГРУППИРОВКА В ЛИНЗЫ
# ============================================================
n = len(ore)
parent = list(range(n))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb: parent[rb] = ra

for i in range(n):
    for j in range(i + 1, n):
        if ore.iloc[i]["BHID"] == ore.iloc[j]["BHID"]:
            continue
        if abs(ore.iloc[i]["X"] - ore.iloc[j]["X"]) > 70:
            continue
        # Увеличили допуск до 15 метров, чтобы линзы лучше связывались
        z1 = sorted([ore.iloc[i]["Z_TOP"], ore.iloc[i]["Z_BOT"]])
        z2 = sorted([ore.iloc[j]["Z_TOP"], ore.iloc[j]["Z_BOT"]])
        if z1[1] + 15 < z2[0] or z2[1] + 15 < z1[0]:
            continue
        union(i, j)

labels = np.array([find(i) for i in range(n)])
uniq = {old: new for new, old in enumerate(sorted(set(labels)))}
ore["LENS"] = [uniq[l] for l in labels]

print(f"Всего интервалов: {len(ore)}")
print(f"Найдено линз: {ore['LENS'].nunique()}")

# ============================================================
# 3. ВИЗУАЛИЗАЦИЯ (VOXEL МЕТОД - БЕЗ ОШИБОК ИНТЕРПОЛЯЦИИ)
# ============================================================
plotter = pv.Plotter()
colors = ["red", "green", "blue", "orange", "purple", "cyan", "magenta", "yellow", "brown", "pink", "teal", "olive"]

# 3.1. Стволы скважин
for bhid, (x, y) in collars.items():
    plotter.add_mesh(pv.Line((x, y, 500), (x, y, 380)).tube(radius=1), color="black")

# 3.2. Создание 3D-сетки (Воксели)
# Задаем границы сетки вокруг всех скважин
step = 2.5 # Шаг сетки (2.5 метра)
x_vals = np.arange(990, 1460, step)
y_vals = np.arange(980, 1020, step) # Делаем толщину по Y, так как скважины на одной линии
z_vals = np.arange(370, 510, step)

X, Y, Z = np.meshgrid(x_vals, y_vals, z_vals, indexing='ij')
grid_mask = np.zeros_like(X, dtype=bool)

# Раскрашиваем сетку: если точка попадает в рудный интервал - ставим True
for _, row in ore.iterrows():
    # Находим индексы ячеек сетки, которые попадают в интервал
    mask = (X >= row["X"] - 15) & (X <= row["X"] + 15) & \
           (Y >= row["Y"] - 15) & (Y <= row["Y"] + 15) & \
           (Z >= row["Z_BOT"]) & (Z <= row["Z_TOP"])
    grid_mask[mask] = True

# Создаем 3D-структуру
grid = pv.StructuredGrid(X, Y, Z)
grid["ore"] = grid_mask.flatten(order='F')

# Строим гладкую поверхность по нашим "кубикам"
print("Строим 3D поверхность...")
surface = grid.contour([0.5], scalars="ore")

if surface.n_points > 0:
    plotter.add_mesh(surface, color="red", opacity=0.5, smooth_shading=True, show_edges=False)
else:
    print("Внимание: поверхность не построилась.")

# 3.3. Отрисовка рудных интервалов (трубки)
for _, row in ore.iterrows():
    plotter.add_mesh(pv.Line((row["X"], row["Y"], row["Z_TOP"]),
                             (row["X"], row["Y"], row["Z_BOT"])).tube(radius=3),
                     color=colors[row["LENS"] % len(colors)])

# 3.4. Настройка камеры, чтобы точно попасть в центр
plotter.camera_position = [(1225, 1000, 450),  # позиция камеры
                           (1225, 1000, 440),  # точка, куда смотрим
                           (0, 0, 1)]          # вектор "вверх"
plotter.add_axes()
plotter.show_grid()
plotter.show()
