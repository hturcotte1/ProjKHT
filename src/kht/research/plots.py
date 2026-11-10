"""Shared chart styling for the research figures (static PNGs for the docs).

One quiet look for every figure: thin marks, hairline solid grid, text in ink
colours (never in the series colour), blue for "made money" and red for "lost
money" where a chart is about the sign of a number. Colours were checked for
colour-blind separation with the palette validator.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_3 = "#8a8983"
GRID = "#e7e6e1"
BLUE = "#2a78d6"     # gain / primary series
RED = "#e34948"      # loss
ORANGE = "#eb6834"   # second series
NEUTRAL = "#b9b8b2"  # context, benchmarks

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2,
    "axes.titlecolor": INK,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "text.color": INK,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def new_figure(width: float = 8.0, height: float = 4.2):
    fig, ax = plt.subplots(figsize=(width, height), dpi=160)
    style(ax)
    return fig, ax


def style(ax) -> None:
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.yaxis.grid(True, color=GRID, linewidth=1.0, linestyle="-")
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0, labelsize=9)


def _plain(text: str) -> str:
    """Stop matplotlib from reading dollar amounts as maths."""
    return text.replace("$", r"\$")


def title(ax, text: str, subtitle: str | None = None) -> None:
    fig = ax.figure
    fig.text(0.012, 0.975, _plain(text), ha="left", va="top", fontsize=12.5, fontweight="bold", color=INK)
    if subtitle:
        fig.text(0.012, 0.915, _plain(subtitle), ha="left", va="top", fontsize=9.5, color=INK_2)


def rounded_bar(ax, x: float, height: float, width: float, color: str, radius_pts: float = 3.0) -> None:
    """A bar from zero to ``height`` with a rounded data end and a square base."""
    if height == 0:
        return
    fig = ax.figure
    # convert the corner radius from points to data units on each axis
    inv = ax.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform([(0, 0), (radius_pts * fig.dpi / 72, radius_pts * fig.dpi / 72)])
    rx, ry = abs(x1 - x0), abs(y1 - y0)
    rx = min(rx, width / 2)
    ry = min(ry, abs(height))
    left, right = x - width / 2, x + width / 2
    s = 1 if height > 0 else -1
    tip = height
    verts = [(left, 0), (left, tip - s * ry), (left, tip), (left + rx, tip), (right - rx, tip), (right, tip),
             (right, tip - s * ry), (right, 0), (left, 0)]
    codes = [MPath.MOVETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CURVE3,
             MPath.CURVE3, MPath.LINETO, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color, edgecolor="none", zorder=3))


def signed_bars(ax, labels: list[str], values: list[float], width: float = 0.42,
                pos: str = BLUE, neg: str = RED, value_fmt: str = "{:+.1f}") -> None:
    """Bars coloured by sign, with the value written at each tip in ink."""
    xs = list(range(len(labels)))
    lo, hi = min(values + [0.0]), max(values + [0.0])
    span = (hi - lo) or 1.0
    ax.set_xlim(-0.6, len(labels) - 0.4)
    ax.set_ylim(lo - 0.14 * span, hi + 0.14 * span)
    ax.axhline(0, color=INK_3, linewidth=1.0, zorder=2)
    for x, v in zip(xs, values):
        rounded_bar(ax, x, v, width, pos if v >= 0 else neg)
        ax.text(x, v + (0.025 * span if v >= 0 else -0.025 * span), value_fmt.format(v).replace("-", "\u2212"),
                ha="center", va="bottom" if v >= 0 else "top", fontsize=8.5, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)


def save(fig, path: str | Path, top: float = 0.83) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.subplots_adjust(top=top, left=0.085, right=0.985, bottom=0.14)
    fig.savefig(path)
    plt.close(fig)
    return path


def percent_axis(ax, step: float | None = None) -> None:
    """Percent tick labels with a real minus sign, on round steps."""
    from matplotlib.ticker import FuncFormatter, MultipleLocator

    if step:
        ax.yaxis.set_major_locator(MultipleLocator(step))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%".replace("-", "\u2212")))
