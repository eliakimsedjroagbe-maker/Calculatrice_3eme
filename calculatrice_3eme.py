import tkinter as tk
from tkinter import messagebox, filedialog
import math
import threading
import json
import urllib.request
import datetime
import sys
import os

if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

from sympy import (
    symbols, sympify, factor, expand, simplify, solve,
    pretty, sqrt, Rational, Symbol, cancel,
    diff, integrate, parse_expr, SympifyError
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application
)
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# ─── COULEURS ─────────────────────────────────────────────
BG     = "#0a0a1a"
BG2    = "#12122a"
ACCENT = "#ffd200"
TEXT   = "#e0e0e0"
GRAY   = "#666688"
CARD   = "#14142b"
BORDER = "#2a2a5a"
GREEN  = "#00e676"
RED    = "#ff5252"

FONT_TITLE  = ("Courier", 14, "bold")
FONT_LABEL  = ("Courier", 9, "bold")
FONT_INPUT  = ("Courier", 11)
FONT_BTN    = ("Courier", 10, "bold")
FONT_RESULT = ("Courier", 10)
FONT_TAB    = ("Courier", 8, "bold")

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

def parse(s):
    return parse_expr(s, transformations=TRANSFORMS)

# ─── HISTORIQUE GLOBAL ────────────────────────────────────
HISTORY = []

def add_history(module, entree, sortie):
    HISTORY.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "module": module,
        "entree": entree,
        "sortie": sortie[:120] + "..." if len(sortie) > 120 else sortie
    })

# ─── HELPERS ──────────────────────────────────────────────
def make_label(parent, text):
    return tk.Label(parent, text=text, bg=CARD, fg=GRAY, font=FONT_LABEL)

def make_entry(parent, placeholder=""):
    e = tk.Entry(parent, font=FONT_INPUT, bg=BG, fg=TEXT,
                 insertbackground=ACCENT, relief="flat",
                 highlightthickness=1, highlightcolor=ACCENT,
                 highlightbackground=BORDER)
    if placeholder:
        e.insert(0, placeholder)
        e.config(fg=GRAY)
        def fi(ev):
            if e.get() == placeholder: e.delete(0,"end"); e.config(fg=TEXT)
        def fo(ev):
            if not e.get(): e.insert(0,placeholder); e.config(fg=GRAY)
        e.bind("<FocusIn>", fi); e.bind("<FocusOut>", fo)
    return e

def make_btn(parent, text, cmd, color=ACCENT, fg="#000"):
    return tk.Button(parent, text=text, command=cmd,
                     font=FONT_BTN, bg=color, fg=fg,
                     activebackground="#f7971e", relief="flat",
                     cursor="hand2", pady=8)

def result_box(parent, height=12):
    frame = tk.Frame(parent, bg=BG, highlightbackground=ACCENT, highlightthickness=1)
    txt = tk.Text(frame, font=FONT_RESULT, bg=BG, fg=GREEN,
                  relief="flat", padx=10, pady=8,
                  wrap="word", state="disabled", height=height)
    sb = tk.Scrollbar(frame, command=txt.yview, bg=BG)
    txt.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    txt.pack(fill="both", expand=True)
    return frame, txt

def show_result(txt, content, color=GREEN):
    txt.config(state="normal", fg=color)
    txt.delete("1.0","end")
    txt.insert("end", content)
    txt.config(state="disabled")

def show_error(txt, msg):
    show_result(txt, f"❌ ERREUR :\n{msg}", RED)

def r4(x): return round(x, 4)

def gcd(a,b):
    a,b=abs(round(a)),abs(round(b))
    while b: a,b=b,a%b
    return a or 1

def frac(num,den):
    if abs(den)<1e-9: return "∞"
    if abs(num)<1e-9: return "0"
    sign="-" if num*den<0 else ""
    num,den=abs(num),abs(den)
    g=gcd(round(num*1000),round(den*1000))
    n=round(num*1000)//g; d=round(den*1000)//g
    return f"{sign}{n}" if d==1 else f"{sign}{n}/{d}"


# ══════════════════════════════════════════════════════════
# MODULE 1 — CALCULATRICE SCIENTIFIQUE
# ══════════════════════════════════════════════════════════
class ScientifiqueFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD, padx=12, pady=12)
        self.expr = tk.StringVar()

        # Écran
        screen = tk.Entry(self, textvariable=self.expr, font=("Courier",18,"bold"),
                          bg=BG, fg=ACCENT, relief="flat", justify="right",
                          insertbackground=ACCENT,
                          highlightthickness=1, highlightbackground=BORDER)
        screen.pack(fill="x", pady=(0,10), ipady=10)

        self.result_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.result_var, bg=CARD, fg=GREEN,
                 font=("Courier",13), anchor="e").pack(fill="x", pady=(0,8))

        # Boutons
        btns = [
            ["C",    "⌫",   "(",   ")"],
            ["sin(", "cos(","tan(","√("],
            ["π",    "e",   "^",   "%"],
            ["7",    "8",   "9",   "÷"],
            ["4",    "5",   "6",   "×"],
            ["1",    "2",   "3",   "-"],
            ["0",    ".",   "=",   "+"],
        ]
        grid = tk.Frame(self, bg=CARD)
        grid.pack(fill="both", expand=True)
        for r, row in enumerate(btns):
            for c, btn in enumerate(row):
                color = ACCENT if btn=="=" else (
                        "#1a1a3a" if btn in "0123456789." else
                        "#2a1a4a" if btn in ["sin(","cos(","tan(","√(","π","e"] else
                        "#1a2a3a")
                fg_c  = "#000" if btn=="=" else TEXT
                tk.Button(grid, text=btn,
                          font=("Courier",11,"bold"),
                          bg=color, fg=fg_c,
                          relief="flat", cursor="hand2",
                          command=lambda b=btn: self.press(b)
                          ).grid(row=r, column=c, sticky="nsew",
                                 padx=2, pady=2, ipadx=4, ipady=8)
                grid.columnconfigure(c, weight=1)
            grid.rowconfigure(r, weight=1)

    def press(self, btn):
        cur = self.expr.get()
        if btn == "C":
            self.expr.set(""); self.result_var.set("")
        elif btn == "⌫":
            self.expr.set(cur[:-1])
        elif btn == "=":
            self._calculate()
        elif btn == "π":
            self.expr.set(cur + str(math.pi))
        elif btn == "e":
            self.expr.set(cur + str(math.e))
        elif btn == "÷":
            self.expr.set(cur + "/")
        elif btn == "×":
            self.expr.set(cur + "*")
        elif btn == "^":
            self.expr.set(cur + "**")
        elif btn == "√(":
            self.expr.set(cur + "math.sqrt(")
        elif btn in ["sin(","cos(","tan("]:
            self.expr.set(cur + f"math.{btn}")
        else:
            self.expr.set(cur + btn)

    def _calculate(self):
        expr = self.expr.get().strip()
        if not expr: return
        try:
            result = eval(expr, {"math":math,"sqrt":math.sqrt,
                                  "pi":math.pi,"e":math.e,"abs":abs})
            res_str = str(r4(result))
            self.result_var.set(f"= {res_str}")
            add_history("Calc. Sci.", expr, res_str)
        except Exception as ex:
            self.result_var.set(f"Erreur !")


