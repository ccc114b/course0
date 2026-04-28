"""math4py - A Python library for mathematics."""

from .geometry import Vector, Point
from .geometry._3d import Line3D, Plane3D
from . import statistics as R

from .statistics import (
    dnorm, pnorm, qnorm, rnorm,
    dt, pt, qt, rt,
    dchisq, pchisq, qchisq, rchisq,
    df, pf, qf, rf,
    dbinom, pbinom, qbinom, rbinom,
    dpois, ppois, qpois, rpois,
    mean, median, var, sd, cov, cor, quantile, summary,
    t_test, z_test, chisq_test, anova, conf_interval,
    plot_t_ci, plot_z_ci, plot_chisq_ci, plot_anova_ci, plot_distribution,
)

__all__ = [
    "Vector", "Point", "Line", "Plane",
    "R",
    "dnorm", "pnorm", "qnorm", "rnorm",
    "dt", "pt", "qt", "rt",
    "dchisq", "pchisq", "qchisq", "rchisq",
    "df", "pf", "qf", "rf",
    "dbinom", "pbinom", "qbinom", "rbinom",
    "dpois", "ppois", "qpois", "rpois",
    "mean", "median", "var", "sd", "cov", "cor", "quantile", "summary",
    "t_test", "z_test", "chisq_test", "anova", "conf_interval",
    "plot_t_ci", "plot_z_ci", "plot_chisq_ci", "plot_anova_ci", "plot_distribution",
]
__version__ = "0.1.0"
