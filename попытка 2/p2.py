import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from matplotlib.widgets import TextBox
# -----------------------------------
# Бортовое содержание
# -----------------------------------

cutoff = 1

# -----------------------------------
# Загрузка данных
# -----------------------------------

df = pd.read_excel("assays.xlsx")

depths = df.iloc[:, 0].values
holes = df.columns[1:]

spacing = 50

# -----------------------------------
# Формирование координат
# -----------------------------------

X = []
Z = []
AU = []

for i, hole in enumerate(holes):

    x = i * spacing

    for depth, au in zip(depths, df[hole]):

        try:
            au = float(str(au).replace(",", "."))
        except:
            continue

        X.append(x)
        Z.append(-depth)
        AU.append(au)

X = np.array(X)
Z = np.array(Z)
AU = np.array(AU)

# -----------------------------------
# Интерполяция
# -----------------------------------

xi = np.linspace(X.min(), X.max(), 500)
zi = np.linspace(Z.min(), Z.max(), 500)

XI, ZI = np.meshgrid(xi, zi)

AI = griddata(
    (X, Z),
    AU,
    (XI, ZI),
    method="cubic"
)

# -----------------------------------
# График
# -----------------------------------

fig, ax = plt.subplots(
    figsize=(8, 4),
    dpi=120
)
plt.subplots_adjust(bottom=0.22)

ax_box = plt.axes([0.35, 0.03, 0.15, 0.05])

text_box = TextBox(
    ax_box,
    'Борт:',
    initial=str(cutoff)
)
levels = np.linspace(
    np.nanmin(AI),
    np.nanpercentile(AI, 98),
    40
)
ore_fill = []
ore_black = []
ore_white = []

cf = ax.contourf(
    XI,
    ZI,
    AI,
    levels=levels,
    cmap="turbo"
)

# -----------------------------------
# Тёмная заливка рудного тела
# -----------------------------------

ax.contourf(
    XI,
    ZI,
    AI,
    levels=[cutoff, np.nanmax(AI)],
    colors=["darkred"],
    alpha=0.55
)

# -----------------------------------
# Толстый чёрный контур
# -----------------------------------

ax.contour(
    XI,
    ZI,
    AI,
    levels=[cutoff],
    colors="black",
    linewidths=3
)

# -----------------------------------
# Белая обводка поверх
# -----------------------------------

ax.contour(
    XI,
    ZI,
    AI,
    levels=[cutoff],
    colors="white",
    linewidths=1.2
)

# -----------------------------------
# Скважины
# -----------------------------------

for i, hole in enumerate(holes):

    x = i * spacing

    ax.plot(
        [x, x],
        [-100, 0],
        color="black",
        linewidth=0.8
    )

    ax.text(
        x,
        0.5,
        hole,
        ha="center",
        va="bottom",
        fontsize=4
    )
ore_fill.append(
    ax.contourf(
        XI,
        ZI,
        AI,
        levels=[cutoff, np.nanmax(AI)],
        colors=["darkred"],
        alpha=0.55
    )
)

ore_black.append(
    ax.contour(
        XI,
        ZI,
        AI,
        levels=[cutoff],
        colors="black",
        linewidths=3
    )
)

ore_white.append(
    ax.contour(
        XI,
        ZI,
        AI,
        levels=[cutoff],
        colors="white",
        linewidths=1.2
    )
)
# -----------------------------------
# Цветовая шкала
# -----------------------------------

cbar = plt.colorbar(cf)

cbar.set_label(
    "Au",
    fontsize=6
)

cbar.ax.tick_params(
    labelsize=5
)

# -----------------------------------
# Подписи
# -----------------------------------

ax.set_xlabel(
    "Профиль (м)",
    fontsize=6
)

ax.set_ylabel(
    "Глубина (м)",
    fontsize=6
)

ax.set_title(
    f"Au (борт = {cutoff} г/т)",
    fontsize=7
)

ax.tick_params(
    axis="both",
    labelsize=5
)

# -----------------------------------
# Глубина
# -----------------------------------

ax.set_ylim(-90, 0)

# -----------------------------------
# Сетка
# -----------------------------------

ax.grid(
    linestyle="--",
    alpha=0.15
)

# -----------------------------------
# Поля
# -----------------------------------

fig.subplots_adjust(
    left=0.08,
    right=0.95,
    bottom=0.12,
    top=0.90
)
def update_cutoff(text):

    try:
        value = float(text)
    except:
        return

    ax.clear()

    # основная карта
    ax.contourf(
        XI,
        ZI,
        AI,
        levels=levels,
        cmap="turbo"
    )

    # рудное тело
    ax.contourf(
        XI,
        ZI,
        AI,
        levels=[value, np.nanmax(AI)],
        colors=["darkred"],
        alpha=0.55
    )

    ax.contour(
        XI,
        ZI,
        AI,
        levels=[value],
        colors="black",
        linewidths=3
    )

    ax.contour(
        XI,
        ZI,
        AI,
        levels=[value],
        colors="white",
        linewidths=1.2
    )

    # скважины
    for i, hole in enumerate(holes):

        x = i * spacing

        ax.plot(
            [x, x],
            [-100, 0],
            color="black",
            linewidth=0.8
        )

        ax.text(
            x,
            0.5,
            hole,
            ha="center",
            fontsize=4
        )

    ax.set_ylim(-90, 0)

    ax.set_title(
        f"Au (борт = {value:.2f} г/т)",
        fontsize=7
    )

    fig.canvas.draw_idle()

text_box.on_submit(update_cutoff)
plt.show()