# ══════════════════════════════════════════════════════════
# MODULE 2 — GÉOMÉTRIE (Pythagore, Thalès, Aires)
# ══════════════════════════════════════════════════════════
class GeometrieFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD, padx=14, pady=12)

        # Sélecteur
        top = tk.Frame(self, bg=CARD)
        top.pack(fill="x", pady=(0,8))
        tk.Label(top, text="Choisir :", bg=CARD, fg=GRAY, font=FONT_LABEL).pack(side="left", padx=(0,8))
        self.mode = tk.StringVar(value="pythagore")
        modes = [("📐 Pythagore","pythagore"),("📏 Thalès","thales"),
                 ("🔺 Aires","aires"),("⭕ Cercle","cercle")]
        for label, val in modes:
            tk.Radiobutton(top, text=label, variable=self.mode, value=val,
                           bg=CARD, fg=ACCENT, selectcolor=BG,
                           activebackground=CARD, font=("Courier",8,"bold"),
                           cursor="hand2", command=self._rebuild
                           ).pack(side="left", padx=4)

        self.fields = tk.Frame(self, bg=CARD)
        self.fields.pack(fill="x")

        make_btn(self,"⚡  CALCULER",self.calculate).pack(fill="x",pady=(10,6))

        rf, self.rt = result_box(self, height=12)
        rf.pack(fill="both", expand=True)

        self._rebuild()

    def _clear_fields(self):
        for w in self.fields.winfo_children(): w.destroy()
        self.entries = {}

    def _add_field(self, label, key, placeholder=""):
        row = tk.Frame(self.fields, bg=CARD)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=f"{label} :", bg=CARD, fg=GRAY,
                 font=FONT_LABEL, width=20, anchor="w").pack(side="left")
        e = make_entry(row, placeholder)
        e.pack(side="left", fill="x", expand=True)
        self.entries[key] = e

    def _rebuild(self):
        self._clear_fields()
        m = self.mode.get()
        if m == "pythagore":
            tk.Label(self.fields, text="Laisse vide le côté à calculer",
                     bg=CARD, fg=GRAY, font=("Courier",8)).pack(anchor="w",pady=(0,4))
            self._add_field("Hypoténuse c", "c", "vide si inconnu")
            self._add_field("Côté a", "a", "vide si inconnu")
            self._add_field("Côté b", "b", "vide si inconnu")
        elif m == "thales":
            tk.Label(self.fields, text="AB/AD = AC/AE = BC/DE",
                     bg=CARD, fg=GRAY, font=("Courier",8)).pack(anchor="w",pady=(0,4))
            for k in ["AB","AD","AC","AE","BC","DE"]:
                self._add_field(k, k, "vide si inconnu")
        elif m == "aires":
            tk.Label(self.fields, text="Choisir la figure :",
                     bg=CARD, fg=GRAY, font=("Courier",8)).pack(anchor="w")
            self.fig_var = tk.StringVar(value="triangle")
            figs = [("Triangle","triangle"),("Rectangle","rectangle"),
                    ("Trapèze","trapeze"),("Losange","losange")]
            row = tk.Frame(self.fields, bg=CARD)
            row.pack(fill="x", pady=4)
            for label, val in figs:
                tk.Radiobutton(row, text=label, variable=self.fig_var, value=val,
                               bg=CARD, fg=ACCENT, selectcolor=BG,
                               activebackground=CARD, font=("Courier",8),
                               cursor="hand2").pack(side="left",padx=4)
            self._add_field("Base", "base", "ex: 5")
            self._add_field("Hauteur", "hauteur", "ex: 3")
            self._add_field("Base2 (trapèze)", "base2", "ex: 8")
            self._add_field("Diagonale2 (losange)", "diag2", "ex: 4")
        elif m == "cercle":
            tk.Label(self.fields, text="Entre le rayon OU le diamètre",
                     bg=CARD, fg=GRAY, font=("Courier",8)).pack(anchor="w",pady=(0,4))
            self._add_field("Rayon r", "r", "vide si inconnu")
            self._add_field("Diamètre d", "d", "vide si inconnu")

    def _get(self, key):
        v = self.entries.get(key, None)
        if v is None: return None
        s = v.get().strip()
        if not s or s in ["vide si inconnu","ex: 5","ex: 3","ex: 8","ex: 4"]: return None
        try: return float(s)
        except: return None

    def calculate(self):
        m = self.mode.get()
        try:
            if m == "pythagore":
                c,a,b = self._get("c"), self._get("a"), self._get("b")
                knowns = sum(x is not None for x in [c,a,b])
                if knowns < 2:
                    show_error(self.rt,"Donne au moins 2 valeurs !"); return
                if c is None:
                    c = math.sqrt(a**2 + b**2)
                    msg = f"c = √(a² + b²) = √({a}² + {b}²) = √{r4(a**2+b**2)} ≈ {r4(c)}"
                elif a is None:
                    if c**2 < b**2: show_error(self.rt,"c doit être > b !"); return
                    a = math.sqrt(c**2 - b**2)
                    msg = f"a = √(c² - b²) = √({c}² - {b}²) ≈ {r4(a)}"
                else:
                    if c**2 < a**2: show_error(self.rt,"c doit être > a !"); return
                    b = math.sqrt(c**2 - a**2)
                    msg = f"b = √(c² - a²) = √({c}² - {a}²) ≈ {r4(b)}"
                out = (f"╔══ THÉORÈME DE PYTHAGORE ════════════╗\n\n"
                       f"  c² = a² + b²\n\n"
                       f"  {msg}\n\n"
                       f"  ✅ a={r4(a)}  b={r4(b)}  c={r4(c)}\n\n"
                       f"  Vérif : {r4(a)}² + {r4(b)}² = {r4(a**2+b**2):.4f}\n"
                       f"          c² = {r4(c**2):.4f} ✓\n\n"
                       f"╚═════════════════════════════════════╝")

            elif m == "thales":
                vals = {k: self._get(k) for k in ["AB","AD","AC","AE","BC","DE"]}
                known = {k:v for k,v in vals.items() if v is not None}
                unknown = {k for k,v in vals.items() if v is None}
                # Thalès : AB/AD = AC/AE = BC/DE
                ratio = None
                if "AB" in known and "AD" in known: ratio = known["AB"]/known["AD"]
                elif "AC" in known and "AE" in known: ratio = known["AC"]/known["AE"]
                elif "BC" in known and "DE" in known: ratio = known["BC"]/known["DE"]
                if ratio is None:
                    show_error(self.rt,"Donne assez de valeurs pour calculer le rapport !"); return
                results = dict(known)
                pairs = [("AB","AD"),("AC","AE"),("BC","DE")]
                for a,b in pairs:
                    if a in unknown and b in results: results[a] = results[b]*ratio
                    elif b in unknown and a in results: results[b] = results[a]/ratio
                lines = "\n".join(f"  {k} = {r4(v)}" for k,v in results.items())
                out = (f"╔══ THÉORÈME DE THALÈS ═══════════════╗\n\n"
                       f"  Rapport k = {r4(ratio)}\n\n"
                       f"  AB/AD = AC/AE = BC/DE = {r4(ratio)}\n\n"
                       f"  Valeurs :\n{lines}\n\n"
                       f"╚═════════════════════════════════════╝")

            elif m == "aires":
                fig = self.fig_var.get()
                base = self._get("base")
                h    = self._get("hauteur")
                b2   = self._get("base2")
                d2   = self._get("diag2")
                if fig == "triangle":
                    if base is None or h is None:
                        show_error(self.rt,"Donne base et hauteur !"); return
                    aire = (base * h) / 2
                    out = (f"╔══ AIRE DU TRIANGLE ═════════════════╗\n\n"
                           f"  Aire = (base × hauteur) / 2\n"
                           f"       = ({base} × {h}) / 2\n"
                           f"       = {r4(aire)} unités²\n\n"
                           f"  Périmètre : non calculable sans les 3 côtés\n\n"
                           f"╚═════════════════════════════════════╝")
                elif fig == "rectangle":
                    if base is None or h is None:
                        show_error(self.rt,"Donne longueur et largeur !"); return
                    aire = base * h
                    perim = 2*(base+h)
                    diag = math.sqrt(base**2 + h**2)
                    out = (f"╔══ AIRE DU RECTANGLE ════════════════╗\n\n"
                           f"  Aire      = L × l = {base} × {h} = {r4(aire)} u²\n"
                           f"  Périmètre = 2(L+l) = {r4(perim)} u\n"
                           f"  Diagonale = √(L²+l²) = {r4(diag)} u\n\n"
                           f"╚═════════════════════════════════════╝")
                elif fig == "trapeze":
                    if base is None or b2 is None or h is None:
                        show_error(self.rt,"Donne base1, base2 et hauteur !"); return
                    aire = ((base+b2)*h)/2
                    out = (f"╔══ AIRE DU TRAPÈZE ══════════════════╗\n\n"
                           f"  Aire = ((b1 + b2) × h) / 2\n"
                           f"       = (({base} + {b2}) × {h}) / 2\n"
                           f"       = {r4(aire)} u²\n\n"
                           f"╚═════════════════════════════════════╝")
                elif fig == "losange":
                    if base is None or d2 is None:
                        show_error(self.rt,"Donne les 2 diagonales !"); return
                    aire = (base*d2)/2
                    out = (f"╔══ AIRE DU LOSANGE ══════════════════╗\n\n"
                           f"  Aire = (d1 × d2) / 2\n"
                           f"       = ({base} × {d2}) / 2\n"
                           f"       = {r4(aire)} u²\n\n"
                           f"╚═════════════════════════════════════╝")

            elif m == "cercle":
                r_val = self._get("r")
                d_val = self._get("d")
                if r_val is None and d_val is None:
                    show_error(self.rt,"Donne le rayon ou le diamètre !"); return
                if r_val is None: r_val = d_val / 2
                if d_val is None: d_val = r_val * 2
                aire   = math.pi * r_val**2
                perim  = 2 * math.pi * r_val
                out = (f"╔══ CERCLE ═══════════════════════════╗\n\n"
                       f"  Rayon     : r = {r4(r_val)}\n"
                       f"  Diamètre  : d = {r4(d_val)}\n\n"
                       f"  Aire      = π × r² = {r4(aire)} u²\n"
                       f"  Périmètre = 2πr    = {r4(perim)} u\n\n"
                       f"╚═════════════════════════════════════╝")

            show_result(self.rt, out)
            add_history("Géométrie", m, out)
        except Exception as ex:
            show_error(self.rt, str(ex))


