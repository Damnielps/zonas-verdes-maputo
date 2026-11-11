"""Sistema Ardosia - paleta e estilo matplotlib.

Uso:
    from palette import apply_ardosia, ARDOSIA, VIZ_CATEGORICAL, emphasis
    apply_ardosia()
"""

# --- Nucleo ---------------------------------------------------------------
TINTA        = "#1B1F23"
GRAFITE_CL   = "#31383D"
GRAFITE      = "#4A5157"
PEDRA        = "#7B7D78"
FILETE       = "#D8D4CC"
FILETE_CL    = "#E6E2DA"
PAPEL        = "#F4F2ED"
PAPEL_CL     = "#FAF9F6"
# Fundo de figura: cinza claro quase branco, o tom mais claro da paleta. E o fundo
# de TODA figura, grafico e mapa (matplotlib em modo claro, cards do dashboard).
PAPEL_FIG    = "#FAFAF9"

# --- Assinatura -----------------------------------------------------------
ARDOSIA      = "#24404F"
ARDOSIA_MED  = "#3A6076"
ARDOSIA_CL   = "#7E9BAA"
ARDOSIA_NEV  = "#E3E9EC"
TERRACOTA    = "#9C5B41"
TERRACOTA_CL = "#B8795C"
TERRACOTA_NEV= "#F2E2DC"

# --- Apoio ----------------------------------------------------------------
PETROLEO     = "#3D5A4C"
OCRE         = "#A98A3F"
BORDO        = "#6E3B45"

# --- Escuro ---------------------------------------------------------------
FUNDO_ESC    = "#171B1E"
SUPERF_ESC   = "#212A2F"
TEXTO_ESC    = "#EDEAE4"
TEXTO2_ESC   = "#9AA6AC"
FILETE_ESC   = "#3A4348"

# --- Status ---------------------------------------------------------------
STATUS = {
    "conforme": {"solid": "#4A6B57", "bg": "#E4EBE6", "fg": "#33513F"},
    "atencao":  {"solid": "#A98A3F", "bg": "#F2EBD8", "fg": "#6B5518"},
    "critico":  {"solid": "#9A4B3F", "bg": "#F2E2DC", "fg": "#6E3226"},
    "sem_dado": {"solid": "#8A8781", "bg": "#EAE8E2", "fg": "#57564F"},
}

# --- Escalas de visualizacao ----------------------------------------------
VIZ_CATEGORICAL = [ARDOSIA, TERRACOTA, PETROLEO, ARDOSIA_CL, OCRE, BORDO]
VIZ_SEQUENTIAL  = [ARDOSIA_NEV, "#A9BEC9", ARDOSIA_CL, ARDOSIA_MED, ARDOSIA]
VIZ_DIVERGING   = [TERRACOTA, "#C08066", "#E0BCAC", FILETE,
                   "#A7BFB4", "#6C8F80", PETROLEO]
VIZ_MUTED       = "#B4B2A9"

SERIF = ["Source Serif 4", "Iowan Old Style", "Georgia", "DejaVu Serif", "serif"]
SANS  = ["Source Sans 3", "Segoe UI", "DejaVu Sans", "sans-serif"]


def status_color(estado, papel="solid"):
    """Cor de status. papel in {'solid','bg','fg'}."""
    return STATUS[estado][papel]


def emphasis(labels, destaque):
    """Paleta de enfase: uma serie em terracota, o resto em cinza neutro.

    E a solucao correta para 'esta subiu' - nao a paleta categorica.
    """
    return [TERRACOTA if l == destaque else VIZ_MUTED for l in labels]


def apply_ardosia(dark=False, base_size=10):
    """Aplica o estilo Ardosia ao matplotlib e registra os colormaps."""
    import matplotlib as mpl
    from matplotlib.colors import LinearSegmentedColormap
    from cycler import cycler

    for nome, cores in (("ardosia_seq", VIZ_SEQUENTIAL),
                        ("ardosia_div", VIZ_DIVERGING)):
        cmap = LinearSegmentedColormap.from_list(nome, cores)
        try:
            mpl.colormaps.register(cmap, name=nome, force=True)
        except (AttributeError, ValueError):
            pass

    fundo  = FUNDO_ESC if dark else PAPEL_FIG
    superf = SUPERF_ESC if dark else PAPEL_CL
    texto  = TEXTO_ESC if dark else TINTA
    texto2 = TEXTO2_ESC if dark else PEDRA
    linha  = FILETE_ESC if dark else FILETE
    grade  = FILETE_ESC if dark else FILETE_CL

    mpl.rcParams.update({
        "figure.facecolor": fundo,
        "figure.edgecolor": fundo,
        "figure.dpi": 150,
        "savefig.facecolor": fundo,
        "savefig.bbox": "tight",
        "savefig.dpi": 300,

        "axes.facecolor": superf if dark else fundo,
        "axes.edgecolor": linha,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.labelcolor": texto2,
        "axes.labelsize": base_size,
        "axes.labelpad": 8,
        "axes.titlecolor": texto,
        "axes.titlesize": base_size + 4,
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.prop_cycle": cycler(color=VIZ_CATEGORICAL),

        "grid.color": grade,
        "grid.linewidth": 0.7,
        "grid.alpha": 1.0,

        "xtick.color": texto2,
        "ytick.color": texto2,
        "xtick.labelsize": base_size - 1,
        "ytick.labelsize": base_size - 1,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "xtick.major.pad": 6,
        "ytick.major.pad": 6,

        "font.family": "serif",
        "font.serif": SERIF,
        "font.sans-serif": SANS,
        "font.size": base_size,

        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
        "lines.markersize": 5,

        "patch.linewidth": 0,
        "patch.edgecolor": fundo,

        "legend.frameon": False,
        "legend.fontsize": base_size - 1,
        "legend.labelcolor": texto2,

        "text.color": texto,
    })


def titulo(ax, texto_titulo, kicker=None):
    """Titulo em serifa com kicker em versalete terracota acima."""
    if kicker:
        ax.set_title(kicker.upper(), loc="left", pad=26,
                     fontsize=8, color=TERRACOTA, fontweight="semibold",
                     fontfamily=SANS)
        ax.text(0, 1.055, texto_titulo, transform=ax.transAxes,
                fontsize=13, color=TINTA, fontfamily=SERIF, va="bottom")
    else:
        ax.set_title(texto_titulo, loc="left")
    return ax
