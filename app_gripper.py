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
    "Gomma su acciaio (zigrinato)": 0.8,
    "Poliuretano su acciaio": 0.5,
    "Alluminio su acciaio": 0.30,
    "Acciaio liscio su acciaio": 0.20,
    "Carta vetrata su acciaio": 1.0,
    "Personalizzato": None,
}

with st.sidebar:
    st.header("Impostazioni")
    st.markdown("**Unità:** SI (kg, m, s, N).")
    st.markdown("**Assunzioni:** presa puramente **frizionale** (senza incastri).")

    # --- Dati oggetto/dinamica ---
    m = st.number_input("Massa oggetto m [kg]", min_value=0.0, value=2.0, step=0.1, format="%.3f")
    g = st.number_input("Gravità g [m/s²]", min_value=0.0, value=9.81, step=0.01, format="%.2f")
    a = st.number_input("Accel. verticale extra a [m/s²] (sollevamento/urti)", value=0.0, step=0.1, format="%.2f")
    SF = st.number_input("Fattore di sicurezza SF [-]", min_value=1.0, value=2.0, step=0.1, format="%.1f")

    # --- Pinza ---
    n_contacts = st.selectbox("Numero dita / contatti attivi", [2, 3], index=0)

    # --- Attrito ---
    mu_key = st.selectbox("Coppia materiali (coefficiente μ)", list(MU_PRESETS.keys()), index=0)
    if MU_PRESETS[mu_key] is None:
        mu = st.number_input("μ personalizzato [-]", min_value=0.01, value=0.60, step=0.01, format="%.2f")
    else:
        mu = MU_PRESETS[mu_key]

    # --- Momento da baricentro fuori asse (opzionale) ---
    st.divider()
    st.subheader("Baricentro fuori asse (rotazione) – opzionale")
    st.caption(
        "Se il baricentro non è allineato al piano di presa, serve anche vincere un **momento**.\n"
        "Usiamo un braccio d'attrito efficace r_eff (mm) che rappresenta quanto il contatto può generare momento "
        "prima di slittare (dipende da altezza pad, conformità, zigrinatura, gomma ecc.)."
    )
    use_moment = st.checkbox("Considera effetto momento", value=False)
    if use_moment:
        e = st.number_input("Offset baricentro e [mm] (distanza orizzontale dal piano medio di presa)", value=20.0, step=1.0)
        r_eff = st.number_input("Braccio d'attrito efficace r_eff [mm] (tipico 5–15 per pad piatti)", value=10.0, step=0.5)
    else:
        e, r_eff = 0.0, 1.0  # r_eff dummy per evitare divisioni per zero

# ------------------------------------------------
# Calcoli
# ------------------------------------------------
W = m * (g + a)  # N, carico "effettivo" da sostenere (peso + dinamica)
W = max(W, 0.0)

# 1) Requisito traslazionale (no rotazione): somma attriti ≥ W*SF
# Somma attriti = n_contacts * μ * N_contatto.
# => N_req_transl_per_contatto = (W * SF) / (n_contacts * μ)
N_req_transl = (W * SF) / (n_contacts * mu) if mu > 0 else np.inf

# 2) Requisito rotazionale (se baricentro fuori asse)
# Momento da vincere: M_g = W * e, con e in metri.
# Momento frizionale disponibile (approssimazione "soft contact"):
#   M_fric_max ≈ n_contacts * μ * N_contatto * r_eff
# con r_eff in metri. => N_req_rot_per_contatto = (W*e*SF) / (n_contacts * μ * r_eff)
if use_moment:
    e_m = e / 1000.0       # mm -> m
    r_m = max(r_eff, 1e-6) / 1000.0
    N_req_rot = (W * e_m * SF) / (n_contacts * mu * r_m) if (mu > 0 and r_m > 0) else np.inf
else:
    N_req_rot = 0.0

# Requisito complessivo per contatto
N_per_contact = max(N_req_transl, N_req_rot)
N_total = N_per_contact * n_contacts

# ------------------------------------------------
# Output
# ------------------------------------------------
st.subheader("Risultati")
c1, c2, c3 = st.columns(3)
c1.metric("Carico effettivo W [N]", f"{W:.1f}")
c2.metric("μ", f"{mu:.2f}")
c3.metric("Dita/contatti", f"{n_contacts}")

st.write("**Forza minima richiesta**")
o1, o2 = st.columns(2)
o1.metric("Per contatto Nᵢ [N]", f"{N_per_contact:.1f}")
o2.metric("Totale pinza ΣN [N]", f"{N_total:.1f}")

with st.expander("Dettaglio calcoli e formule"):
    st.markdown(
        f"""
- **Traslazione**:  
  \\( \\sum F_\\text{{attr}} = n \\mu N_i \\ge SF \\cdot W \\Rightarrow N_i \\ge \\frac{{SF\\,W}}{{n\\,\\mu}} \\)  
  → **Nᵢ,transl = {N_req_transl:.1f} N**
  
- **Rotazione** {'(considerata)' if use_moment else '(non considerata)'}:  
  \\( M_g = W \\cdot e \\)  con *e* in metri  
  \\( M_\\max \\approx n \\mu N_i r_\\text{{eff}} \\Rightarrow N_i \\ge \\frac{{SF\\,W\\,e}}{{n\\,\\mu\\,r_\\text{{eff}}}} \\)  
  → **Nᵢ,rot = {N_req_rot:.1f} N**
  
- **Requisito totale**: \\( N_i = \\max(N_i^{{transl}}, N_i^{{rot}}) \\), **ΣN = n·Nᵢ**
        """
    )

st.divider()
st.subheader("Linee guida rapide")
st.markdown(
    """
- Se **slitta**: aumenta **μ**, **SF** o la **forza pinza**.  
- Se l’oggetto **ruota** in presa, indica **e** (offset baricentro) e un **r_eff** realistico (maggiore con pad più alti/morbidi).  
- Tipici **μ**:
  - Gomma su acciaio 0.7–0.9
  - Poliuretano 0.4–0.6
  - Acciaio liscio 0.15–0.25
"""
)

st.caption("Modello semplificato per prese frizionali. Per componenti critici, validare con test e fattori normativi aziendali.")