# ══════════════════════════════════════════════════════════
# MODULE 3 — FONCTION AFFINE + GRAPHIQUE
# ══════════════════════════════════════════════════════════
class AffineGraphFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD, padx=14, pady=12)

        top = tk.Frame(self, bg=CARD)
        top.pack(fill="x")

        left = tk.Frame(top, bg=CARD)
        left.pack(side="left", fill="y", padx=(0,10))

        tk.Label(left, text="f(x) = ax + b", bg=CARD, fg=ACCENT,
                 font=("Courier",12,"bold")).pack(anchor="w", pady=(0,8))

        for label, key, ph in [("a (coefficient)","a","ex: 2"),
                                ("b (terme constant)","b","ex: -3"),
                                ("x min","xmin","-10"),
                                ("x max","xmax","10")]:
            tk.Label(left, text=label, bg=CARD, fg=GRAY, font=FONT_LABEL).pack(anchor="w")
            e = make_entry(left, ph)
            e.pack(fill="x", pady=3)
            setattr(self, f"e_{key}", e)

        make_btn(left,"📈  TRACER",self.plot).pack(fill="x",pady=(10,4))
        make_btn(left,"🧮  CALCULER",self.calculate).pack(fill="x",pady=4)

        rf, self.rt = result_box(left, height=8)
        rf.pack(fill="both", expand=True, pady=(6,0))

        # Zone graphique
        self.graph_frame = tk.Frame(top, bg=BG,
                                    highlightbackground=BORDER, highlightthickness=1)
        self.graph_frame.pack(side="left", fill="both", expand=True)

        tk.Label(self.graph_frame, text="Le graphique apparaîtra ici",
                 bg=BG, fg=GRAY, font=("Courier",9)).pack(expand=True)

    def _get_ab(self):
        a_s = self.e_a.get().strip()
        b_s = self.e_b.get().strip()
        xmin_s = self.e_xmin.get().strip() or "-10"
        xmax_s = self.e_xmax.get().strip() or "10"
        a = float(a_s) if a_s not in ["","ex: 2"] else None
        b = float(b_s) if b_s not in ["","ex: -3"] else None
        xmin = float(xmin_s) if xmin_s != "-10" else -10.0
        xmax = float(xmax_s) if xmax_s != "10" else 10.0
        return a, b, xmin, xmax

    def plot(self):
        try:
            a, b, xmin, xmax = self._get_ab()
            if a is None or b is None:
                show_error(self.rt,"Entre a et b !"); return

            for w in self.graph_frame.winfo_children(): w.destroy()

            fig, ax = plt.subplots(figsize=(4.5, 3.8), facecolor="#0a0a1a")
            ax.set_facecolor("#0a0a1a")
            xs = np.linspace(xmin, xmax, 400)
            ys = a*xs + b
            ax.plot(xs, ys, color="#ffd200", linewidth=2,
                    label=f"f(x) = {a}x + ({b})")
            ax.axhline(0, color="#444466", linewidth=0.8)
            ax.axvline(0, color="#444466", linewidth=0.8)
            ax.grid(True, color="#1a1a3a", linewidth=0.5)
            ax.tick_params(colors=TEXT)
            for spine in ax.spines.values(): spine.set_color(BORDER)
            ax.legend(facecolor=CARD, labelcolor=ACCENT,
                      edgecolor=BORDER, fontsize=8)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig)

            show_result(self.rt, f"✅ Graphique tracé !\n  f(x) = {a}x + ({b})\n  x ∈ [{xmin}, {xmax}]")
            add_history("Affine", f"a={a} b={b}", f"f(x)={a}x+{b}")
        except Exception as ex:
            show_error(self.rt, str(ex))

    def calculate(self):
        try:
            a, b, xmin, xmax = self._get_ab()
            if a is None or b is None:
                show_error(self.rt,"Entre a et b !"); return
            sens = "croissante ↗" if a>0 else ("décroissante ↘" if a<0 else "constante →")
            zero = frac(-b, a) if abs(a)>1e-9 else None
            xs = [xmin, 0.0, xmax, 1.0, -1.0]
            xs = sorted(set(r4(x) for x in xs))
            tableau = "\n".join(f"  x={x:>6}  →  f(x)={r4(a*x+b)}" for x in xs)
            show_result(self.rt,
                f"╔══ FONCTION AFFINE ══════════════════╗\n\n"
                f"  f(x) = {a}x + ({b})\n\n"
                f"  Coeff. directeur : a = {a}\n"
                f"  Terme constant   : b = {b}\n"
                f"  Sens             : {sens}\n"
                f"  Zéro             : x = {zero if zero else 'aucun'}\n\n"
                f"  Tableau de valeurs :\n{tableau}\n\n"
                f"╚═════════════════════════════════════╝")
            add_history("Affine", f"a={a} b={b}", f"sens={sens} zero={zero}")
        except Exception as ex:
            show_error(self.rt, str(ex))


