"""Generate the figures for the flash-flood analysis."""
from __future__ import annotations

import json
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

from .config import DATABASE, EXPORTS, FIGURES

NAVY, TEAL, RUST, GREY, CREAM = "#122e3a", "#087f8c", "#c25a36", "#657982", "#f5f2e9"


def money(value):
    return f"${value / 1e9:,.2f}B" if abs(value) >= 1e9 else f"${value / 1e6:,.1f}M" if abs(value) >= 1e6 else f"${value:,.0f}"


def style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": NAVY,
                         "axes.labelcolor": NAVY, "xtick.color": GREY, "ytick.color": GREY,
                         "axes.edgecolor": "#d4dedc", "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "axes.facecolor": "white",
                         "savefig.facecolor": "white", "svg.fonttype": "none", "svg.hashsalt": "floodfolio-2020-2024"})


def save(fig, name):
    fig.savefig(FIGURES / f"{name}.png", dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight", facecolor=fig.get_facecolor(), metadata={"Date": None})
    plt.close(fig)


def make_figures(e, s):
    FIGURES.mkdir(parents=True, exist_ok=True)
    style()
    # A real analytical chart carries the cover, rather than decorative stock art.
    fig = plt.figure(figsize=(15, 6), facecolor=NAVY)
    fig.text(.055, .88, "FLASH FLOOD / IMPACT ANALYSIS", color="#7bd0d2", size=12, weight="bold")
    fig.text(.055, .68, "The tail is the story.", color="white", size=34, weight="bold")
    fig.text(.055, .55, "Five years of U.S. flash-flood records.\nThree linked source tables. One defensible event-level model.", color="#c8d6d8", size=14, linespacing=1.7)
    for x, val, label in [(.055, f"{int(s['recorded_events']):,}", "recorded events"),
                           (.275, money(s['reported_property_damage_usd']), "reported property damage"),
                           (.535, f"{s['top_1pct_loss_share_pct']:.1f}%", "loss in the top 1% of events")]:
        fig.text(x, .27, val, color="white", size=28, weight="bold")
        fig.text(x, .19, label, color="#c8d6d8", size=11)
    fig.text(.055, .065, "2020–2024  |  50 states + D.C.  |  NOAA NCEI / NWS  |  Recorded impacts; nominal USD", color="#a2b7bd", size=10)
    ax = fig.add_axes([.77, .19, .19, .60], facecolor=NAVY)
    ax.bar([0, 1], [1, s["top_1pct_loss_share_pct"]], color=["#7bd0d2", "#e69b69"], width=.6)
    ax.set_xticks([0, 1], ["Events", "Reported\nloss"]); ax.set_ylim(0, 105)
    ax.set_yticks([]); ax.tick_params(axis="x", colors="white", labelsize=11)
    for sp in ax.spines.values(): sp.set_visible(False)
    for x, y in [(0, 1), (1, s["top_1pct_loss_share_pct"])]: ax.text(x, y + 3, f"{y:.1f}%", ha="center", color="white", size=13)
    ax.set_title("Highest-loss 1%", color="white", size=12, pad=15)
    save(fig, "01_cover")

    ranked = e.sort_values(["property_damage_usd", "event_id"], ascending=[False, True])
    x = np.arange(1, len(e) + 1) / len(e) * 100
    y = ranked.property_damage_usd.cumsum().to_numpy() / ranked.property_damage_usd.sum() * 100
    fig, ax = plt.subplots(figsize=(11.5, 5.5))
    ax.plot(np.r_[0, x], np.r_[0, y], color=TEAL, lw=2.8)
    ax.fill_between(np.r_[0, x], np.r_[0, y], color=TEAL, alpha=.08)
    ax.axvline(1, color=RUST, linestyle="--", lw=1.3)
    ax.scatter([s["top_1pct_event_count"] / len(e) * 100], [s["top_1pct_loss_share_pct"]], color=RUST, zorder=5)
    ax.annotate(f"192 events account for {s['top_1pct_loss_share_pct']:.1f}% of reported loss", xy=(1, s["top_1pct_loss_share_pct"]), xytext=(17, 74), arrowprops={"arrowstyle": "-", "color": RUST}, fontsize=12, color=NAVY)
    ax.set(xlim=(0,100), ylim=(0,103), xlabel="Cumulative share of events, highest reported loss first (%)", ylabel="Cumulative share of reported property damage (%)")
    ax.set_title("Removing extreme losses would remove most of the impact", loc="left", fontsize=17, weight="bold", pad=20)
    fig.text(.12, -.01, "All 19,191 recorded events; observed damage entries only. A zero entry does not establish that no loss occurred.", fontsize=9, color=GREY)
    ax.grid(axis="y", alpha=.2); save(fig, "02_loss_concentration")

    overnight = pd.read_csv(EXPORTS / "overnight_start.csv")
    fig, axes = plt.subplots(1,2, figsize=(12,4.9))
    for ax, col, title in [(axes[0], "events", "Recorded events"), (axes[1], "fatal_event_pct", "Events with a reported direct death")]:
        values = overnight[col].to_numpy()
        bars = ax.bar(["Overnight start", "Other start"], values, color=[RUST, TEAL], width=.55)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x()+bar.get_width()/2, value*1.04, f"{value:.2f}%" if col.endswith("pct") else f"{value:,.0f}", ha="center", weight="bold")
        ax.set_ylim(0,max(values)*1.23); ax.set_title(title, loc="left", size=13, pad=14); ax.grid(axis="y",alpha=.14);ax.set_axisbelow(True)
    fig.suptitle("Overnight starts carry a different recorded casualty profile", x=.07, ha="left", size=17, weight="bold")
    fig.text(.07, -.02, "Overnight = 20:00–05:59 in reported local time. Descriptive association; no adjustment for severity, geography, or exposure.", size=9, color=GREY)
    fig.tight_layout(rect=[0,.03,1,.92]); save(fig, "03_overnight_profile")

    monthly = pd.read_csv(EXPORTS / "monthly_trend.csv")
    dt = pd.to_datetime(monthly.month_start)
    fig, axes = plt.subplots(2,1,figsize=(12,6.5),sharex=True)
    axes[0].plot(dt,monthly.events,color=TEAL,lw=2);axes[0].fill_between(dt,monthly.events,color=TEAL,alpha=.08)
    axes[0].set_ylabel("Recorded events")
    axes[1].bar(dt,monthly.property_damage_usd/1e9,width=22,color=RUST);axes[1].set_ylabel("Reported loss ($B)")
    fig.suptitle("Event frequency and reported damage tell different stories", x=.075, ha="left", size=17,weight="bold")
    for ax in axes: ax.grid(axis="y",alpha=.18);ax.set_axisbelow(True)
    fig.text(.075, .005, "60 monthly observations, 2020–2024. Dollar figures are nominal, broad estimates—not insurance claims or inflation-adjusted losses.", size=9,color=GREY)
    fig.tight_layout(rect=[0,.04,1,.94]);save(fig,"04_monthly_impacts")

    quality = e.groupby("year").agg(events=("event_id","size"),with_locations=("valid_location_records",lambda x:x.gt(0).sum()),zero_damage=("property_damage_status",lambda x:x.eq("zero").sum()))
    quality["location_coverage_pct"] = quality.with_locations/quality.events*100
    quality["zero_damage_pct"] = quality.zero_damage/quality.events*100
    quality.to_csv(EXPORTS / "quality_by_year.csv")
    fig, ax = plt.subplots(figsize=(11,5))
    ax.plot(quality.index,quality.location_coverage_pct,marker="o",lw=2.5,color=TEAL,label="At least one valid linked location")
    ax.plot(quality.index,quality.zero_damage_pct,marker="s",lw=2,color=RUST,label="Property damage entered as zero")
    for year,row in quality.iterrows(): ax.annotate(f"{row.location_coverage_pct:.1f}%",(year,row.location_coverage_pct),xytext=(0,9),textcoords="offset points",ha="center",size=10,color=TEAL)
    ax.set_ylim(0,110);ax.set_xticks(quality.index);ax.set_ylabel("Share of recorded events (%)")
    ax.set_title("Reporting coverage belongs beside the impact KPIs",loc="left",size=17,weight="bold",pad=20)
    ax.grid(axis="y",alpha=.18);ax.legend(loc="lower left",frameon=False)
    fig.text(.12,-.015,"Location coverage uses the child locations table. A missing child point does not mean the event lacks a coordinate in the details table.",size=9,color=GREY)
    save(fig,"05_reporting_coverage")

    sensitivity = pd.read_csv(EXPORTS / "outlier_sensitivity.csv")
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    compare=sensitivity.iloc[[0,3]]
    for ax,col,title in [(axes[0],"events","Events retained"),(axes[1],"property_damage_usd","Reported property damage retained")]:
        vals=compare[col].to_numpy();bars=ax.bar(["Full population","Routine comparison"], vals/ (1e9 if col.endswith("usd") else 1),color=[TEAL,RUST],width=.5)
        for bar,v in zip(bars,vals):ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()*1.04,money(v) if col.endswith("usd") else f"{v:,.0f}",ha="center",weight="bold")
        ax.set_title(title,loc="left",size=13,pad=15);ax.set_ylim(0,max(b.get_height() for b in bars)*1.23);ax.grid(axis="y",alpha=.15);ax.set_axisbelow(True)
        if col.endswith("usd"): ax.set_ylabel("Nominal USD, billions")
    fig.suptitle("A routine-event filter excludes 6.1% of events—and 95.2% of reported loss",x=.06,ha="left",size=16,weight="bold")
    fig.text(.06,-.01,"Duration: upper 1.5×IQR fence. Damage: upper 1.5×IQR fence of log(1 + positive loss). Headline KPIs use the full population.",size=9,color=GREY)
    fig.tight_layout(rect=[0,.03,1,.92]);save(fig,"06_outlier_sensitivity")

    heat=e.groupby(["month","begin_hour"]).size().unstack(fill_value=0).reindex(index=range(1,13),columns=range(24),fill_value=0)
    fig,ax=plt.subplots(figsize=(12,5.2));img=ax.imshow(heat.to_numpy(),aspect="auto",cmap="YlGnBu",interpolation="nearest")
    ax.set_xticks(range(0,24,2),range(0,24,2));ax.set_yticks(range(12),["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
    ax.set_xlabel("Event start hour in reported local time");ax.set_title("Recorded demand clusters by season and time of day",loc="left",size=17,weight="bold",pad=20)
    cbar=fig.colorbar(img,ax=ax,pad=.02);cbar.set_label("Recorded events, 2020–2024")
    fig.text(.12,-.01,"Pooled five-year record counts. This describes start-time patterns, not a staffing forecast or the hour of fatality.",size=9,color=GREY)
    save(fig,"07_season_hour")


def main():
    summary=json.loads((EXPORTS/"kpi_summary.json").read_text())
    with sqlite3.connect(DATABASE) as conn:
        events=pd.read_sql("SELECT * FROM vw_event_enriched ORDER BY event_id",conn)
    make_figures(events,summary)


if __name__ == "__main__":
    main()
