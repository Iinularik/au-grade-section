import pandas as pd
import numpy as np
import pyvista as pv

# -----------------------------------------
# Исходные данные
# -----------------------------------------

ore = pd.read_csv("ore_intervals.csv")

collars = {
    "C130": (1000, 1000),
    "C131": (1050, 1000),
    "C132": (1100, 1000),
    "C133": (1150, 1000),
    "C134": (1200, 1000),
    "C135": (1250, 1000),
    "C136": (1300, 1000),
    "C137": (1350, 1000),
    "C138": (1400, 1000),
    "C139": (1450, 1000),
}

# -----------------------------------------
# Верх и низ руды по каждой скважине
# -----------------------------------------

tops = []
bottoms = []

for bhid, group in ore.groupby("BHID"):

    if bhid not in collars:
        continue

    x, y = collars[bhid]

    top_depth = group["FROM"].min()
    bottom_depth = group["TO"].max()

    tops.append([
        x,
        y,
        500 - top_depth
    ])

    bottoms.append([
        x,
        y,
        500 - bottom_depth
    ])

tops.sort(key=lambda p: p[0])
bottoms.sort(key=lambda p: p[0])

# -----------------------------------------
# Рудные интервалы
# -----------------------------------------

plotter = pv.Plotter()

for _, row in ore.iterrows():

    bhid = row["BHID"]

    if bhid not in collars:
        continue

    x, y = collars[bhid]

    z1 = 500 - row["FROM"]
    z2 = 500 - row["TO"]

    line = pv.Line(
        (x, y, z1),
        (x, y, z2)
    )

    tube = line.tube(radius=2.5)

    plotter.add_mesh(
        tube,
        color="gold"
    )

# -----------------------------------------
# Полигональное тело
# -----------------------------------------

points = []
faces = []

for i in range(len(tops) - 1):

    p1 = np.array(tops[i])
    p2 = np.array(tops[i + 1])

    p3 = np.array(bottoms[i + 1])
    p4 = np.array(bottoms[i])

    start = len(points)

    points.extend([
        p1,
        p2,
        p3,
        p4
    ])

    faces.extend([
        4,
        start,
        start + 1,
        start + 2,
        start + 3
    ])

points = np.array(points)

ore_shell = pv.PolyData(points, faces)

plotter.add_mesh(
    ore_shell,
    color="orange",
    opacity=0.5,
    show_edges=True
)

# -----------------------------------------
# Контуры
# -----------------------------------------

for i in range(len(tops) - 1):

    plotter.add_mesh(
        pv.Line(tops[i], tops[i + 1]).tube(radius=1),
        color="red"
    )

    plotter.add_mesh(
        pv.Line(bottoms[i], bottoms[i + 1]).tube(radius=1),
        color="blue"
    )

for t, b in zip(tops, bottoms):

    plotter.add_mesh(
        pv.Line(t, b).tube(radius=1),
        color="green"
    )

plotter.add_axes()
plotter.show_grid()

plotter.show()