# ══════════════════════════════════════════════════════════
# MODULE 4 — ALGÈBRE PUISSANTE
# ══════════════════════════════════════════════════════════
class AlgebreFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD, padx=14, pady=12)
        tk.Label(self, text="Expression (** pour puissance, * pour multiplier)",
                 bg=CARD, fg=GRAY, font=("Courier",8)).pack(anchor="w")
        self.expr_entry = make_entry(self, "ex: (2x+3)**2 - (x-1)*(x+5)")
        self.expr_entry.pack(fill="x", pady=6)

        btn_frame = tk.Frame(self, bg=CARD)
        btn_frame.pack(fill="x", pady=4)
        for txt, cmd, col in [
            ("🔓 DÉVELOPPER", self.do_expand,  "#1565c0"),
            ("🔒 FACTORISER", self.do_factor,  "#6a1b9a"),
            ("✨ SIMPLIFIER", self.do_simplify, "#1b5e20"),
            ("📉 RÉDUIRE",    self.do_cancel,  "#bf360c"),
        ]:
            tk.Button(btn_frame, text=txt, command=cmd,
                      font=("Courier",8,"bold"), bg=col, fg=TEXT,
                      relief="flat", cursor="hand2", padx=4, pady=7
                      ).pack(side="left", expand=True, fill="x", padx=2)

        tk.Label(self, text="── Exemples ──", bg=CARD, fg=GRAY,
                 font=("Courier",8)).pack(anchor="w", pady=(8,2))
        for ex, label in [
            ("(2x+3)**2 - 4*(x-1)**2",       "Carré - carré"),
            ("x**4 - 16",                     "Diff. de carrés"),
            ("6*x**3 + 11*x**2 - 10*x - 24", "Cubique"),
            ("(x**2-9)/(x-3)",                "Fraction algébrique"),
        ]:
            tk.Button(self, text=f"▶  {label}  →  {ex}",
                      bg=BG2, fg=GRAY, font=("Courier",7), relief="flat",
                      cursor="hand2", anchor="w",
                      command=lambda e=ex: self._fill(e)
                      ).pack(fill="x", pady=1)

        rf, self.rt = result_box(self, height=10)
        rf.pack(fill="both", expand=True, pady=(8,0))

    def _fill(self, text):
        self.expr_entry.delete(0,"end")
        self.expr_entry.insert(0, text)
        self.expr_entry.config(fg=TEXT)

    def _get(self):
        raw = self.expr_entry.get().strip().replace("^","**")
        if not raw: raise ValueError("Entre une expression !")
        return parse(raw)

    def do_expand(self):
        try:
            e=self._get(); r=expand(e)
            out=(f"╔══ DÉVELOPPEMENT ════════════════════╗\n\n"
                 f"  Expression :\n  {e}\n\n"
                 f"  Résultat :\n  {r}\n\n"
                 f"╚═════════════════════════════════════╝")
            show_result(self.rt, out)
            add_history("Algèbre", str(e), f"expand={r}")
        except Exception as ex: show_error(self.rt, str(ex))

    def do_factor(self):
        try:
            e=self._get(); r=factor(e)
            out=(f"╔══ FACTORISATION ════════════════════╗\n\n"
                 f"  Expression :\n  {e}\n\n"
                 f"  Factorisée :\n  {r}\n\n"
                 f"  Développée :\n  {expand(e)}\n\n"
                 f"╚═════════════════════════════════════╝")
            show_result(self.rt, out)
            add_history("Algèbre", str(e), f"factor={r}")
        except Exception as ex: show_error(self.rt, str(ex))

    def do_simplify(self):
        try:
            e=self._get(); r=simplify(e)
            out=(f"╔══ SIMPLIFICATION ═══════════════════╗\n\n"
                 f"  Expression :\n  {e}\n\n"
                 f"  Simplifiée :\n  {r}\n\n"
                 f"╚═════════════════════════════════════╝")
            show_result(self.rt, out)
            add_history("Algèbre", str(e), f"simplify={r}")
        except Exception as ex: show_error(self.rt, str(ex))

    def do_cancel(self):
        try:
            e=self._get(); r=cancel(e)
            out=(f"╔══ RÉDUCTION ════════════════════════╗\n\n"
                 f"  Expression :\n  {e}\n\n"
                 f"  Réduite :\n  {r}\n\n"
                 f"╚═════════════════════════════════════╝")
            show_result(self.rt, out)
            add_history("Algèbre", str(e), f"cancel={r}")
        except Exception as ex: show_error(self.rt, str(ex))


