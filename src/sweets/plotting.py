from pathlib import Path
from typing import Optional, Tuple

import ipywidgets
import matplotlib.pyplot as plt
import numpy as np
from dolphin import io
from matplotlib.colors import LinearSegmentedColormap
from numpy.typing import ArrayLike

from ._types import Filename


def _make_dismph_colors():
    """Create a cyclic colormap for insar phase."""
    red, green, blue = [], [], []
    for i in range(120):
        red.append(i * 2.13 * 155.0 / 255.0 + 100)
        green.append((119.0 - i) * 2.13 * 155.0 / 255.0 + 100.0)
        blue.append(255)
    for i in range(120):
        red.append(255)
        green.append(i * 2.13 * 155.0 / 255.0 + 100.0)
        blue.append((119 - i) * 2.13 * 155.0 / 255.0 + 100.0)
    for i in range(120):
        red.append((119 - i) * 2.13 * 155.0 / 255.0 + 100.0)
        green.append(255)
        blue.append(i * 2.13 * 155.0 / 255.0 + 100.0)
    return np.vstack((red, green, blue))


try:
    plt.get_cmap("dismph")
except:
    DISMPH = LinearSegmentedColormap.from_list("dismph", _make_dismph_colors().T / 256)
    plt.register_cmap(cmap=DISMPH)


def plot_ifg(
    img: Optional[ArrayLike] = None,
    filename: Optional[Filename] = None,
    phase_cmap: str = "dismph",
    ax: Optional[plt.Axes] = None,
    add_colorbar: bool = True,
    title: str = "",
    figsize: Optional[Tuple[float, float]] = None,
    plot_cor: bool = False,
    **kwargs,
):
    """Plot an interferogram.

    Parameters
    ----------
    img : np.ndarray
        Complex interferogram array.
    filename : str
        Filename of interferogram to load.
    phase_cmap : str
        Colormap to use for phase.
    ax : matplotlib.axes.Axes
        Axes to plot on.
    add_colorbar : bool
        If true, add a colorbar to the plot.
    title : str
        Title for the plot.
    figsize : tuple
        Figure size.
    plot_cor : bool
        If true, plot the correlation image as well.

    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure of the plot.
    ax : matplotlib.axes.Axes
        Axes of the plot containing the interferogram.
    """
    if img is None:
        # check for accidentally passing a filename as positional
        if isinstance(img, (Path, str)):
            img = io.load_gdal(img)
        else:
            img = io.load_gdal(filename)
    phase = np.angle(img) if np.iscomplexobj(img) else img
    if plot_cor:
        cor = np.abs(img)

    if ax is None:
        if plot_cor:
            fig, (ax, cor_ax) = plt.subplots(ncols=2, figsize=figsize)
        else:
            fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Note: other interpolations (besides nearest/None) make dismph/cyclic maps look weird
    axim = ax.imshow(
        phase, cmap=phase_cmap, interpolation="nearest", vmax=3.14, vmin=-3.14
    )
    if add_colorbar:
        fig.colorbar(axim, ax=ax)
    if plot_cor:
        axim = cor_ax.imshow(cor, cmap="plasma", vmax=1, vmin=0)
        fig.colorbar(axim, ax=cor_ax)
    if title:
        ax.set_title(title)
    return fig, ax


def browse_ifgs(sweets_path: Filename):
    """Browse interferograms in a sweets directory.

    Creates an interactive plot with a slider to browse stitched interferograms.

    Parameters
    ----------
    sweets_path : str
        Path to sweets directory.
    """
    ifg_path = Path(sweets_path) / "interferograms/stitched"
    file_list = sorted(ifg_path.glob("2*.int"))

    imgs = np.stack([io.load_gdal(f) for f in file_list])
    phases = np.angle(imgs)
    cors = np.abs(imgs)
    dates = [f.stem for f in file_list]

    fig, axes = plt.subplots(ncols=2, figsize=(7, 4))

    # plot once with colorbar
    plot_ifg(img=phases[0], add_colorbar=True, ax=axes[0])
    axim_ifg = axes[0].images[0]

    axim_cor = axes[1].imshow(cors[0], cmap="plasma", vmax=1, vmin=0)
    fig.colorbar(axim_cor, ax=axes[1])

    @ipywidgets.interact(idx=(0, len(file_list) - 1))
    def browse_plot(idx=0):
        axim_ifg.set_data(phases[idx])
        axim_cor.set_data(cors[idx])
        fig.suptitle(dates[idx])
