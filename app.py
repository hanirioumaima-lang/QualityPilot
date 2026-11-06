# -*- coding: utf-8 -*-
"""
QualityPilot : suivi, analyse et réduction des non-conformités (NC)
dans l'industrie aéronautique.

Lancer :  streamlit run app.py

Comptes de démonstration (créés au premier lancement dans users.json) :
    admin    /  QualityPilot2026
    oumaima  /  Haniri2026
Les nouveaux comptes se créent depuis l'onglet "Create account" : l'utilisateur est connecté
directement et arrive sur la page Home, sans repasser par Sign in.
"""

import hashlib
import hmac
import json
import re
import secrets

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib.colors import LinearSegmentedColormap

try:
    st.set_page_config(
        page_title="QualityPilot",
        page_icon=str(Path(__file__).parent / "logo.svg"),
        layout="wide",
        initial_sidebar_state="expanded",
    )
except Exception:
    st.set_page_config(page_title="QualityPilot", layout="wide", initial_sidebar_state="expanded")

# =============================================================================
# 1. CONSTANTES : identité visuelle (bordeaux / blanc / texte noir, ombres en relief)
# =============================================================================
BORDEAUX = "#7A1230"
BORDEAUX_FONCE = "#4F0B1F"
BORDEAUX_MOYEN = "#A8405B"
ROSE = "#D9A0B0"
ROSE_CLAIR = "#EFD5DC"
GRIS = "#6B6B6B"

CMAP = LinearSegmentedColormap.from_list("bordeaux", ["#FFFFFF", ROSE_CLAIR, BORDEAUX_MOYEN, BORDEAUX_FONCE])
COULEURS_GRAVITE = {"Mineure": ROSE, "Majeure": BORDEAUX_MOYEN, "Critique": BORDEAUX_FONCE}
ORDRE_GRAVITE = ["Mineure", "Majeure", "Critique"]
PALETTE_PROGRAMMES = [BORDEAUX_FONCE, BORDEAUX, "#B5506B", ROSE, GRIS]
MOIS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

DATA_PATH = Path(__file__).parent / "dataset.csv"

USERS_PATH = Path(__file__).parent / "users.json"
COMPTES_DEMO = {
    "admin": ("admin@qualitypilot.com", "QualityPilot2026"),
    "oumaima": ("oumaima@qualitypilot.com", "Haniri2026"),
}

PAGES = [
    "Home",
    "Dashboard",
    "Tendances",
    "Défauts et Pareto",
    "Causes racines 5M",
    "Détection chez le client",
    "Clôture et récurrence",
    "Données et nettoyage",
    "Rapport",
]

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "text.color": "#000000",
        "axes.labelcolor": "#000000",
        "axes.edgecolor": "#C9B8BE",
        "xtick.color": "#000000",
        "ytick.color": "#000000",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#F0E6E9",
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.titlelocation": "left",
        "legend.frameon": False,
    }
)

# =============================================================================
# 2. STYLE CSS
# =============================================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,700;9..144,800&display=swap');