# ══════════════════════════════════════════════════════════
# MODULE 5 — RÉSOLUTION D'ÉQUATIONS
# ══════════════════════════════════════════════════════════
class EquationFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD, padx=14, pady=12)
        tk.Label(self, text="Équation (ex: x**3 - 6*x**2 + 11*x - 6 = 0)",
                 bg=CARD, fg=GRAY, font=("Courier",8)).pack(anchor="w")
        self.eq_entry = make_entry(self, "ex: x**3 - 6x**2 + 11x - 6 = 0")
        self.eq_entry.pack(fill="x", pady=6)
        tk.Label(self, text="Variable :", bg=CARD, fg=GRAY, font=("Courier",8)).pack(anchor="w")
        self.var_entry = make_entry(self, "x")
        self.var_entry.pack(fill="x", pady=(0,8))
        make_btn(self,"⚡  RÉSOUDRE",self.solve_eq).pack(fill="x",pady=(0,6))

        tk.Label(self, text="── Exemples ──", bg=CARD, fg=GRAY,
                 font=("Courier",8)).pack(anchor="w", pady=(4,2))
        for ex, label in [
            ("2*x**2 + 5*x - 3 = 0",         "Degré 2"),
            ("x**3 - 6*x**2 + 11*x - 6 = 0", "Degré 3"),
            ("x**4 - 5*x**2 + 4 = 0",         "Bicarrée"),
            ("(x+2)**3 = 8",                   "Avec membre droit"),
        ]:
            tk.Button(self, text=f"▶  {label}  →  {ex}",
                      bg=BG2, fg=GRAY, font=("Courier",7), relief="flat",
                      cursor="hand2", anchor="w",
                      command=lambda e=ex: self._fill(e)
                      ).pack(fill="x", pady=1)

        rf, self.rt = result_box(self, height=10)
        rf.pack(fill="both", expand=True, pady=(8,0))

    def _fill(self, text):
        self.eq_entry.delete(0,"end")
        self.eq_entry.insert(0, text)
        self.eq_entry.config(fg=TEXT)

    def solve_eq(self):
        raw = self.eq_entry.get().strip().replace("^","**")
        var_str = self.var_entry.get().strip() or "x"
        if not raw: show_error(self.rt,"Entre une équation !"); return
        try:
            var = Symbol(var_str)
            if "=" in raw:
                p = raw.split("=",1)
                expr = parse(p[0]) - parse(p[1])
            else:
                expr = parse(raw)
            solutions = solve(expr, var)
            factored  = factor(expr)
            expanded  = expand(expr)
            sol_str   = "\n".join(f"  {var} = {s}" for s in solutions) if solutions else "  Pas de solution réelle."
            out = (f"╔══ RÉSOLUTION ═══════════════════════╗\n\n"
                   f"  Équation : {expr} = 0\n\n"
                   f"  Développée  : {expanded}\n"
                   f"  Factorisée  : {factored}\n\n"
                   f"  Solutions :\n{sol_str}\n\n"
                   f"╚═════════════════════════════════════╝")
            show_result(self.rt, out)
            add_history("Équation", str(expr), sol_str)
        except Exception as ex:
            show_error(self.rt, str(ex))


