# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np

st.set_page_config(page_title="Calcolo Forza Pinza Robot", layout="centered")

st.title("🤖 Calcolo Forza Necessaria per Pinza Robot")
st.caption("Modello semplificato con attrito secco. Output: forza per dito e forza totale pinza.")

# ----------------------------
# Preset materiali (attrito)
# ----------------------------
MU_PRESETS = {
    "Acciaio su acciaio": 0.15,
    "Alluminio su acciaio": 0.30,
    "Gomma su acciaio (zigrinato)": 0.8,
    "Poliuretano su acciaio": 0.5,
    "Carta vetrata su acciaio": 1.0,
    "Personalizzato": None,
}

# ============================
#  PARAMETRI IN TESTATA
# ============================
st.subheader("Parametri di input")

# Riga 1: massa, g, a
c1, c2, c3, c4 = st.columns(4)
with c1:
    m = st.number_input("Massa oggetto m [kg]", min_value=0.0, value=2.0, step=0.1, format="%.3f")
with c2:
    g = st.number_input("Gravità g [m/s²]", min_value=0.0, value=9.81, step=0.01, format="%.2f")
with c3:
    a = st.number_input("Accel. verticale [m/s²]", value=0.0, step=0.1, format="%.2f")
with c4:
    SF = st.number_input("Fattore di sicurezza SF [-]", min_value=1.0, value=2.0, step=0.1, format="%.1f")

# Riga 2: dita, materiale/μ
c5, c6, c7 = st.columns([1, 2, 1])
with c5:
    n_contacts = st.selectbox("Dita / contatti", [2, 3, 4], index=0)
with c6:
    mu_key = st.selectbox("Coppia materiali (coefficiente μ)", list(MU_PRESETS.keys()), index=0)
with c7:
    if MU_PRESETS[mu_key] is None:
        mu = st.number_input("μ personalizzato [-]", min_value=0.01, value=0.60, step=0.01, format="%.2f")
    else:
        mu = MU_PRESETS[mu_key]

# Riga 3: momento (opzionale) in expander ma sempre in alto
with st.expander("Baricentro fuori asse (rotazione) – opzionale"):
    st.caption(
        "Se il baricentro non è allineato al piano di presa, serve vincere un **momento**. "
        "Si usa un **braccio d'attrito efficace** r_eff che dipende da pad e conformità."
    )
    use_moment = st.checkbox("Considera effetto momento", value=False)
    colM1, colM2 = st.columns(2)
    if use_moment:
        with colM1:
            e = st.number_input("Offset baricentro e [mm]", value=20.0, step=1.0)
        with colM2:
            r_eff = st.number_input("Braccio d'attrito efficace r_eff [mm]", value=10.0, step=0.5)
    else:
        e, r_eff = 0.0, 1.0  # dummy

st.markdown("---")

# ============================
#  CALCOLI
# ============================
W = m * (g + a)          # N
W = max(W, 0.0)

# Requisito traslazionale
N_req_transl = (W * SF) / (n_contacts * mu) if mu > 0 else np.inf

# Requisito rotazionale (se attivo)
if use_moment:
    e_m = e / 1000.0
    r_m = max(r_eff, 1e-6) / 1000.0
    N_req_rot = (W * e_m * SF) / (n_contacts * mu * r_m) if (mu > 0 and r_m > 0) else np.inf
else:
    N_req_rot = 0.0

N_per_contact = max(N_req_transl, N_req_rot)
N_total = N_per_contact * n_contacts

# ============================
#  OUTPUT
# ============================
st.subheader("Risultati")
top1, top2, top3 = st.columns(3)
top1.metric("Carico effettivo W [N]", f"{W:.1f}")
top2.metric("μ", f"{mu:.2f}")
top3.metric("Dita/contatti", f"{n_contacts}")

o1, o2 = st.columns(2)
o1.metric("Per contatto Fᵢ [N]", f"{N_per_contact:.1f}")
o2.metric("Totale pinza ΣF [N]", f"{N_total:.1f}")

with st.expander("Dettaglio calcoli e formule"):
    st.markdown(
        f"""
- **Traslazione**:  
  \\( \\sum F_\\text{{attr}} = n\\,\\mu\\,N_i \\ge SF\\,W \\Rightarrow N_i \\ge \\frac{{SF\\,W}}{{n\\,\\mu}} \\)  
  → **Nᵢ,transl = {N_req_transl:.1f} N**
  
- **Rotazione** {'(considerata)' if use_moment else '(non considerata)'}:  
  \\( M_g = W\\,e \\) con *e* in metri,  
  \\( M_\\max \\approx n\\,\\mu\\,N_i\\,r_\\text{{eff}} \\Rightarrow N_i \\ge \\frac{{SF\\,W\\,e}}{{n\\,\\mu\\,r_\\text{{eff}}}} \\)  
  → **Nᵢ,rot = {N_req_rot:.1f} N**
  
- **Requisito totale**: \\( N_i = \\max(N_i^{{transl}},\\,N_i^{{rot}}) \\), **ΣN = n·Nᵢ**
        """
    )

st.divider()
st.subheader("Linee guida rapide")
st.markdown(
    """
- Se **slitta**: aumenta **μ**, **SF** o la **forza pinza**.  
- Se l’oggetto **ruota** in presa, indica **e** (offset) e un **r_eff** realistico.  
- Tipici **μ**: gomma 0.7–0.9, PU 0.4–0.6, acciaio liscio 0.15–0.25.
"""
)

st.caption("Modello semplificato per prese frizionali. Validare con test per applicazioni critiche.")