@keyframes monter { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
@keyframes flotter { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }
@keyframes entrer-nom { from { opacity: 0; transform: translateX(-26px); letter-spacing: 0.18em; } to { opacity: 1; transform: none; letter-spacing: -0.035em; } }
@keyframes brillance { 0% { background-position: 130% 0; } 60%, 100% { background-position: -30% 0; } }
@keyframes tourner { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.stApp {
    font-family: 'Manrope', 'Segoe UI', sans-serif; color: #000000;
    background:
        radial-gradient(1100px 520px at 96% -8%, #F6E3E9 0%, rgba(246,227,233,0) 62%),
        radial-gradient(900px 480px at -8% 108%, #F8ECF0 0%, rgba(248,236,240,0) 60%),
        #FFFFFF;
}
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1400px; }

h1, h2, h3, h4 { color: #000000 !important; font-weight: 800 !important; letter-spacing: -0.01em; }
p, label, li, .stMarkdown { color: #000000; }

/* ---------- Barre latérale ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FCF7F9 0%, #F4E6EB 100%);
    border-right: 1px solid #E9D8DE; box-shadow: 10px 0 34px -14px rgba(122,18,48,0.28);
}
.marque {
    position: relative; overflow: hidden; border-radius: 16px; padding: 18px 18px 16px 18px; margin-bottom: 14px;
    background: radial-gradient(circle at 100% 0%, rgba(255,255,255,0.22), rgba(255,255,255,0) 45%), linear-gradient(135deg, %BF% 0%, %B% 70%, %BM% 130%);
    box-shadow: 0 8px 0 -4px %BM%, 0 16px 0 -8px %R%, 0 24px 30px -12px rgba(79,11,31,0.55);
    margin-bottom: 30px;
}
.marque, .marque * { color: #FFFFFF !important; }
.marque-ligne { display: flex; align-items: center; gap: 12px; }
.marque .nom { font-family: 'Fraunces', Georgia, serif; font-size: 1.35rem; font-weight: 800; letter-spacing: -0.01em; line-height: 1.1; text-shadow: 0 2px 8px rgba(0,0,0,0.3); }
.marque .desc { font-size: 0.78rem; font-weight: 500; opacity: 0.85; margin-top: 3px; }
.marque svg { filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3)); }
.titre-section { font-weight: 800; font-size: 0.95rem; margin: 18px 0 6px 0; padding-bottom: 6px; border-bottom: 2px solid transparent; border-image: linear-gradient(90deg, %B%, %R%, rgba(217,160,176,0)) 1; }
.compteur { font-size: 0.85rem; font-weight: 600; background: #FFFFFF; border: 1px solid #E9D8DE; border-left: 4px solid %B%; border-radius: 10px; padding: 8px 10px; margin: 10px 0; box-shadow: 0 8px 18px -10px rgba(122,18,48,0.4); }

[data-testid="stSidebar"] [role="radiogroup"] label { padding: 7px 10px; border-radius: 10px; transition: all .18s ease; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(122,18,48,0.07); transform: translateX(3px); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: #FFFFFF; box-shadow: 0 8px 18px -8px rgba(122,18,48,0.45), inset 4px 0 0 %B%; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color: %B% !important; font-weight: 800; }

/* ---------- Bandeau de page ---------- */
.banniere {
    position: relative; overflow: hidden; border-radius: 18px; padding: 28px 34px; margin-bottom: 38px;
    background:
        radial-gradient(circle at 94% 10%, rgba(255,255,255,0.20), rgba(255,255,255,0) 36%),
        radial-gradient(circle at 78% 130%, rgba(217,160,176,0.45), rgba(217,160,176,0) 46%),
        repeating-linear-gradient(115deg, rgba(255,255,255,0.045) 0 2px, rgba(255,255,255,0) 2px 14px),
        linear-gradient(115deg, %BF% 0%, %B% 58%, %BM% 130%);
    box-shadow: 0 9px 0 -4px %BM%, 0 18px 0 -8px %R%, 0 30px 46px -14px rgba(79,11,31,0.55);
    animation: monter .55s ease backwards;
}
.banniere, .banniere * { color: #FFFFFF !important; }
.banniere .bl { display: flex; align-items: center; gap: 20px; position: relative; z-index: 1; }
.banniere .t { font-family: 'Fraunces', Georgia, serif; font-size: 1.95rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.15; text-shadow: 0 2px 0 rgba(79,11,31,0.55), 0 10px 26px rgba(0,0,0,0.3); }
.banniere .s { font-size: 0.95rem; font-weight: 500; opacity: 0.9; margin-top: 8px; max-width: 900px; }

/* ---------- Cartes KPI ---------- */
.kpi {
    position: relative; overflow: hidden; height: 100%; border-radius: 16px; padding: 18px 20px;
    background: linear-gradient(180deg, #FFFFFF 0%, #FCF6F8 100%); border: 1px solid #EBDDE2;
    box-shadow: 0 1px 0 #FFFFFF inset, 0 2px 4px rgba(79,11,31,0.05), 0 14px 28px -12px rgba(122,18,48,0.32);
    transition: transform .22s ease, box-shadow .22s ease; animation: monter .5s ease backwards;
}
.kpi::before { content: ""; position: absolute; left: 0; top: 0; right: 0; height: 5px; background: linear-gradient(90deg, %BF%, %B%, %BM%, %R%); }
.kpi::after { content: ""; position: absolute; right: -28px; bottom: -34px; width: 110px; height: 110px; border-radius: 50%; background: radial-gradient(circle, rgba(217,160,176,0.38), rgba(217,160,176,0) 70%); }
.kpi:hover { transform: translateY(-4px); box-shadow: 0 1px 0 #FFFFFF inset, 0 4px 8px rgba(79,11,31,0.06), 0 26px 38px -14px rgba(122,18,48,0.45); }
.kpi .l { font-size: 0.8rem; font-weight: 700; color: #1A1A1A; position: relative; z-index: 1; }
.kpi .v { font-family: 'Fraunces', Georgia, serif; font-size: 1.8rem; font-weight: 800; color: #000000; line-height: 1.15; margin-top: 6px; position: relative; z-index: 1; text-shadow: 3px 3px 0 rgba(217,160,176,0.35); }
.kpi .n { font-size: 0.78rem; font-weight: 700; color: %B%; margin-top: 6px; position: relative; z-index: 1; }

/* ---------- Blocs d'analyse ---------- */
.constat {
    background: linear-gradient(90deg, #FFFFFF, #FDF9FA); border: 1px solid #EBDDE2; border-left: 6px solid %B%; border-radius: 12px; padding: 15px 20px; margin-bottom: 14px;
    box-shadow: 0 12px 24px -14px rgba(122,18,48,0.35); transition: transform .2s ease, box-shadow .2s ease;
}
.constat:hover { transform: translateX(4px); box-shadow: 0 16px 28px -14px rgba(122,18,48,0.45); }
.constat b { color: %B%; }
.reco {
    background: linear-gradient(135deg, #FBF1F4, #F6E6EB); border: 1px solid #F0DCE3; border-radius: 14px; padding: 15px 20px; margin-bottom: 16px;
    box-shadow: 7px 7px 0 -1px %RC%, 0 18px 28px -16px rgba(122,18,48,0.4);
}
.reco .rt { font-weight: 800; color: %B%; margin-bottom: 4px; }
.sous-titre { font-family: 'Fraunces', Georgia, serif; font-size: 1.25rem; font-weight: 800; margin: 30px 0 10px 0; display: flex; align-items: center; gap: 12px; }
.sous-titre::after { content: ""; flex: 1; height: 3px; border-radius: 3px; background: linear-gradient(90deg, %R%, rgba(217,160,176,0)); }

/* Graphiques et tableaux posés comme des cartes */
[data-testid="stImage"] img { border-radius: 16px; border: 1px solid #EBDDE2; background: #FFFFFF; box-shadow: 0 2px 4px rgba(79,11,31,0.05), 0 18px 34px -16px rgba(122,18,48,0.38); }
[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; box-shadow: 0 18px 30px -16px rgba(122,18,48,0.35); border: 1px solid #EBDDE2; }

/* ---------- Boutons ---------- */
.stButton > button, [data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
    background: linear-gradient(135deg, %B% 0%, %BF% 100%); color: #FFFFFF; border: none; border-radius: 12px; font-weight: 700; width: 100%; padding: 0.55rem 1rem;
    box-shadow: 0 4px 0 %BF%, 0 12px 20px -8px rgba(79,11,31,0.55); transition: transform .15s ease, box-shadow .15s ease;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover, .stDownloadButton > button:hover {
    background: linear-gradient(135deg, %BM% 0%, %B% 100%); color: #FFFFFF; transform: translateY(-2px); box-shadow: 0 6px 0 %BF%, 0 16px 24px -8px rgba(79,11,31,0.6);
}
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(2px); box-shadow: 0 1px 0 %BF%, 0 4px 8px -4px rgba(79,11,31,0.5); }
.stButton > button p, [data-testid="stFormSubmitButton"] > button p, .stDownloadButton > button p { color: #FFFFFF !important; }

/* Onglets */
.stTabs [data-baseweb="tab"] { font-weight: 700; }
.stTabs [aria-selected="true"] { color: %B% !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: %B% !important; }

/* Étiquettes des filtres */
span[data-baseweb="tag"] { background-color: %B% !important; }
span[data-baseweb="tag"], span[data-baseweb="tag"] span { color: #FFFFFF !important; }

/* ---------- Home : hero ---------- */
.hero {
    position: relative; overflow: hidden; border-radius: 26px; padding: 34px 44px 32px 44px; margin-bottom: 40px; min-height: 0;
    background:
        radial-gradient(circle at 88% 12%, rgba(255,255,255,0.22), rgba(255,255,255,0) 34%),
        radial-gradient(circle at 70% 120%, rgba(217,160,176,0.55), rgba(217,160,176,0) 48%),
        repeating-linear-gradient(115deg, rgba(255,255,255,0.05) 0 2px, rgba(255,255,255,0) 2px 16px),
        linear-gradient(120deg, %BF% 0%, %B% 55%, %BM% 135%);
    box-shadow: 0 12px 0 -5px %BM%, 0 24px 0 -10px %R%, 0 38px 0 -16px %RC%, 0 48px 60px -18px rgba(79,11,31,0.6);
    animation: monter .7s ease backwards;
}
.hero, .hero * { color: #FFFFFF !important; }
.hero .anneau { position: absolute; border-radius: 50%; border: 2px dashed rgba(255,255,255,0.28); animation: tourner 60s linear infinite; }
.hero .a1 { width: 440px; height: 440px; right: -120px; top: -150px; }
.hero .a2 { width: 280px; height: 280px; right: -30px; top: -70px; border-style: solid; border-color: rgba(255,255,255,0.14); animation-duration: 90s; animation-direction: reverse; }
.hero .orbe { position: absolute; border-radius: 50%; filter: blur(2px); background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.55), rgba(217,160,176,0.25) 55%, rgba(217,160,176,0) 72%); }
.hero .o1 { width: 110px; height: 110px; right: 80px; bottom: 20px; animation: flotter 7s ease-in-out infinite; }
.hero .o2 { width: 64px; height: 64px; right: 300px; top: 60px; animation: flotter 5s ease-in-out infinite .8s; }
.hero .contenu { position: relative; z-index: 2; max-width: 780px; }
.hero .logo svg { filter: drop-shadow(0 14px 18px rgba(0,0,0,0.38)); animation: flotter 6s ease-in-out infinite; }
.hero .kicker { font-size: 0.74rem; font-weight: 800; letter-spacing: 0.22em; opacity: 0.85; margin: 0 0 14px 0; }
.hero .marque-hero { display: flex; align-items: center; gap: 22px; }
.hero .nom {
    font-family: 'Fraunces', Georgia, serif; font-size: clamp(2.4rem, 5vw, 3.7rem); font-weight: 800; letter-spacing: -0.035em; line-height: 1.05; white-space: nowrap;
    background: linear-gradient(100deg, #FFFFFF 0%, #FFFFFF 38%, #F6C6D3 48%, #FFFFFF 58%, #FFFFFF 100%); background-size: 260% 100%;
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent !important;
    filter: drop-shadow(0 3px 0 rgba(122,18,48,0.9)) drop-shadow(0 6px 0 rgba(79,11,31,0.85)) drop-shadow(0 14px 20px rgba(0,0,0,0.35));
    animation: entrer-nom 1.1s cubic-bezier(.2,.8,.2,1) backwards, brillance 4.5s ease-in-out 1.2s infinite;
}
.hero .slogan { font-size: 1.1rem; font-weight: 700; margin-top: 14px; line-height: 1.35; text-shadow: 0 2px 14px rgba(0,0,0,0.3); }
.hero .texte { font-size: 0.92rem; font-weight: 500; opacity: 0.92; margin-top: 8px; max-width: 620px; line-height: 1.55; }

/* Home : cartes de présentation et parcours */
.feature {
    position: relative; height: 100%; border-radius: 18px; padding: 22px 22px 20px 22px; background: linear-gradient(180deg, #FFFFFF, #FCF6F8); border: 1px solid #EBDDE2;
    box-shadow: 8px 8px 0 -2px %RC%, 0 22px 34px -18px rgba(122,18,48,0.42); transition: transform .22s ease; animation: monter .6s ease backwards;
}
.feature:hover { transform: translate(-3px, -3px); }
.feature .pastille { width: 44px; height: 44px; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; background: linear-gradient(135deg, %BM%, %BF%); box-shadow: 0 10px 16px -6px rgba(79,11,31,0.6); }
.feature .ft { font-family: 'Fraunces', Georgia, serif; font-weight: 800; font-size: 1.2rem; margin-bottom: 6px; }
.feature .fd { font-size: 0.92rem; line-height: 1.5; color: #1A1A1A; }
.etape {
    position: relative; overflow: hidden; border-radius: 16px; padding: 18px 18px 16px 18px; min-height: 178px; margin-bottom: 10px; background: #FFFFFF; border: 1px solid #EBDDE2;
    box-shadow: 0 2px 4px rgba(79,11,31,0.05), 0 18px 28px -16px rgba(122,18,48,0.4); transition: transform .22s ease, box-shadow .22s ease; animation: monter .6s ease backwards;
}
.etape:hover { transform: translateY(-4px); box-shadow: 0 4px 8px rgba(79,11,31,0.06), 0 28px 38px -16px rgba(122,18,48,0.5); }
.etape .num { position: absolute; right: 12px; bottom: -10px; font-family: 'Fraunces', Georgia, serif; font-weight: 800; font-size: 4.4rem; line-height: 1; color: %RC%; text-shadow: 3px 3px 0 rgba(217,160,176,0.45); }
.etape .et { position: relative; font-weight: 800; font-size: 1.02rem; color: %B%; margin-top: 4px; }
.etape .ed { position: relative; font-size: 0.86rem; line-height: 1.45; margin-top: 8px; color: #1A1A1A; }

/* ---------- Connexion ---------- */
.login-gauche {
    position: relative; overflow: hidden; border-radius: 22px; min-height: 520px; padding: 44px 40px; display: flex; flex-direction: column; justify-content: flex-end;
    background:
        radial-gradient(circle at 90% 8%, rgba(255,255,255,0.22), rgba(255,255,255,0) 34%),
        radial-gradient(circle at 60% 118%, rgba(217,160,176,0.5), rgba(217,160,176,0) 50%),
        repeating-linear-gradient(115deg, rgba(255,255,255,0.05) 0 2px, rgba(255,255,255,0) 2px 16px),
        linear-gradient(145deg, %BF% 0%, %B% 60%, %BM% 135%);
    box-shadow: 0 11px 0 -5px %BM%, 0 22px 0 -10px %R%, 0 32px 50px -16px rgba(79,11,31,0.6);
}
.login-gauche, .login-gauche * { color: #FFFFFF !important; }
.login-gauche .anneau { position: absolute; width: 380px; height: 380px; right: -110px; top: -110px; border-radius: 50%; border: 2px dashed rgba(255,255,255,0.28); animation: tourner 60s linear infinite; }
.login-gauche .marque-login { display: flex; align-items: center; gap: 14px; margin-bottom: auto; position: relative; z-index: 1; }
.login-gauche .marque-login svg { filter: drop-shadow(0 8px 12px rgba(0,0,0,0.35)); }
.login-gauche .nom { animation: entrer-nom 1s ease backwards; font-family: 'Fraunces', Georgia, serif; font-weight: 800; font-size: 1.6rem; letter-spacing: -0.01em; text-shadow: 0 2px 0 rgba(79,11,31,0.6), 0 8px 20px rgba(0,0,0,0.3); }
.login-gauche .t { font-family: 'Fraunces', Georgia, serif; font-size: 2.2rem; font-weight: 800; line-height: 1.15; letter-spacing: -0.02em; position: relative; z-index: 1; text-shadow: 0 2px 0 rgba(79,11,31,0.55), 0 12px 28px rgba(0,0,0,0.3); }
.login-gauche .s { font-size: 0.95rem; font-weight: 500; opacity: 0.9; margin-top: 12px; position: relative; z-index: 1; }
[data-testid="stForm"] { border: 1px solid #EBDDE2; border-radius: 18px; padding: 22px 22px 14px 22px; background: linear-gradient(180deg, #FFFFFF, #FCF7F9); box-shadow: 7px 7px 0 -1px %RC%, 0 22px 34px -18px rgba(122,18,48,0.4); }
</style>
"""
for _nom, _val in {"%BF%": BORDEAUX_FONCE, "%BM%": BORDEAUX_MOYEN, "%B%": BORDEAUX, "%RC%": ROSE_CLAIR, "%R%": ROSE}.items():
    CSS = CSS.replace(_nom, _val)

CSS_LOGIN = """
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { display: none; }
</style>
"""


# =============================================================================
# 3. OUTILS DE FORMAT
# =============================================================================
def fnum(x, d=0):
    """Format français : espace fine pour les milliers, virgule décimale."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/d"
    return f"{x:,.{d}f}".replace(",", "\u202f").replace(".", ",")


def fmad(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/d"
    if abs(x) >= 1e6:
        return f"{fnum(x / 1e6, 1)} M MAD"
    if abs(x) >= 1e3:
        return f"{fnum(x / 1e3, 0)} k MAD"
    return f"{fnum(x, 0)} MAD"


def carte_kpi(libelle, valeur, note=""):
    n = f'<div class="n">{note}</div>' if note else ""
    return f'<div class="kpi"><div class="l">{libelle}</div><div class="v">{valeur}</div>{n}</div>'


def rangee_kpi(cartes):
    cols = st.columns(len(cartes))
    for col, (l, v, n) in zip(cols, cartes):
        col.markdown(carte_kpi(l, v, n), unsafe_allow_html=True)


def logo_svg(taille=44, variante="clair"):
    """Logo QualityPilot : un monogramme Q dont la queue est une aile d'avion, avec une étoile de contrôle au centre.
    variante 'clair' : tuile claire, pour les fonds bordeaux. variante 'fonce' : tuile bordeaux, pour les fonds clairs."""
    if variante == "clair":
        t0, t1, q0, q1, aile0, aile1, filet, etoile = "#FFFFFF", ROSE_CLAIR, BORDEAUX_MOYEN, BORDEAUX_FONCE, BORDEAUX, BORDEAUX_FONCE, BORDEAUX, BORDEAUX
    else:
        t0, t1, q0, q1, aile0, aile1, filet, etoile = BORDEAUX_MOYEN, BORDEAUX_FONCE, "#FFFFFF", ROSE_CLAIR, "#FFFFFF", ROSE, ROSE_CLAIR, "#FFFFFF"
    u = "qp" + variante
    return (
        f'<svg width="{taille}" height="{taille}" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        f'<linearGradient id="{u}t" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t0}"/><stop offset="1" stop-color="{t1}"/></linearGradient>'
        f'<linearGradient id="{u}q" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{q0}"/><stop offset="1" stop-color="{q1}"/></linearGradient>'
        f'<linearGradient id="{u}w" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{aile0}"/><stop offset="1" stop-color="{aile1}"/></linearGradient>'
        f'</defs>'
        f'<rect width="48" height="48" rx="14" fill="url(#{u}t)"/>'
        f'<rect x="2.6" y="2.6" width="42.8" height="42.8" rx="11.8" fill="none" stroke="{filet}" stroke-width="0.7" opacity="0.4"/>'
        f'<circle cx="22.5" cy="22" r="11.5" fill="none" stroke="url(#{u}q)" stroke-width="3"/>'
        f'<path d="M26.5 27.5 L41.5 40.5 L31.5 38.8 L24.5 31.5 Z" fill="url(#{u}w)"/>'
        f'<path d="M22.5 15.2 L23.9 20.6 L29.3 22 L23.9 23.4 L22.5 28.8 L21.1 23.4 L15.7 22 L21.1 20.6 Z" fill="{etoile}"/>'
        f'</svg>'
    )


def banniere(titre, sous_titre, logo=False):
    marque = logo_svg(64) if logo else ""
    texte = f'<div><div class="t">{titre}</div><div class="s">{sous_titre}</div></div>'
    st.markdown(f'<div class="banniere"><div class="bl">{marque}{texte}</div></div>', unsafe_allow_html=True)


def sous_titre(texte):
    st.markdown(f'<div class="sous-titre">{texte}</div>', unsafe_allow_html=True)


def tableau(df):
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True)


def afficher(fig):
    st.pyplot(fig)
    plt.close(fig)


# =============================================================================
# 4. CHARGEMENT ET NETTOYAGE DES DONNÉES
# =============================================================================
@st.cache_data(show_spinner="Chargement et nettoyage des données...")
def charger_et_nettoyer(chemin: str):
    """Charge le CSV, applique les contrôles qualité et renvoie (df, journal)."""
    brut = pd.read_csv(chemin)
    df = brut.copy()
    journal = []

    def noter(controle, constat, traitement):
        journal.append({"Contrôle": controle, "Constat": constat, "Traitement": traitement})

    noter("Volumétrie initiale", f"{len(df):,} lignes et {df.shape[1]} colonnes".replace(",", " "), "Aucun")

    # --- Noms de colonnes
    df.columns = [c.strip() for c in df.columns]

    # --- Espaces parasites dans les textes
    cols_txt = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    n_espaces = 0
    for c in cols_txt:
        propre = df[c].str.strip()
        n_espaces += int((df[c].notna() & (df[c] != propre)).sum())
        df[c] = propre
    noter("Espaces parasites", f"{n_espaces} valeurs texte avec espaces en début ou fin", "Suppression (strip)")

    # --- Doublons
    n_dup = int(df.duplicated().sum())
    df = df.drop_duplicates()
    n_dup_id = int(df["id_nc"].duplicated().sum())
    df = df.drop_duplicates(subset="id_nc", keep="first")
    noter("Doublons", f"{n_dup} lignes entièrement dupliquées, {n_dup_id} identifiants id_nc répétés", "Suppression (première occurrence conservée)")

    # --- Types
    for c in ["date_detection", "date_cloture"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    for c in ["taille_lot", "quantite_non_conforme", "cout_nc_mad", "delai_cloture_jours"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    noter("Types de données", "Dates converties en datetime, montants et quantités en numérique", "Conversion avec contrôle des valeurs invalides")

    # --- Dates de détection invalides
    n_date = int(df["date_detection"].isna().sum())
    df = df[df["date_detection"].notna()]
    noter("Dates de détection invalides", f"{n_date} lignes sans date exploitable", "Suppression" if n_date else "Aucun traitement nécessaire")

    # --- Valeurs manquantes
    cols_cat = [c for c in cols_txt if c not in ("date_detection", "date_cloture")]
    n_cat = int(df[cols_cat].isna().sum().sum())
    for c in cols_cat:
        df[c] = df[c].fillna("Non renseigné")
    noter("Valeurs manquantes (catégories)", f"{n_cat} valeurs manquantes", "Remplacées par « Non renseigné »" if n_cat else "Aucun traitement nécessaire")

    # --- Coûts
    n_neg = int((df["cout_nc_mad"] < 0).sum())
    df = df[~(df["cout_nc_mad"] < 0)]
    n_cout_nan = int(df["cout_nc_mad"].isna().sum())
    if n_cout_nan:
        med = df.groupby(["procede", "gravite"])["cout_nc_mad"].transform("median")
        df["cout_nc_mad"] = df["cout_nc_mad"].fillna(med)
    noter("Coûts", f"{n_neg} coûts négatifs, {n_cout_nan} coûts manquants", "Suppression des négatifs, imputation par la médiane procédé x gravité" if (n_neg or n_cout_nan) else "Aucun traitement nécessaire")

    # --- Cohérence des dates de clôture
    delai_calc = (df["date_cloture"] - df["date_detection"]).dt.days
    incoh = int((delai_calc < 0).sum())
    df.loc[delai_calc < 0, ["date_cloture", "delai_cloture_jours"]] = np.nan
    ecart = int(((delai_calc - df["delai_cloture_jours"]).abs() > 0).sum())
    manquant_rempli = df["delai_cloture_jours"].isna() & df["date_cloture"].notna()
    df.loc[manquant_rempli, "delai_cloture_jours"] = delai_calc[manquant_rempli]
    noter("Cohérence des clôtures", f"{incoh} clôtures antérieures à la détection, {ecart} délais différents de date_cloture - date_detection", "Délais invalidés ou recalculés à partir des dates" if (incoh or ecart) else "Délais cohérents avec les dates, aucun traitement")

    # --- NC encore ouvertes
    n_ouv = int(df["delai_cloture_jours"].isna().sum())
    noter("NC ouvertes", f"{n_ouv} NC sans délai de clôture (statuts Ouverte ou En cours)", "Valeur laissée vide volontairement et exclue des moyennes de délai")

    # --- Quantité non conforme supérieure au lot
    n_qte = int((df["quantite_non_conforme"] > df["taille_lot"]).sum())
    noter("Quantité NC > taille du lot", f"{n_qte} lignes incohérentes", "Conservées après vérification" if n_qte == 0 else "Signalées, conservées")

    # --- Valeurs extrêmes de coût (signalées, conservées)
    q1, q3 = df["cout_nc_mad"].quantile([0.25, 0.75])
    seuil = q3 + 3 * (q3 - q1)
    df["cout_atypique"] = df["cout_nc_mad"] > seuil
    noter("Coûts extrêmes", f"{int(df['cout_atypique'].sum())} NC au-dessus de {fnum(seuil)} MAD (Q3 + 3 x IQR)", "Conservées : surtout des NC détectées chez le client, donc réelles")

    # --- Colonnes dérivées
    df["mois"] = df["date_detection"].dt.to_period("M").dt.to_timestamp()
    df["annee"] = df["date_detection"].dt.year
    df["mois_num"] = df["date_detection"].dt.month
    df["trimestre"] = df["annee"].astype(str) + " T" + df["date_detection"].dt.quarter.astype(str)
    df["chez_client"] = df["etape_detection"].eq("Client")
    df["recurrente"] = df["recurrence"].eq("Oui")
    df["gravite"] = pd.Categorical(df["gravite"], categories=ORDRE_GRAVITE, ordered=True)
    noter("Colonnes créées", "mois, annee, mois_num, trimestre, chez_client, recurrente, cout_atypique", "Ajout pour les KPI")

    noter("Volumétrie finale", f"{len(df):,} lignes exploitables".replace(",", " "), "Aucun")
    df = df.reset_index(drop=True)
    return df, pd.DataFrame(journal)


# =============================================================================
# 5. CALCUL DES KPI
# =============================================================================
def calcul_kpi(d):
    n = len(d)
    client = d[d["chez_client"]]
    autres = d[~d["chez_client"]]
    cout_client = client["cout_nc_mad"].mean() if len(client) else np.nan
    cout_autres = autres["cout_nc_mad"].mean() if len(autres) else np.nan
    return {
        "n": n,
        "cout_total": d["cout_nc_mad"].sum(),
        "cout_moyen": d["cout_nc_mad"].mean(),
        "pct_critique": (d["gravite"] == "Critique").mean() * 100,
        "delai_moyen": d["delai_cloture_jours"].mean(),
        "delai_median": d["delai_cloture_jours"].median(),
        "pct_recurrence": d["recurrente"].mean() * 100,
        "n_client": len(client),
        "pct_client": len(client) / n * 100 if n else np.nan,
        "cout_client": cout_client,
        "cout_autres": cout_autres,
        "ratio_client": cout_client / cout_autres if cout_autres and cout_autres > 0 else np.nan,
        "n_ouvertes": int((d["statut"] != "Clôturée").sum()),
    }


def evolution_volume(d):
    """Compare le volume mensuel moyen du début et de la fin de la sélection."""
    m = d.groupby("mois").size().sort_index()
    if len(m) >= 24:
        debut, fin, lib = m.iloc[:12].mean(), m.iloc[-12:].mean(), "12 premiers mois contre 12 derniers mois"
    elif len(m) >= 4:
        k = len(m) // 2
        debut, fin, lib = m.iloc[:k].mean(), m.iloc[-k:].mean(), "première moitié contre seconde moitié de la période"
    else:
        return np.nan, "période trop courte"
    return (fin - debut) / debut * 100, lib


# =============================================================================
# 6. GRAPHIQUES
# =============================================================================
def nouvelle_fig(l=10, h=4.2):
    fig, ax = plt.subplots(figsize=(l, h))
    return fig, ax


def formater_axe_mois(ax, d_index):
    """Un repère tous les k mois, exactement sur les mois présents dans les données."""
    pas = max(1, int(np.ceil(len(d_index) / 12)))
    reperes = list(d_index[::pas])
    ax.set_xticks(reperes)
    ax.set_xticklabels([f"{MOIS_FR[t.month - 1]} {t.year % 100:02d}" for t in reperes], rotation=45, ha="right")


def fig_tendance(d):
    m = d.groupby("mois").size().sort_index()
    fig, ax = nouvelle_fig(10, 4.2)
    ax.fill_between(m.index, m.values, color=ROSE_CLAIR, alpha=0.9)
    ax.plot(m.index, m.values, color=BORDEAUX, lw=2.2, label="NC par mois")
    if len(m) >= 3:
        ax.plot(m.index, m.rolling(3, min_periods=1).mean(), color="#000000", lw=1.2, ls=":", label="Moyenne mobile 3 mois")
        x = np.arange(len(m))
        a, b = np.polyfit(x, m.values, 1)
        ax.plot(m.index, a * x + b, color=BORDEAUX_FONCE, lw=1.6, ls="--", label=f"Tendance ({fnum(a, 1)} NC par mois)")
    ax.set_ylim(0, m.max() * 1.15)
    ax.set_ylabel("Nombre de NC")
    ax.set_title("Nombre de non-conformités par mois")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right", fontsize=9)
    formater_axe_mois(ax, m.index)
    fig.tight_layout()
    return fig


def fig_gravite_donut(d):
    c = d["gravite"].value_counts().reindex(ORDRE_GRAVITE).fillna(0)
    fig, ax = plt.subplots(figsize=(5, 4.2))
    ax.pie(
        c.values,
        colors=[COULEURS_GRAVITE[g] for g in c.index],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.38, "edgecolor": "white", "linewidth": 2},
    )
    total = c.sum()
    ax.text(0, 0.07, fnum(total), ha="center", va="center", fontsize=20, fontweight="bold")
    ax.text(0, -0.17, "NC", ha="center", va="center", fontsize=10)
    ax.legend(
        [f"{g} : {fnum(v)} ({v / total * 100:.1f} %)".replace(".", ",") for g, v in c.items()],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.12),
        fontsize=9,
    )
    ax.set_title("Répartition par gravité")
    fig.tight_layout()
    return fig


def fig_sites(d):
    g = d.groupby("site").agg(nc=("id_nc", "count"), cout=("cout_nc_mad", "sum")).reset_index().sort_values("nc", ascending=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    sns.barplot(data=g, x="site", y="nc", color=BORDEAUX, ax=axes[0])
    axes[0].bar_label(axes[0].containers[0], labels=[fnum(v) for v in g["nc"]], padding=3, fontsize=9)
    axes[0].set_title("NC par site")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Nombre de NC")
    axes[0].set_ylim(0, g["nc"].max() * 1.15)
    sns.barplot(data=g, x="site", y="cout", color=BORDEAUX_MOYEN, ax=axes[1])
    axes[1].bar_label(axes[1].containers[0], labels=[fmad(v) for v in g["cout"]], padding=3, fontsize=9)
    axes[1].set_title("Coût de la non-qualité par site")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("MAD")
    axes[1].yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: fnum(v / 1e6, 0) + " M"))
    axes[1].set_ylim(0, g["cout"].max() * 1.15)
    for a in axes:
        a.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


def fig_programmes(d):
    g = d.groupby("programme").agg(nc=("id_nc", "count"), cout=("cout_nc_mad", "mean")).reset_index().sort_values("nc", ascending=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    sns.barplot(data=g, y="programme", x="nc", color=BORDEAUX, ax=axes[0], orient="h")
    axes[0].bar_label(axes[0].containers[0], labels=[fnum(v) for v in g["nc"]], padding=3, fontsize=9)
    axes[0].set_title("NC par programme")
    axes[0].set_xlabel("Nombre de NC")
    axes[0].set_ylabel("")
    axes[0].set_xlim(0, g["nc"].max() * 1.18)
    sns.barplot(data=g, y="programme", x="cout", color=BORDEAUX_MOYEN, ax=axes[1], orient="h")
    axes[1].bar_label(axes[1].containers[0], labels=[fmad(v) for v in g["cout"]], padding=3, fontsize=9)
    axes[1].set_title("Coût moyen par NC")
    axes[1].set_xlabel("MAD")
    axes[1].set_ylabel("")
    axes[1].set_xlim(0, g["cout"].max() * 1.3)
    for a in axes:
        a.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def fig_gravite_mensuelle(d):
    p = d.pivot_table(index="mois", columns="gravite", values="id_nc", aggfunc="count", fill_value=0, observed=True).reindex(columns=ORDRE_GRAVITE, fill_value=0)
    fig, ax = nouvelle_fig(10, 4.2)
    ax.stackplot(p.index, [p[g] for g in ORDRE_GRAVITE], labels=ORDRE_GRAVITE, colors=[COULEURS_GRAVITE[g] for g in ORDRE_GRAVITE], alpha=0.95)
    ax.set_title("NC par mois et par gravité")
    ax.set_ylabel("Nombre de NC")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right", ncol=3, fontsize=9)
    formater_axe_mois(ax, p.index)
    fig.tight_layout()
    return fig


def fig_cout_mensuel(d):
    m = d.groupby("mois")["cout_nc_mad"].sum().sort_index() / 1e6
    fig, ax = nouvelle_fig(10, 4.2)
    ax.bar(m.index, m.values, width=22, color=BORDEAUX)
    if len(m) >= 3:
        ax.plot(m.index, m.rolling(3, min_periods=1).mean(), color="#000000", lw=1.4, ls=":", label="Moyenne mobile 3 mois")
        ax.legend(loc="upper right", fontsize=9)
    ax.set_title("Coût mensuel de la non-qualité")
    ax.set_ylabel("Millions de MAD")
    ax.grid(axis="x", visible=False)
    formater_axe_mois(ax, m.index)
    fig.tight_layout()
    return fig


def fig_cout_annuel(d):
    g = d.groupby("annee").agg(cout=("cout_nc_mad", "sum"), nc=("id_nc", "count")).reset_index()
    g["annee"] = g["annee"].astype(str)
    fig, ax = plt.subplots(figsize=(5, 4.2))
    sns.barplot(data=g, x="annee", y="cout", color=BORDEAUX, ax=ax)
    ax.bar_label(ax.containers[0], labels=[fmad(v) for v in g["cout"]], padding=3, fontsize=9)
    ax.set_title("Coût annuel")
    ax.set_xlabel("")
    ax.set_ylabel("MAD")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: fnum(v / 1e6, 0) + " M"))
    ax.set_ylim(0, g["cout"].max() * 1.15)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


def fig_calendrier(d):
    t = d.pivot_table(index="annee", columns="mois_num", values="id_nc", aggfunc="count", fill_value=0)
    t = t.reindex(columns=range(1, 13))
    t.columns = MOIS_FR
    fig, ax = nouvelle_fig(10, 2.8 + 0.3 * len(t))
    sns.heatmap(t, annot=True, fmt=".0f", cmap=CMAP, linewidths=1, linecolor="white", cbar=False, ax=ax, annot_kws={"size": 9}, mask=t.isna())
    ax.set_title("Calendrier des NC (année x mois)")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    return fig


def fig_programmes_trimestre(d):
    t = d.groupby(["trimestre", "programme"]).size().reset_index(name="nc")
    progs = sorted(d["programme"].unique())
    fig, ax = nouvelle_fig(10, 4.2)
    sns.lineplot(data=t, x="trimestre", y="nc", hue="programme", hue_order=progs, palette=PALETTE_PROGRAMMES[: len(progs)], marker="o", lw=2, ax=ax)
    ax.set_title("NC par trimestre et par programme")
    ax.set_xlabel("")
    ax.set_ylabel("Nombre de NC")
    ax.set_ylim(bottom=0)
    ax.grid(axis="x", visible=False)
    ax.legend(title="", ncol=5, loc="upper right", fontsize=9)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    return fig


def fig_pareto(serie, titre, unite):
    s = serie.sort_values(ascending=False)
    part = s / s.sum() * 100
    cum = part.cumsum()
    vitaux = (cum - part) < 80
    fig, ax = nouvelle_fig(11, 5)
    ax.bar(range(len(s)), s.values, color=[BORDEAUX if v else ROSE for v in vitaux], width=0.75)
    ax.set_xticks(range(len(s)))
    ax.set_xticklabels(s.index, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel(unite)
    ax.set_title(titre)
    ax.grid(axis="x", visible=False)
    if s.max() >= 1e6:
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: fnum(v / 1e6, 0) + " M"))
    ax2 = ax.twinx()
    ax2.plot(range(len(s)), cum.values, color="#000000", marker="o", ms=4, lw=1.4)
    ax2.axhline(80, color=BORDEAUX_FONCE, ls="--", lw=1)
    ax2.text(len(s) - 0.5, 81.5, "80 %", ha="right", fontsize=9, color=BORDEAUX_FONCE, fontweight="bold")
    ax2.set_ylim(0, 105)
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax2.set_ylabel("Cumul")
    fig.tight_layout()
    return fig, int(vitaux.sum()), len(s)


def fig_heatmap(tab, titre, fmt=".0f", figsize=(10, 4.2)):
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(tab, annot=True, fmt=fmt, cmap=CMAP, linewidths=1, linecolor="white", cbar=False, ax=ax, annot_kws={"size": 9})
    ax.set_title(titre)
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    return fig


def fig_gravite_procede(d):
    p = pd.crosstab(d["procede"], d["gravite"], normalize="index").reindex(columns=ORDRE_GRAVITE, fill_value=0) * 100
    p = p.sort_values("Critique", ascending=True)
    fig, ax = nouvelle_fig(7, 4.2)
    gauche = np.zeros(len(p))
    for g in ORDRE_GRAVITE:
        ax.barh(p.index, p[g], left=gauche, color=COULEURS_GRAVITE[g], label=g, edgecolor="white")
        for i, (v, l) in enumerate(zip(p[g], gauche)):
            if v >= 6:
                ax.text(l + v / 2, i, f"{v:.0f} %", ha="center", va="center", fontsize=8.5, color="#000000" if g == "Mineure" else "#FFFFFF")
        gauche += p[g].values
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_title("Mix de gravité par procédé")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=9)
    fig.tight_layout()
    return fig


def fig_barres_h(serie, titre, couleur=BORDEAUX, formateur=fnum, xlabel="", figsize=(7, 4.2)):
    s = serie.sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(s.index, s.values, color=couleur)
    ax.bar_label(ax.containers[0], labels=[formateur(v) for v in s.values], padding=3, fontsize=9)
    ax.set_title(titre)
    ax.set_xlabel(xlabel)
    ax.set_xlim(0, s.max() * 1.22)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def fig_etapes_cout(d):
    g = d.groupby("etape_detection")["cout_nc_mad"].mean().sort_values(ascending=False)
    fig, ax = nouvelle_fig(7, 4.2)
    ax.bar(g.index, g.values, color=[BORDEAUX_FONCE if i == "Client" else ROSE for i in g.index], width=0.65)
    ax.bar_label(ax.containers[0], labels=[fmad(v) for v in g.values], padding=3, fontsize=9)
    ax.set_title("Coût moyen d'une NC selon l'étape de détection")
    ax.set_ylabel("MAD")
    ax.set_ylim(0, g.max() * 1.15)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: fnum(v / 1e3, 0) + " k"))
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    fig.tight_layout()
    return fig


def fig_taux_client_mensuel(d):
    g = d.groupby("mois").agg(taux=("chez_client", "mean"), n=("chez_client", "sum")).sort_index()
    g["taux"] *= 100
    fig, ax = nouvelle_fig(10, 3.8)
    ax.bar(g.index, g["n"], width=22, color=ROSE, label="Nombre d'escapes")
    ax.set_ylabel("Escapes par mois")
    ax.grid(axis="x", visible=False)
    ax2 = ax.twinx()
    ax2.plot(g.index, g["taux"], color=BORDEAUX, lw=2.2, label="Part des NC détectées chez le client")
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax2.set_ylim(0, max(g["taux"].max() * 1.3, 1))
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax.set_title("NC détectées chez le client (escapes)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=9)
    formater_axe_mois(ax, g.index)
    fig.tight_layout()
    return fig


def fig_boite_delai(d):
    f = d[d["delai_cloture_jours"].notna()].copy()
    f["gravite"] = f["gravite"].astype(str)
    fig, ax = nouvelle_fig(7, 4.2)
    sns.boxplot(data=f, x="gravite", y="delai_cloture_jours", order=ORDRE_GRAVITE, hue="gravite", hue_order=ORDRE_GRAVITE, palette=COULEURS_GRAVITE, showfliers=False, legend=False, linecolor="#000000", linewidth=1, ax=ax)
    ax.set_title("Délai de clôture selon la gravité")
    ax.set_xlabel("")
    ax.set_ylabel("Jours")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


def fig_histogramme_delai(d):
    f = d["delai_cloture_jours"].dropna()
    fig, ax = nouvelle_fig(7, 4.2)
    sns.histplot(f, bins=30, color=BORDEAUX, edgecolor="white", ax=ax)
    ax.axvline(f.mean(), color="#000000", ls="--", lw=1.4)
    ax.text(f.mean() + 1, ax.get_ylim()[1] * 0.92, f"Moyenne : {fnum(f.mean(), 1)} j", fontsize=9)
    ax.set_title("Distribution des délais de clôture")
    ax.set_xlabel("Jours")
    ax.set_ylabel("Nombre de NC")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


def fig_recurrence_mensuelle(d):
    g = d.groupby("mois")["recurrente"].mean().sort_index() * 100
    fig, ax = nouvelle_fig(7, 4.2)
    ax.plot(g.index, g.values, color=BORDEAUX, lw=2.2)
    ax.fill_between(g.index, g.values, color=ROSE_CLAIR)
    ax.set_ylim(0, max(g.max() * 1.3, 1))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_title("Taux de récurrence par mois")
    ax.grid(axis="x", visible=False)
    formater_axe_mois(ax, g.index)
    fig.tight_layout()
    return fig


# =============================================================================
# 7. CONNEXION
# =============================================================================
def hacher(mot_de_passe, sel=None):
    """Hash PBKDF2-SHA256 salé : le mot de passe n'est jamais stocké en clair."""
    sel = sel or secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel, 120_000)
    return sel.hex() + "$" + h.hex()


def verifier_hash(mot_de_passe, stocke):
    try:
        sel_hex, h_hex = stocke.split("$")
        attendu = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), bytes.fromhex(sel_hex), 120_000)
    except ValueError:
        return False
    return hmac.compare_digest(attendu.hex(), h_hex)


def sauver_comptes(comptes):
    try:
        USERS_PATH.write_text(json.dumps(comptes, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except OSError:
        return False


def charger_comptes():
    if USERS_PATH.exists():
        try:
            return json.loads(USERS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    comptes = {u: {"email": e, "mot_de_passe": hacher(p)} for u, (e, p) in COMPTES_DEMO.items()}
    sauver_comptes(comptes)
    return comptes


def verifier_identifiants(identifiant, mot_de_passe):
    """Connexion par nom d'utilisateur ou par email. Renvoie le nom d'utilisateur ou None."""
    ident = identifiant.strip().lower()
    if not ident or not mot_de_passe:
        return None
    for nom, c in charger_comptes().items():
        if ident in (nom, c.get("email", "").lower()) and verifier_hash(mot_de_passe, c["mot_de_passe"]):
            return nom
    return None


def creer_compte(nom, email, mot_de_passe, confirmation):
    """Valide les champs puis enregistre le compte. Renvoie (succès, message)."""
    nom, email = nom.strip(), email.strip().lower()
    if not (nom and email and mot_de_passe and confirmation):
        return False, "Veuillez remplir tous les champs."
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", nom):
        return False, "Le nom d'utilisateur doit contenir de 3 à 30 caractères : lettres, chiffres, point, tiret ou underscore."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return False, "L'adresse email n'est pas valide."
    if len(mot_de_passe) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if mot_de_passe != confirmation:
        return False, "Les deux mots de passe ne correspondent pas."
    comptes = charger_comptes()
    if nom.lower() in comptes:
        return False, "Ce nom d'utilisateur est déjà utilisé."
    if any(c.get("email", "").lower() == email for c in comptes.values()):
        return False, "Un compte existe déjà avec cet email."
    comptes[nom.lower()] = {"email": email, "mot_de_passe": hacher(mot_de_passe)}
    if not sauver_comptes(comptes):
        return False, "Impossible d'enregistrer le compte : le dossier de l'application est en lecture seule."
    return True, "Compte créé avec succès."


def ouvrir_session(nom, nouveau=False):
    """Connecte l'utilisateur et relance l'application : il arrive directement sur la page Home."""
    st.session_state["connecte"] = True
    st.session_state["utilisateur"] = nom
    st.session_state["page"] = "Home"
    if nouveau:
        st.session_state["nouveau_compte"] = True
    st.rerun()


def page_connexion():
    st.markdown(CSS_LOGIN, unsafe_allow_html=True)
    st.write("")
    gauche, droite = st.columns([1.15, 1], gap="large")
    with gauche:
        st.markdown(
            '<div class="login-gauche"><div class="anneau"></div>'
            f'<div class="marque-login">{logo_svg(60)}<div class="nom">QualityPilot</div></div>'
            '<div class="t">Piloter la non-qualité, sur chaque site et chaque programme.</div>'
            '<div class="s">Registre des non-conformités aéronautiques, 2024 à 2026. A320, A350, B737, B787 et ATR 72, sur trois sites marocains.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with droite:
        onglet_connexion, onglet_creation = st.tabs(["Sign in", "Create account"])
        with onglet_connexion:
            st.markdown("## Sign in")
            st.markdown("Accédez au tableau de bord avec votre compte.")
            with st.form("formulaire_connexion"):
                identifiant = st.text_input("Username or email", key="si_identifiant")
                mot_de_passe = st.text_input("Password", type="password", key="si_mdp")
                envoye = st.form_submit_button("Sign in")
            if envoye:
                nom = verifier_identifiants(identifiant, mot_de_passe)
                if nom:
                    ouvrir_session(nom)
                else:
                    st.error("Identifiant ou mot de passe incorrect. Vérifiez votre saisie et réessayez.")
        with onglet_creation:
            st.markdown("## Create account")
            st.markdown("Créez votre compte : vous entrez directement dans QualityPilot, sans repasser par Sign in.")
            with st.form("formulaire_creation", clear_on_submit=False):
                nom = st.text_input("Username", key="ca_nom")
                email = st.text_input("Email", key="ca_email")
                mdp = st.text_input("Password", type="password", key="ca_mdp")
                confirmation = st.text_input("Confirm Password", type="password", key="ca_confirmation")
                cree = st.form_submit_button("Create account")
            if cree:
                ok, message = creer_compte(nom, email, mdp, confirmation)
                if ok:
                    ouvrir_session(nom.strip().lower(), nouveau=True)
                else:
                    st.error(message)


# =============================================================================
# 8. BARRE LATÉRALE ET FILTRES
# =============================================================================
FILTRES = {
    "site": "Site",
    "programme": "Programme",
    "procede": "Procédé",
    "gravite": "Gravité",
    "etape_detection": "Étape de détection",
    "statut": "Statut",
}


def options_filtre(df, col):
    if col == "gravite":
        return ORDRE_GRAVITE
    return sorted(df[col].dropna().astype(str).unique().tolist())


def cle_case(col, option):
    return f"f_{col}_{option}"


def reinitialiser_filtres(cles):
    """Recoche toutes les cases et remet la période complète."""
    for k in cles:
        st.session_state[k] = True
    st.session_state.pop("f_date", None)


def barre_laterale(df):
    with st.sidebar:
        st.markdown(
            f'<div class="marque"><div class="marque-ligne">{logo_svg(44)}'
            '<div><div class="nom">QualityPilot</div><div class="desc">Pilotage de la non-qualité</div></div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="titre-section">Navigation</div>', unsafe_allow_html=True)
        page = st.radio("Pages", PAGES, label_visibility="collapsed", key="page")

        st.markdown('<div class="titre-section">Filtres</div>', unsafe_allow_html=True)
        dmin, dmax = df["date_detection"].min().date(), df["date_detection"].max().date()
        periode = st.date_input("Période de détection", value=(dmin, dmax), min_value=dmin, max_value=dmax, key="f_date", format="DD/MM/YYYY")

        masque = pd.Series(True, index=df.index)
        toutes_les_cles = []
        for col, libelle in FILTRES.items():
            options = options_filtre(df, col)
            toutes_les_cles += [cle_case(col, o) for o in options]
            with st.expander(libelle, expanded=False):
                choix = [o for o in options if st.checkbox(o, value=True, key=cle_case(col, o))]
            masque &= df[col].astype(str).isin(choix)

        if isinstance(periode, (tuple, list)) and len(periode) == 2:
            debut, fin = pd.Timestamp(periode[0]), pd.Timestamp(periode[1])
            masque &= df["date_detection"].between(debut, fin)
            periode_ok = True
        else:
            periode_ok = False

        st.button("Réinitialiser les filtres", on_click=reinitialiser_filtres, args=(toutes_les_cles,))
        dff = df[masque]
        st.markdown(
            f'<div class="compteur">{fnum(len(dff))} NC sélectionnées sur {fnum(len(df))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="titre-section">Session</div>', unsafe_allow_html=True)
        st.write(f"Connecté : **{st.session_state.get('utilisateur', '')}**")
        if st.button("Se déconnecter"):
            st.session_state["connecte"] = False
            st.session_state.pop("utilisateur", None)
            st.rerun()
    return page, dff, periode_ok


# =============================================================================
# 9. PAGES
# =============================================================================
DESCRIPTIONS_PAGES = {
    "Dashboard": "Les indicateurs clés en un coup d'œil : volume, coût, gravité, délais et détection chez le client.",
    "Tendances": "Évolution mensuelle, calendrier des NC, coût de la non-qualité et trajectoire de chaque programme.",
    "Défauts et Pareto": "Les quelques défauts, pièces et procédés qui concentrent 80 % du problème.",
    "Causes racines 5M": "Matière, Main d'œuvre, Méthode, Machine, Milieu : d'où viennent les NC et quelles actions les traitent.",
    "Détection chez le client": "Combien coûte une NC qui échappe aux contrôles internes et arrive chez le client.",
    "Clôture et récurrence": "Rapidité de traitement des NC et efficacité des actions correctives.",
    "Données et nettoyage": "Journal des contrôles qualité, aperçu des données et export de la sélection.",
    "Rapport": "Conclusions calculées, recommandations et rapport à télécharger.",
}


def aller_a(page):
    """Rappel de bouton : change la page affichée dans la navigation."""
    st.session_state["page"] = page


def icone(chemin):
    return (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        f"{chemin}</svg>"
    )


ICONE_MESURER = icone('<path d="M3 20h18"/><rect x="5" y="11" width="3.5" height="7" rx="1"/><rect x="10.5" y="6" width="3.5" height="12" rx="1"/><rect x="16" y="9" width="3.5" height="9" rx="1"/>')
ICONE_COMPRENDRE = icone('<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/><path d="M8 12l2-2 1.8 1.5L14 9"/>')
ICONE_AGIR = icone('<path d="M5 12.5l4.2 4.2L19 7"/>')


def page_home(df):
    """Page d'accueil : présentation de la plateforme et aperçu du parcours d'analyse."""
    utilisateur = str(st.session_state.get("utilisateur", "")).capitalize()
    st.markdown(
        '<div class="hero"><div class="anneau a1"></div><div class="anneau a2"></div><div class="orbe o1"></div><div class="orbe o2"></div>'
        '<div class="contenu">'
        '<div class="kicker">PLATEFORME DE PILOTAGE QUALITÉ · AÉRONAUTIQUE</div>'
        f'<div class="marque-hero"><div class="logo">{logo_svg(84)}</div><div class="nom">QualityPilot</div></div>'
        '<div class="slogan">Piloter la non-qualité, sur chaque site et chaque programme.</div>'
        f'<div class="texte">Bienvenue {utilisateur}. QualityPilot rassemble le registre des non-conformités, le nettoie, le met en graphiques et en tire des recommandations, '
        'pour voir où la qualité se dégrade, ce que cela coûte et où agir en premier.</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    sous_titre("La plateforme en chiffres")
    programmes = sorted(df["programme"].unique())
    rangee_kpi(
        [
            ("NC enregistrées", fnum(len(df)), "après nettoyage des données"),
            ("Période couverte", f"{df['date_detection'].min():%m/%Y} → {df['date_detection'].max():%m/%Y}", f"{df['annee'].nunique()} années de suivi"),
            ("Sites · Programmes", f"{df['site'].nunique()} · {len(programmes)}", ", ".join(programmes)),
            ("Coût de la non-qualité", fmad(df["cout_nc_mad"].sum()), "sur toute la période"),
        ]
    )

    sous_titre("Ce que fait QualityPilot")
    f1, f2, f3 = st.columns(3, gap="large")
    cartes = [
        (f1, ICONE_MESURER, "Mesurer", "Volume, coût, gravité, délais de clôture et récurrence : chaque indicateur est calculé automatiquement, avec des filtres par site, programme, procédé et période."),
        (f2, ICONE_COMPRENDRE, "Comprendre", "Tendances dans le temps, diagramme de Pareto, causes racines 5M et analyse des NC détectées chez le client : on voit d'où vient le problème."),
        (f3, ICONE_AGIR, "Agir", "Un rapport de conclusions et de recommandations, calculé sur la sélection en cours et téléchargeable, pour décider quoi traiter en premier."),
    ]
    for col, ic, titre, texte in cartes:
        col.markdown(f'<div class="feature"><div class="pastille">{ic}</div><div class="ft">{titre}</div><div class="fd">{texte}</div></div>', unsafe_allow_html=True)

    sous_titre("Le parcours d'analyse")
    etapes = [p for p in PAGES if p != "Home"]
    for debut in range(0, len(etapes), 4):
        cols = st.columns(4, gap="large")
        for col, nom in zip(cols, etapes[debut : debut + 4]):
            numero = etapes.index(nom) + 1
            col.markdown(
                f'<div class="etape"><div class="num">{numero:02d}</div><div class="et">{nom}</div><div class="ed">{DESCRIPTIONS_PAGES[nom]}</div></div>',
                unsafe_allow_html=True,
            )
            col.button(f"Ouvrir : {nom}", key=f"aller_{nom}", on_click=aller_a, args=(nom,))
        st.write("")
    st.caption("Les filtres de la barre latérale s'appliquent à toutes les pages d'analyse, du Dashboard au Rapport.")


def page_dashboard(d):
    utilisateur = str(st.session_state.get("utilisateur", "")).capitalize()
    banniere("Dashboard", f"{utilisateur}, voici les indicateurs clés de la non-qualité sur la sélection en cours : volume, coût, gravité, délais et détection chez le client.")
    k = calcul_kpi(d)
    rangee_kpi(
        [
            ("NC détectées", fnum(k["n"]), f"{fnum(k['n_ouvertes'])} encore ouvertes"),
            ("Coût de la non-qualité", fmad(k["cout_total"]), f"{fnum(k['cout_total'])} MAD"),
            ("Coût moyen par NC", fmad(k["cout_moyen"]), ""),
            ("NC critiques", f"{fnum(k['pct_critique'], 1)} %", f"{fnum((d['gravite'] == 'Critique').sum())} NC"),
        ]
    )
    st.write("")
    rangee_kpi(
        [
            ("Délai moyen de clôture", f"{fnum(k['delai_moyen'], 1)} j", f"Médiane : {fnum(k['delai_median'], 0)} j"),
            ("Taux de récurrence", f"{fnum(k['pct_recurrence'], 1)} %", "NC déjà rencontrées"),
            ("NC détectées chez le client", fnum(k["n_client"]), f"{fnum(k['pct_client'], 1)} % des NC"),
            ("Surcoût d'une NC client", f"x {fnum(k['ratio_client'], 1)}", "coût moyen client / autres étapes"),
        ]
    )
    st.write("")
    c1, c2 = st.columns([2, 1])
    with c1:
        afficher(fig_tendance(d))
        pct, lib = evolution_volume(d)
        if not np.isnan(pct):
            sens = "baisse" if pct < 0 else "hausse"
            st.caption(f"Volume mensuel moyen : {sens} de {fnum(abs(pct), 1)} % ({lib}).")
    with c2:
        afficher(fig_gravite_donut(d))
    sous_titre("Répartition par site et par programme")
    afficher(fig_sites(d))
    afficher(fig_programmes(d))


def page_tendances(d):
    banniere("Tendances", "Évolution dans le temps du volume, de la gravité et du coût des non-conformités.")
    t1, t2, t3, t4 = st.tabs(["Volume et gravité", "Coût", "Calendrier", "Programmes"])
    with t1:
        afficher(fig_tendance(d))
        afficher(fig_gravite_mensuelle(d))
    with t2:
        c1, c2 = st.columns([2, 1])
        with c1:
            afficher(fig_cout_mensuel(d))
        with c2:
            afficher(fig_cout_annuel(d))
    with t3:
        afficher(fig_calendrier(d))
        st.caption("Plus la case est foncée, plus le nombre de NC détectées ce mois-là est élevé.")
    with t4:
        afficher(fig_programmes_trimestre(d))


def page_defauts(d):
    banniere("Défauts et Pareto", "Quels défauts, quelles pièces et quels procédés concentrent l'essentiel du problème ?")
    mesure = st.radio("Mesure du Pareto", ["Nombre de NC", "Coût (MAD)"], horizontal=True)
    if mesure == "Nombre de NC":
        serie, unite = d.groupby("type_defaut").size(), "Nombre de NC"
    else:
        serie, unite = d.groupby("type_defaut")["cout_nc_mad"].sum(), "Coût (MAD)"
    fig, n_vitaux, n_total = fig_pareto(serie, "Pareto des types de défaut (" + ("nombre de NC" if mesure == "Nombre de NC" else "coût en MAD") + ")", unite)
    afficher(fig)
    st.markdown(
        f'<div class="constat"><b>{n_vitaux} types de défaut sur {n_total}</b> concentrent environ 80 % du total. Ce sont les barres foncées du diagramme : le premier terrain d\'action.</div>',
        unsafe_allow_html=True,
    )
    sous_titre("Gravité par procédé")
    c1, c2 = st.columns(2)
    with c1:
        afficher(fig_gravite_procede(d))
    with c2:
        tab = pd.crosstab(d["procede"], d["gravite"]).reindex(columns=ORDRE_GRAVITE, fill_value=0)
        afficher(fig_heatmap(tab, "Nombre de NC par procédé et gravité", fmt=".0f", figsize=(6, 4.2)))
    sous_titre("Pièces les plus touchées")
    c3, c4 = st.columns(2)
    with c3:
        afficher(fig_barres_h(d.groupby("piece").size(), "Nombre de NC par pièce", BORDEAUX, fnum, "Nombre de NC", (7, 4.8)))
    with c4:
        afficher(fig_barres_h(d.groupby("piece")["cout_nc_mad"].sum(), "Coût de la non-qualité par pièce", BORDEAUX_MOYEN, fmad, "MAD", (7, 4.8)))


def page_causes(d):
    banniere("Causes racines 5M", "Matière, Main d'œuvre, Méthode, Machine, Milieu : d'où viennent les non-conformités et quelles actions les traitent.")
    c1, c2 = st.columns(2)
    with c1:
        afficher(fig_barres_h(d.groupby("cause_racine_5M").size(), "NC par cause racine", BORDEAUX, fnum, "Nombre de NC"))
    with c2:
        afficher(fig_barres_h(d.groupby("cause_racine_5M")["cout_nc_mad"].sum(), "Coût par cause racine", BORDEAUX_MOYEN, fmad, "MAD"))
    tab = pd.crosstab(d["cause_racine_5M"], d["procede"])
    afficher(fig_heatmap(tab, "Causes racines par procédé (nombre de NC)", figsize=(10, 3.8)))

    sous_titre("Fournisseurs")
    f = d[d["fournisseur"] != "Interne"]
    if f.empty:
        st.info("Aucune NC fournisseur dans la sélection actuelle.")
    else:
        g = f.groupby("fournisseur").agg(nc=("id_nc", "count"), cout=("cout_nc_mad", "sum"), critiques=("gravite", lambda s: (s == "Critique").sum()))
        c3, c4 = st.columns(2)
        with c3:
            afficher(fig_barres_h(g["nc"], "NC par fournisseur", BORDEAUX, fnum, "Nombre de NC", (7, 4.8)))
        with c4:
            afficher(fig_barres_h(g["cout"], "Coût par fournisseur", BORDEAUX_MOYEN, fmad, "MAD", (7, 4.8)))
    sous_titre("Actions correctives")
    a = d.groupby("action_corrective").agg(NC=("id_nc", "count"), cout=("cout_nc_mad", "sum"), recurrence=("recurrente", "mean"), delai=("delai_cloture_jours", "mean")).reset_index()
    a = a.sort_values("NC", ascending=False)
    a["Coût total"] = a["cout"].map(fmad)
    a["Taux de récurrence"] = (a["recurrence"] * 100).map(lambda v: f"{fnum(v, 1)} %")
    a["Délai moyen (jours)"] = a["delai"].map(lambda v: fnum(v, 1))
    a["NC"] = a["NC"].map(fnum)
    a = a.rename(columns={"action_corrective": "Action corrective"})
    tableau(a[["Action corrective", "NC", "Coût total", "Taux de récurrence", "Délai moyen (jours)"]])


def page_client(d):
    banniere("Détection chez le client", "Une NC qui échappe aux contrôles internes et arrive chez le client coûte beaucoup plus cher.")
    k = calcul_kpi(d)
    rangee_kpi(
        [
            ("NC détectées chez le client", fnum(k["n_client"]), f"{fnum(k['pct_client'], 1)} % des NC"),
            ("Coût moyen NC client", fmad(k["cout_client"]), ""),
            ("Coût moyen autres étapes", fmad(k["cout_autres"]), ""),
            ("Surcoût d'une NC client", f"x {fnum(k['ratio_client'], 1)}", "ratio des coûts moyens"),
        ]
    )
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        afficher(fig_etapes_cout(d))
    with c2:
        c = d["etape_detection"].value_counts()
        afficher(fig_barres_h(c, "NC par étape de détection", BORDEAUX, fnum, "Nombre de NC"))
    afficher(fig_taux_client_mensuel(d))
    sous_titre("Où les NC atteignent-elles le client ?")
    taux = d.pivot_table(index="programme", columns="procede", values="chez_client", aggfunc="mean") * 100
    afficher(fig_heatmap(taux, "Part des NC détectées chez le client (en %)", fmt=".1f", figsize=(10, 3.8)))


def page_cloture(d):
    banniere("Clôture et récurrence", "Rapidité de traitement des NC et capacité des actions correctives à éviter le retour des défauts.")
    k = calcul_kpi(d)
    f = d["delai_cloture_jours"].dropna()
    pct30 = (f > 30).mean() * 100 if len(f) else np.nan
    rangee_kpi(
        [
            ("Délai moyen de clôture", f"{fnum(k['delai_moyen'], 1)} j", "NC clôturées uniquement"),
            ("Délai médian", f"{fnum(k['delai_median'], 0)} j", ""),
            ("Clôtures au-delà de 30 jours", f"{fnum(pct30, 1)} %", ""),
            ("Taux de récurrence", f"{fnum(k['pct_recurrence'], 1)} %", f"{fnum(k['n_ouvertes'])} NC encore ouvertes"),
        ]
    )
    st.write("")
    if f.empty:
        st.info("Aucune NC clôturée dans la sélection actuelle.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            afficher(fig_histogramme_delai(d))
        with c2:
            afficher(fig_boite_delai(d))
    c3, c4 = st.columns(2)
    with c3:
        r = d.groupby("procede")["recurrente"].mean() * 100
        afficher(fig_barres_h(r, "Taux de récurrence par procédé", BORDEAUX, lambda v: f"{fnum(v, 1)} %", "% de NC récurrentes"))
    with c4:
        afficher(fig_recurrence_mensuelle(d))
    sous_titre("Délai moyen par responsable qualité")
    dr = d.groupby("responsable_qualite")["delai_cloture_jours"].mean().dropna()
    if not dr.empty:
        afficher(fig_barres_h(dr, "Délai moyen de clôture (jours)", BORDEAUX_MOYEN, lambda v: f"{fnum(v, 1)} j", "Jours", (10, 3.6)))
    sous_titre("NC encore ouvertes")
    ouv = d[d["statut"] != "Clôturée"].sort_values("date_detection")
    if ouv.empty:
        st.info("Aucune NC ouverte dans la sélection actuelle.")
    else:
        v = ouv[["id_nc", "date_detection", "site", "programme", "procede", "type_defaut", "gravite", "cout_nc_mad", "statut", "responsable_qualite"]].copy()
        v["date_detection"] = v["date_detection"].dt.strftime("%d/%m/%Y")
        v["gravite"] = v["gravite"].astype(str)
        v["cout_nc_mad"] = v["cout_nc_mad"].round(0)
        v.columns = ["Identifiant", "Détection", "Site", "Programme", "Procédé", "Défaut", "Gravité", "Coût (MAD)", "Statut", "Responsable"]
        tableau(v)


def construire_rapport(d):
    """Calcule les KPI, les constats et les recommandations de la sélection en cours."""
    k = calcul_kpi(d)
    pct, lib = evolution_volume(d)

    constats = []
    if not np.isnan(pct):
        if pct < 0:
            constats.append(f"<b>Le volume de NC baisse :</b> {fnum(abs(pct), 1)} % de moins par mois en moyenne ({lib}). Les actions déjà menées produisent des effets.")
        else:
            constats.append(f"<b>Le volume de NC augmente :</b> {fnum(pct, 1)} % de plus par mois en moyenne ({lib}). Un plan de reprise est nécessaire.")

    taux_crit = d.assign(c=d["gravite"] == "Critique").groupby("procede")["c"].mean().sort_values(ascending=False) * 100
    if len(taux_crit) >= 2:
        p1, p2 = taux_crit.index[0], taux_crit.index[1]
        constats.append(
            f"<b>{p1} et {p2} produisent les NC les plus critiques :</b> {fnum(taux_crit.iloc[0], 1)} % et {fnum(taux_crit.iloc[1], 1)} % de leurs NC sont critiques, contre {fnum(d['gravite'].eq('Critique').mean() * 100, 1)} % en moyenne."
        )
    if not np.isnan(k["ratio_client"]):
        constats.append(
            f"<b>Une NC détectée chez le client coûte environ {fnum(k['ratio_client'], 1)} fois plus cher :</b> {fmad(k['cout_client'])} en moyenne, contre {fmad(k['cout_autres'])} pour les autres étapes. {fnum(k['n_client'])} NC concernées ({fnum(k['pct_client'], 1)} %)."
        )
    cause = d.groupby("cause_racine_5M")["cout_nc_mad"].agg(["size", "sum"])
    if not cause.empty:
        top = cause["size"].idxmax()
        constats.append(f"<b>Cause racine dominante : {top}</b>, avec {fnum(cause.loc[top, 'size'] / cause['size'].sum() * 100, 1)} % des NC et {fmad(cause.loc[top, 'sum'])} de coût.")
    serie = d.groupby("type_defaut")["cout_nc_mad"].sum().sort_values(ascending=False)
    if not serie.empty:
        part = serie / serie.sum() * 100
        n80 = int(((part.cumsum() - part) < 80).sum())
        constats.append(f"<b>Effet Pareto :</b> {n80} types de défaut sur {len(serie)} représentent 80 % du coût. Le plus coûteux est « {serie.index[0]} » ({fmad(serie.iloc[0])}).")
    constats.append(f"<b>Récurrence et délais :</b> {fnum(k['pct_recurrence'], 1)} % des NC reviennent, et la clôture prend {fnum(k['delai_moyen'], 1)} jours en moyenne.")

    f = d[d["fournisseur"] != "Interne"].groupby("fournisseur")["cout_nc_mad"].sum().sort_values(ascending=False)
    four = f" Prioriser {f.index[0]} et {f.index[1]}, premiers fournisseurs en coût." if len(f) >= 2 else ""
    p1 = taux_crit.index[0] if len(taux_crit) else "les procédés les plus critiques"
    p2 = taux_crit.index[1] if len(taux_crit) > 1 else ""
    procedes = f"{p1} et {p2}" if p2 else p1

    recos = [
        ("Renforcer la maîtrise de " + procedes, "Mettre en place une inspection de premier article et un contrôle en cours de production renforcé, avec des opérateurs certifiés sur ces procédés. Suivre le taux de NC critiques comme indicateur mensuel."),
        ("Bloquer les NC avant la livraison", f"Chaque NC évitée chez le client économise en moyenne plus de {fmad(k['cout_client'] - k['cout_autres']) if not np.isnan(k['ratio_client']) else 'plusieurs dizaines de milliers de MAD'}. Renforcer le contrôle final par échantillonnage sur les pièces à risque et auditer les lots avant expédition."),
        ("Traiter les causes Matière avec les fournisseurs", "Lancer des plans 8D, une qualification renforcée et un contrôle à réception ciblé." + four),
        ("Concentrer l'effort sur les défauts du Pareto", "Créer un groupe de résolution de problèmes pour les défauts qui représentent 80 % du coût et fixer un objectif de réduction par trimestre."),
        ("Réduire la récurrence et accélérer la clôture", "Vérifier l'efficacité de chaque action corrective trois mois après sa mise en oeuvre. Fixer un délai cible de clôture selon la gravité et relancer les NC ouvertes."),
    ]
    return k, constats, recos


def rapport_html(d, k, constats, recos, utilisateur):
    """Rapport autonome (un seul fichier HTML) : s'ouvre dans le navigateur et s'imprime en PDF."""
    debut, fin = d["date_detection"].min(), d["date_detection"].max()
    kpis = [
        ("NC détectées", fnum(k["n"])),
        ("Coût de la non-qualité", fmad(k["cout_total"])),
        ("NC critiques", f"{fnum(k['pct_critique'], 1)} %"),
        ("Délai moyen de clôture", f"{fnum(k['delai_moyen'], 1)} j"),
        ("Taux de récurrence", f"{fnum(k['pct_recurrence'], 1)} %"),
        ("NC détectées chez le client", f"{fnum(k['n_client'])} ({fnum(k['pct_client'], 1)} %)"),
    ]
    cases = "".join(f'<div class="k"><div class="l">{l}</div><div class="v">{v}</div></div>' for l, v in kpis)
    liste_constats = "".join(f'<div class="c">{c}</div>' for c in constats)
    liste_recos = "".join(f'<div class="r"><div class="rt">{t}</div>{x}</div>' for t, x in recos)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Rapport QualityPilot</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #000; max-width: 900px; margin: 30px auto; padding: 0 20px; }}
.tete {{ background: linear-gradient(120deg, {BORDEAUX_FONCE}, {BORDEAUX} 60%, {BORDEAUX_MOYEN}); color: #fff; border-radius: 16px; padding: 28px 32px; box-shadow: 0 8px 0 -3px {BORDEAUX_MOYEN}, 0 16px 0 -6px {ROSE}, 0 26px 36px -12px rgba(79,11,31,.5); margin-bottom: 36px; }}
.tete h1 {{ margin: 0; font-size: 2rem; color: #fff; text-shadow: 0 2px 0 rgba(79,11,31,.6); }}
.tete p {{ margin: 8px 0 0 0; opacity: .9; }}
h2 {{ color: {BORDEAUX}; border-bottom: 3px solid {ROSE}; padding-bottom: 6px; margin-top: 34px; }}
.grille {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
.k {{ border: 1px solid #EBDDE2; border-top: 4px solid {BORDEAUX}; border-radius: 12px; padding: 12px 14px; box-shadow: 0 10px 20px -12px rgba(122,18,48,.4); }}
.k .l {{ font-size: .8rem; font-weight: 600; }} .k .v {{ font-size: 1.4rem; font-weight: 800; margin-top: 4px; }}
.c {{ border: 1px solid #EBDDE2; border-left: 5px solid {BORDEAUX}; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px; }} .c b {{ color: {BORDEAUX}; }}
.r {{ background: #F8F2F4; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; box-shadow: 5px 5px 0 -1px {ROSE_CLAIR}; }} .r .rt {{ font-weight: 800; color: {BORDEAUX}; margin-bottom: 3px; }}
.pied {{ margin-top: 40px; font-size: .8rem; color: #555; }}
@media print {{ .tete, .k, .r {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
</style></head><body>
<div class="tete"><h1>QualityPilot : rapport de non-qualité</h1><p>Période du {debut:%d/%m/%Y} au {fin:%d/%m/%Y} · {fnum(len(d))} NC · établi pour {utilisateur} le {pd.Timestamp.now():%d/%m/%Y}</p></div>
<h2>Indicateurs clés</h2><div class="grille">{cases}</div>
<h2>Ce que disent les données</h2>{liste_constats}
<h2>Recommandations</h2>{liste_recos}
<div class="pied">Rapport généré automatiquement par QualityPilot à partir de la sélection de filtres en cours.</div>
</body></html>"""


def page_rapport(d):
    utilisateur = str(st.session_state.get("utilisateur", "")).capitalize()
    banniere("Rapport", "Synthèse finale : constats calculés automatiquement sur la sélection en cours, suivis des actions proposées.")
    k, constats, recos = construire_rapport(d)
    rangee_kpi(
        [
            ("NC analysées", fnum(k["n"]), f"{fnum(k['n_ouvertes'])} encore ouvertes"),
            ("Coût de la non-qualité", fmad(k["cout_total"]), ""),
            ("NC critiques", f"{fnum(k['pct_critique'], 1)} %", ""),
            ("Taux de récurrence", f"{fnum(k['pct_recurrence'], 1)} %", f"Clôture en {fnum(k['delai_moyen'], 1)} j en moyenne"),
        ]
    )

    sous_titre("Ce que disent les données")
    for c in constats:
        st.markdown(f'<div class="constat">{c}</div>', unsafe_allow_html=True)

    sous_titre("Recommandations")
    for t, texte in recos:
        st.markdown(f'<div class="reco"><div class="rt">{t}</div>{texte}</div>', unsafe_allow_html=True)

    sous_titre("Emporter le rapport")
    st.markdown("Le rapport est un fichier HTML autonome : ouvrez-le dans votre navigateur, puis imprimez-le en PDF si besoin.")
    st.download_button("Télécharger le rapport (HTML)", data=rapport_html(d, k, constats, recos, utilisateur).encode("utf-8"), file_name="rapport_qualitypilot.html", mime="text/html")


def page_donnees(d, journal, df_complet):
    banniere("Données et nettoyage", "Journal des contrôles qualité appliqués au fichier, aperçu des données et export de la sélection filtrée.")
    t1, t2, t3 = st.tabs(["Journal de nettoyage", "Données filtrées", "Statistiques"])
    with t1:
        st.markdown("Chaque contrôle a été appliqué automatiquement au chargement du fichier `dataset.csv`.")
        tableau(journal)
        sous_titre("Valeurs manquantes après nettoyage")
        mq = df_complet.isna().sum()
        mq = mq[mq > 0].reset_index()
        mq.columns = ["Colonne", "Valeurs manquantes"]
        if mq.empty:
            st.info("Aucune valeur manquante.")
        else:
            tableau(mq)
            st.caption("Les champs de clôture manquent uniquement pour les NC ouvertes ou en cours, c'est attendu.")
    with t2:
        v = d.drop(columns=["mois", "mois_num", "trimestre", "chez_client", "recurrente", "cout_atypique", "annee"]).copy()
        v["gravite"] = v["gravite"].astype(str)
        st.dataframe(v, hide_index=True)
        st.download_button("Télécharger la sélection (CSV)", data=v.to_csv(index=False).encode("utf-8-sig"), file_name="nc_selection.csv", mime="text/csv")
    with t3:
        stats = d[["taille_lot", "quantite_non_conforme", "cout_nc_mad", "delai_cloture_jours"]].describe().T.round(2)
        stats.index = ["Taille du lot", "Quantité non conforme", "Coût (MAD)", "Délai de clôture (jours)"]
        stats.columns = ["Effectif", "Moyenne", "Écart-type", "Min", "25 %", "Médiane", "75 %", "Max"]
        st.dataframe(stats)


# =============================================================================
# 10. POINT D'ENTRÉE
# =============================================================================
def main():
    st.markdown(CSS, unsafe_allow_html=True)
    if not st.session_state.get("connecte", False):
        page_connexion()
        return

    if not DATA_PATH.exists():
        st.error("Le fichier dataset.csv est introuvable. Placez-le dans le même dossier que app.py.")
        return

    df, journal = charger_et_nettoyer(str(DATA_PATH))
    page, dff, periode_ok = barre_laterale(df)

    if st.session_state.pop("nouveau_compte", False):
        st.toast("Compte créé avec succès. Bienvenue sur QualityPilot !")

    # La page Home présente la plateforme : elle ne dépend pas des filtres.
    if page == "Home":
        page_home(df)
        return

    if not periode_ok:
        st.info("Sélectionnez une date de début et une date de fin dans le filtre de période.")
        return
    if dff.empty:
        st.warning("Aucune NC ne correspond aux filtres choisis. Élargissez la sélection ou réinitialisez les filtres.")
        return

    if page == "Dashboard":
        page_dashboard(dff)
    elif page == "Tendances":
        page_tendances(dff)
    elif page == "Défauts et Pareto":
        page_defauts(dff)
    elif page == "Causes racines 5M":
        page_causes(dff)
    elif page == "Détection chez le client":
        page_client(dff)
    elif page == "Clôture et récurrence":
        page_cloture(dff)
    elif page == "Données et nettoyage":
        page_donnees(dff, journal, df)
    else:
        page_rapport(dff)


main()