# ══════════════════════════════════════════════════════════
# MODULE 6 — SYSTÈME (2,3,4 inconnues)
# ══════════════════════════════════════════════════════════
class SystemeFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD, padx=14, pady=12)
        top = tk.Frame(self, bg=CARD)
        top.pack(fill="x", pady=(0,8))
        tk.Label(top, text="Inconnues :", bg=CARD, fg=GRAY, font=FONT_LABEL).pack(side="left", padx=(0,8))
        self.nb_var = tk.IntVar(value=2)
        for n in [2,3,4]:
            tk.Radiobutton(top, text=f"{n}", variable=self.nb_var, value=n,
                           bg=CARD, fg=ACCENT, selectcolor=BG,
                           activebackground=CARD, font=("Courier",10,"bold"),
                           cursor="hand2", command=self._rebuild
                           ).pack(side="left", padx=6)

        self.fields_frame = tk.Frame(self, bg=CARD)
        self.fields_frame.pack(fill="x")
        make_btn(self,"⚡  RÉSOUDRE",self.solve_sys).pack(fill="x",pady=(10,6))

        tk.Label(self, text="── Exemples ──", bg=CARD, fg=GRAY,
                 font=("Courier",8)).pack(anchor="w", pady=(2,2))
        for nb, eqs, label in [
            (2,"2x + 3y = 7\nx - y = 1",                                "2 inconnues"),
            (2,"x**2 + y**2 = 25\nx + y = 7",                           "Non-linéaire"),
            (3,"x + y + z = 6\n2x - y + z = 3\nx + 2y - z = 2",        "3 inconnues"),
            (4,"x+y+z+w=10\n2x-y+z-w=2\nx+2y-z+w=4\nx-y+2z+w=6",      "4 inconnues"),
        ]:
            tk.Button(self, text=f"▶  {label}",
                      bg=BG2, fg=GRAY, font=("Courier",7), relief="flat",
                      cursor="hand2", anchor="w",
                      command=lambda n=nb, e=eqs: self._load(n,e)
                      ).pack(fill="x", pady=1)

        rf, self.rt = result_box(self, height=8)
        rf.pack(fill="both", expand=True, pady=(8,0))
        self._rebuild()

    def _rebuild(self):
        for w in self.fields_frame.winfo_children(): w.destroy()
        n = self.nb_var.get()
        vn = ["x","y","z","w"][:n]
        tk.Label(self.fields_frame,
                 text=f"Inconnues : {', '.join(vn)}   |   Une équation par ligne",
                 bg=CARD, fg=GRAY, font=("Courier",8)).pack(anchor="w", pady=(0,4))
        tf = tk.Frame(self.fields_frame, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        tf.pack(fill="x")
        self.txt_in = tk.Text(tf, font=FONT_INPUT, bg=BG, fg=TEXT,
                              insertbackground=ACCENT, relief="flat",
                              padx=8, pady=8, height=n+1, wrap="word")
        self.txt_in.pack(fill="both")
        defaults = {2:"2x + 3y = 7\nx - y = 1",
                    3:"x + y + z = 6\n2x - y + z = 3\nx + 2y - z = 2",
                    4:"x+y+z+w=10\n2x-y+z-w=2\nx+2y-z+w=4\nx-y+2z+w=6"}
        self.txt_in.insert("end", defaults[n])

    def _load(self, nb, eqs):
        self.nb_var.set(nb); self._rebuild()
        self.txt_in.delete("1.0","end")
        self.txt_in.insert("end", eqs)

    def solve_sys(self):
        raw = self.txt_in.get("1.0","end").strip()
        n = self.nb_var.get()
        vn = ["x","y","z","w"][:n]
        if not raw: show_error(self.rt,"Entre au moins une équation !"); return
        try:
            var_list = [Symbol(v) for v in vn]
            eqs=[]; lines_used=[]
            for line in raw.splitlines():
                line=line.strip().replace("^","**")
                if not line: continue
                if "=" in line:
                    p=line.split("=",1)
                    eqs.append(parse(p[0])-parse(p[1]))
                else:
                    eqs.append(parse(line))
                lines_used.append(line)
            if len(eqs)<n:
                show_error(self.rt,f"Il faut {n} équations pour {n} inconnues !"); return
            solutions=solve(eqs,var_list)
            if not solutions: sol_str="  ∅ Pas de solution."
            elif isinstance(solutions,dict):
                sol_str="\n".join(f"  {k} = {v}" for k,v in solutions.items())
            elif isinstance(solutions,list):
                sol_str=""
                for s in solutions:
                    if isinstance(s,tuple):
                        sol_str+="  ("+", ".join(f"{var_list[i]}={v}" for i,v in enumerate(s))+"\n"
                    else: sol_str+=f"  {s}\n"
            else: sol_str=f"  {solutions}"
            eq_str="\n".join(f"  ({i+1})  {l}" for i,l in enumerate(lines_used))
            out=(f"╔══ SYSTÈME {n} INCONNUES ════════════════╗\n\n"
                 f"  Inconnues : {', '.join(vn)}\n\n"
                 f"  Équations :\n{eq_str}\n\n"
                 f"  Solutions :\n{sol_str}\n\n"
                 f"╚═════════════════════════════════════╝")
            show_result(self.rt, out)
            add_history("Système", eq_str, sol_str)
        except Exception as ex: show_error(self.rt, str(ex))


# ══════════════════════════════════════════════════════════
# MODULE 7 — STATISTIQUES
# ══════════════════════════════════════════════════════════
class StatsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD, padx=14, pady=12)
        make_label(self,"Valeurs (virgule ou espace) :").pack(anchor="w")
        self.entry = make_entry(self)
        self.entry.pack(fill="x", pady=6)
        make_btn(self,"⚡  ANALYSER",self.calculate).pack(fill="x",pady=(4,8))
        rf, self.rt = result_box(self)
        rf.pack(fill="both", expand=True)

    def calculate(self):
        raw = self.entry.get().replace(","," ").split()
        try: nums=[float(v) for v in raw if v]
        except ValueError: show_error(self.rt,"Valeurs invalides !"); return
        if len(nums)<2: show_error(self.rt,"Au moins 2 valeurs !"); return
        n=len(nums); s=sorted(nums)
        mean=sum(nums)/n
        med=(s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]
        freq={}
        for v in nums: freq[v]=freq.get(v,0)+1
        max_f=max(freq.values())
        mode=[k for k,v in freq.items() if v==max_f]
        ecart=math.sqrt(sum((v-mean)**2 for v in nums)/n)
        tableau="\n".join(
            f"  {r4(v):>10}  |  {freq[v]:>4}  |  {r4(freq[v]/n*100):>7}%"
            for v in sorted(freq))
        out=(f"╔══ STATISTIQUES ═════════════════════╗\n\n"
             f"  n={n}  Min={s[0]}  Max={s[-1]}  Étendue={r4(s[-1]-s[0])}\n\n"
             f"  Moyenne    : x̄ = {r4(mean)}\n"
             f"  Médiane    : Me = {r4(med)}\n"
             f"  Mode(s)    : {', '.join(str(r4(m)) for m in mode)}\n"
             f"  Écart-type : σ = {r4(ecart)}\n"
             f"  Variance   : σ² = {r4(ecart**2)}\n\n"
             f"  Série : {' ; '.join(str(r4(v)) for v in s)}\n\n"
             f"╠══ TABLEAU DES FRÉQUENCES ═══════════╣\n\n"
             f"  {'Valeur':>10}  | Eff. | Fréq. (%)\n"
             f"  {'─'*38}\n{tableau}\n\n"
             f"╚═════════════════════════════════════╝")
        show_result(self.rt, out)
        add_history("Stats", self.entry.get(), f"moy={r4(mean)} med={r4(med)}")


