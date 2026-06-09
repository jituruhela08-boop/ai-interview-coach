from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


def create_performance_chart(parent):

    fig = Figure(
        figsize=(6,3),
        dpi=100
    )

    fig.patch.set_facecolor("#151A2D")

    ax = fig.add_subplot(111)

    ax.set_facecolor("#151A2D")

    scores = [55, 63, 71, 78, 81, 88]

    ax.plot(
        scores,
        linewidth=3,
        color="#00D4FF"
    )

    ax.fill_between(
        range(len(scores)),
        scores,
        alpha=0.25,
        color="#00D4FF"
    )

    ax.set_title(
        "Interview Performance",
        color="white"
    )

    ax.tick_params(colors="white")

    for spine in ax.spines.values():
        spine.set_color("#2B3657")

    canvas = FigureCanvasTkAgg(
        fig,
        master=parent
    )

    canvas.draw()

    return canvas.get_tk_widget()