# ══════════════════════════════════════════════════════════
# MODULE 8 — TEXTE → ÉQUATIONS (IA)
# ══════════════════════════════════════════════════════════
class TexteEquationFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD, padx=14, pady=12)
        tk.Label(self, text="🤖 Écris un problème, l'IA le traduit en équations et résout",
                 bg=CARD, fg=GRAY, font=FONT_LABEL).pack(anchor="w", pady=(0,6))
        tf = tk.Frame(self, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        tf.pack(fill="x", pady=4)
        self.txt_in = tk.Text(tf, font=FONT_INPUT, bg=BG, fg=TEXT,
                              insertbackground=ACCENT, relief="flat",
                              padx=8, pady=8, height=5, wrap="word")
        self.txt_in.pack(fill="both")
        tk.Label(self, text="── Exemples ──", bg=CARD, fg=GRAY,
                 font=("Courier",8)).pack(anchor="w", pady=(6,2))
        for ex in [
            "Un sac contient 250 plants de type A et B. Le sac coûte 55000F. Un plant A coûte 200F et un plant B 250F.",
            "Un ouvrier travaille 25 jours et sa femme 15 jours. Ensemble ils gagnent 42070F.",
            "La somme de deux nombres est 15 et leur différence est 3.",
        ]:
            tk.Button(self, text=f"▶  {ex[:62]}...",
                      bg=BG2, fg=GRAY, font=("Courier",7), relief="flat",
                      cursor="hand2", anchor="w",
                      command=lambda t=ex: self._fill(t)
                      ).pack(fill="x", pady=1)
        make_btn(self,"⚡  TRADUIRE & RÉSOUDRE",self.translate).pack(fill="x",pady=(10,4))
        self.status = tk.Label(self, text="", bg=CARD, fg=ACCENT, font=("Courier",9))
        self.status.pack(anchor="w")
        rf, self.rt = result_box(self, height=10)
        rf.pack(fill="both", expand=True, pady=(4,0))

    def _fill(self, text):
        self.txt_in.delete("1.0","end")
        self.txt_in.insert("end", text)

    def translate(self):
        texte = self.txt_in.get("1.0","end").strip()
        if not texte: show_error(self.rt,"Écris un problème !"); return
        self.status.config(text="⏳ Analyse...")
        show_result(self.rt,"Connexion à l'IA...\nPatiente quelques secondes.")
        threading.Thread(target=self._run, args=(texte,), daemon=True).start()

    def _run(self, texte):
        try:
            result = self._call_ai(texte)
            self.after(0, lambda: show_result(self.rt, result))
            self.after(0, lambda: self.status.config(text="✅ Terminé !"))
            add_history("Texte→Éq.", texte[:60], result[:80])
        except Exception as ex:
            self.after(0, lambda: show_error(self.rt, f"{ex}"))
            self.after(0, lambda: self.status.config(text="❌ Erreur"))

    def _call_ai(self, texte):
        """Résolution locale sans API — détecte le type de problème et résout avec sympy."""
        import re
        import sympy as sp

        t = texte.lower()
        nums = [float(x.replace(",",".")) for x in re.findall(r"\d+[,.]?\d*", texte)]

        # ── Helpers ──────────────────────────────────────────────────
        def fmt(v):
            v = float(v)
            return str(int(v)) if v == int(v) else f"{v:.4f}".rstrip("0")

        def solve2(eq1, eq2, x, y):
            sol = sp.solve([eq1, eq2], [x, y])
            return sol

        res = []

        # ════════════════════════════════════════════════════════
        # PATTERN 1 : somme + différence  ex: "somme est 15, différence est 3"
        # ════════════════════════════════════════════════════════
        m_som = re.search(r"somme.{1,20}?(\d+[,.]?\d*)", t)
        m_dif = re.search(r"diff[eé]rence.{1,20}?(\d+[,.]?\d*)", t)
        if m_som and m_dif:
            S = float(m_som.group(1).replace(",","."))
            D = float(m_dif.group(1).replace(",","."))
            x, y = sp.symbols("x y")
            sol = solve2(x+y-S, x-y-D, x, y)
            a, b = float(sol[x]), float(sol[y])
            res.append("1. INCONNUES")
            res.append("   x = premier nombre")
            res.append("   y = deuxième nombre")
            res.append("")
            res.append("2. SYSTÈME D'ÉQUATIONS")
            res.append(f"   x + y = {fmt(S)}")
            res.append(f"   x - y = {fmt(D)}")
            res.append("")
            res.append("3. RÉSOLUTION")
            res.append(f"   En additionnant : 2x = {fmt(S+D)}  →  x = {fmt((S+D)/2)}")
            res.append(f"   Donc : y = {fmt(S)} - {fmt((S+D)/2)} = {fmt(b)}")
            res.append("")
            res.append("4. RÉPONSE")
            res.append(f"   Premier nombre  : {fmt(a)}")
            res.append(f"   Deuxième nombre : {fmt(b)}")
            return "\n".join(res)

        # ════════════════════════════════════════════════════════
        # PATTERN 2 : prix unitaires + total  ex: "250 plants A et B, coûte 55000F, A=200F B=250F"
        # ════════════════════════════════════════════════════════
        m_total_items = re.search(r"(\d+)\s*(?:plants?|objets?|articles?|stylos?|cahiers?|bonbons?|sacs?)", t)
        # Trouver tous les montants en F (ex: 55000F, 200F, 250F)
        tous_montants = re.findall(r"(\d+[,.]?\d*)\s*[Ff]", texte)
        if m_total_items and len(tous_montants) >= 3:
            N  = float(m_total_items.group(1))
            PT = float(tous_montants[0].replace(",","."))
            pA = float(tous_montants[1].replace(",","."))
            pB = float(tous_montants[2].replace(",","."))
            x, y = sp.symbols("x y")
            sol = solve2(x+y-N, pA*x+pB*y-PT, x, y)
            a, b = float(sol[x]), float(sol[y])
            res.append("1. INCONNUES")
            res.append("   x = quantité de A")
            res.append("   y = quantité de B")
            res.append("")
            res.append("2. SYSTÈME D'ÉQUATIONS")
            res.append(f"   x + y = {fmt(N)}           (quantités)")
            res.append(f"   {fmt(pA)}x + {fmt(pB)}y = {fmt(PT)}   (prix total)")
            res.append("")
            res.append("3. RÉSOLUTION (substitution)")
            res.append(f"   y = {fmt(N)} - x")
            res.append(f"   {fmt(pA)}x + {fmt(pB)}({fmt(N)}-x) = {fmt(PT)}")
            res.append(f"   {fmt(pA-pB)}x = {fmt(PT - pB*N)}")
            res.append(f"   x = {fmt(a)}")
            res.append(f"   y = {fmt(N)} - {fmt(a)} = {fmt(b)}")
            res.append("")
            res.append("4. RÉPONSE")
            res.append(f"   Quantité A : {fmt(a)}")
            res.append(f"   Quantité B : {fmt(b)}")
            return "\n".join(res)

        # ════════════════════════════════════════════════════════
        # PATTERN 3 : jours de travail + salaire total
        # ex: "ouvrier 25 jours, femme 15 jours, ensemble 42070F"
        # ════════════════════════════════════════════════════════
        m_jours = re.findall(r"(\d+)\s*jours?", t)
        m_total  = re.search(r"(\d+)\s*[Ff]", texte)
        if len(m_jours) >= 2 and m_total:
            j1 = float(m_jours[0]); j2 = float(m_jours[1])
            T  = float(m_total.group(1))
            x, y = sp.symbols("x y")
            # chercher si un salaire individuel est donné
            # sinon : j1*x + j2*y = T avec une 2ème contrainte
            # Si rien d'autre : on suppose salaire journalier
            # Cherche ratio ou deuxième info
            m_ratio = re.search(r"(\d+)\s*fois", t)
            if m_ratio:
                k = float(m_ratio.group(1))
                sol = solve2(j1*x + j2*y - T, x - k*y, x, y)
            else:
                # Cas simple : 1 inconnue — salaire journalier commun
                # ou ouvrier seul gagne X -> chercher X
                m_seul = re.search(r"(?:seul|lui seul|seule).{1,30}?(\d+)", t)
                if m_seul:
                    S = float(m_seul.group(1))
                    x, y = sp.symbols("x y")
                    sol = solve2(j1*x + j2*y - T, j1*x - S, x, y)
                else:
                    # Pas assez d'info — salaire journalier de chacun
                    x, y = sp.symbols("x y")
                    # On ne peut pas résoudre sans 2ème équation
                    # On présente le système
                    res.append("1. INCONNUES")
                    res.append("   x = salaire journalier de la 1ère personne")
                    res.append("   y = salaire journalier de la 2ème personne")
                    res.append("")
                    res.append("2. SYSTÈME D'ÉQUATIONS")
                    res.append(f"   {fmt(j1)}x + {fmt(j2)}y = {fmt(T)}")
                    res.append("")
                    res.append("⚠️  Il manque une 2ème condition pour résoudre.")
                    res.append("   Exemples : 'x = 2y', 'x = 1500F', etc.")
                    return "\n".join(res)

            a, b = float(sol[x]), float(sol[y])
            res.append("1. INCONNUES")
            res.append("   x = salaire journalier personne 1")
            res.append("   y = salaire journalier personne 2")
            res.append("")
            res.append("2. SYSTÈME D'ÉQUATIONS")
            res.append(f"   {fmt(j1)}x + {fmt(j2)}y = {fmt(T)}")
            res.append("")
            res.append("3. RÉSOLUTION")
            res.append(f"   x = {fmt(a)},   y = {fmt(b)}")
            res.append("")
            res.append("4. RÉPONSE")
            res.append(f"   Salaire journalier (1) : {fmt(a)} F")
            res.append(f"   Salaire journalier (2) : {fmt(b)} F")
            res.append(f"   Vérif : {fmt(j1)}×{fmt(a)} + {fmt(j2)}×{fmt(b)} = {fmt(j1*a + j2*b)} F ✓")
            return "\n".join(res)

        # ════════════════════════════════════════════════════════
        # PATTERN 4 : équation simple ax + b = c
        # ════════════════════════════════════════════════════════
        m_eq = re.search(r"([\d.]+)?\s*x\s*([+-]\s*[\d.]+)?\s*=\s*([\d.]+)", texte, re.IGNORECASE)
        if m_eq:
            x = sp.Symbol("x")
            try:
                expr = sp.sympify(texte.split("=")[0].strip())
                rhs  = float(texte.split("=")[1].strip())
                sol  = sp.solve(expr - rhs, x)
                res.append("1. ÉQUATION DÉTECTÉE")
                res.append(f"   {texte.strip()}")
                res.append("")
                res.append("2. RÉSOLUTION")
                res.append(f"   x = {sol[0]}")
                res.append("")
                res.append("4. RÉPONSE")
                res.append(f"   x = {sol[0]}")
                return "\n".join(res)
            except Exception:
                pass

        # ════════════════════════════════════════════════════════
        # FALLBACK : afficher les nombres trouvés et demander plus d'infos
        # ════════════════════════════════════════════════════════
        res.append("⚠️  Je n'ai pas pu identifier le type de problème.")
        res.append("")
        res.append(f"Nombres trouvés dans l'énoncé : {nums}")
        res.append("")
        res.append("Essaie de reformuler en précisant :")
        res.append("  • La somme et la différence de deux nombres")
        res.append("  • Les quantités et prix unitaires de deux objets")
        res.append("  • Les jours de travail et le salaire total")
        return "\n".join(res)


# ══════════════════════════════════════════════════════════
# MODULE 9 — HISTORIQUE
# ══════════════════════════════════════════════════════════
class HistoriqueFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD, padx=14, pady=12)

        top = tk.Frame(self, bg=CARD)
        top.pack(fill="x", pady=(0,8))
        make_btn(top,"🔄 RAFRAÎCHIR", self.refresh, color=BG2, fg=ACCENT
                 ).pack(side="left", padx=(0,6))
        make_btn(top,"💾 EXPORTER .TXT", self.export, color="#1b5e20", fg=TEXT
                 ).pack(side="left", padx=(0,6))
        make_btn(top,"🗑️ VIDER", self.clear, color="#7f0000", fg=TEXT
                 ).pack(side="left")

        rf, self.rt = result_box(self, height=22)
        rf.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        if not HISTORY:
            show_result(self.rt, "  Aucun calcul pour l'instant.\n  Lance des calculs dans les autres onglets !", GRAY)
            return
        lines = ["╔══ HISTORIQUE DES CALCULS ═══════════╗\n"]
        for i, h in enumerate(reversed(HISTORY), 1):
            lines.append(f"  [{h['time']}] {h['module']}")
            lines.append(f"  Entrée  : {h['entree']}")
            lines.append(f"  Résultat: {h['sortie']}")
            lines.append(f"  {'─'*36}")
        lines.append("╚═════════════════════════════════════╝")
        show_result(self.rt, "\n".join(lines))

    def export(self):
        if not HISTORY:
            messagebox.showinfo("Vide","Pas encore de calculs à exporter !"); return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichier texte","*.txt")],
            initialfile="historique_maths.txt")
        if not path: return
        with open(path,"w",encoding="utf-8") as f:
            f.write("HISTORIQUE — CALCULATRICE 3ÈME\n")
            f.write(f"Exporté le {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("="*50+"\n\n")
            for h in HISTORY:
                f.write(f"[{h['time']}] {h['module']}\n")
                f.write(f"Entrée  : {h['entree']}\n")
                f.write(f"Résultat: {h['sortie']}\n")
                f.write("-"*40+"\n")
        messagebox.showinfo("Exporté !",f"Fichier sauvegardé :\n{path}")

    def clear(self):
        if messagebox.askyesno("Vider","Supprimer tout l'historique ?"):
            HISTORY.clear()
            self.refresh()


# ══════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ Calculatrice Ultra")
        self.geometry("820x700")
        self.minsize(750,600)
        self.configure(bg=BG)

        tk.Label(self, text="⚡ CALCULATRICE ULTRA ",
                 font=FONT_TITLE, bg=BG, fg=ACCENT).pack(pady=(10,0))
        tk.Label(self, text="POWERED BY SYMPY + MATPLOTLIB · MATHÉMATIQUES AVANCÉES",
                 font=("Courier",7), bg=BG, fg=GRAY).pack(pady=(0,6))

        tab_bar = tk.Frame(self, bg=BG)
        tab_bar.pack(fill="x", padx=8, pady=2)

        self.tabs = [
            ("🧮 Sci.",         ScientifiqueFrame),
            ("📐 Géométrie",    GeometrieFrame),
            ("📈 Affine",       AffineGraphFrame),
            ("✏️ Algèbre",      AlgebreFrame),
            ("🔣 Équations",    EquationFrame),
            ("🔢 Système",      SystemeFrame),
            ("📊 Stats",        StatsFrame),
            ("🤖 Texte→Éq.",   TexteEquationFrame),
            ("📋 Historique",   HistoriqueFrame),
        ]
        self.btns = []
        for i,(label,_) in enumerate(self.tabs):
            b = tk.Button(tab_bar, text=label, font=FONT_TAB,
                          bg=BG2, fg=GRAY, relief="flat", padx=6, pady=4,
                          cursor="hand2", command=lambda i=i: self.show(i))
            b.pack(side="left", padx=1)
            self.btns.append(b)

        content = tk.Frame(self, bg=BG, padx=8, pady=6)
        content.pack(fill="both", expand=True)
        self.frames = []
        for _,FC in self.tabs:
            f = FC(content)
            f.place(relwidth=1, relheight=1)
            self.frames.append(f)

        self.show(0)

    def show(self, idx):
        for i,b in enumerate(self.btns):
            b.config(bg=ACCENT if i==idx else BG2,
                     fg="#000" if i==idx else GRAY)
        if idx == 8:  # Historique
            self.frames[8].refresh()
        self.frames[idx].tkraise()


if __name__ == "__main__":
    App().mainloop()
