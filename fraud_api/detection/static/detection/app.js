// Interface de test du modèle de détection de fraude (appelle l'API Django).
(() => {
  "use strict";

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const fr = (x, d = 2) => Number(x).toLocaleString("fr-FR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const heureTexte = (t) => {
    const h = (t % 86400) / 3600;
    return `${String(Math.floor(h)).padStart(2, "0")} h ${String(Math.floor((h % 1) * 60)).padStart(2, "0")}`;
  };
  const echapper = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  let seuils = { alerte: 0.233, blocage: 0.614 };
  let classeReelle = null;
  let scoreAffiche = 0;

  // ---------- Statut et appels à l'API ----------
  function statut(texte, etat = "ok") {
    const el = $("#statut");
    el.className = `statut ${etat}`;
    el.querySelector("span").textContent = texte;
  }

  async function api(url, options) {
    const reponse = await fetch(url, options);
    const donnees = await reponse.json().catch(() => ({}));
    if (!reponse.ok) throw new Error(donnees.erreur || `Erreur ${reponse.status}`);
    return donnees;
  }

  function occupe(oui) {
    $$("button[data-exemple], #analyser, #rejouer").forEach((b) => (b.disabled = oui));
    $("#fichier").disabled = oui;
  }

  async function tache(message, fonction) {
    occupe(true);
    statut(message, "travail");
    try {
      await fonction();
      statut("Modèle prêt");
    } catch (e) {
      statut("Erreur", "erreur");
      alert(e.message);
    } finally {
      occupe(false);
    }
  }

  // ---------- Onglets ----------
  $$(".onglet").forEach((b) => b.addEventListener("click", () => {
    $$(".onglet").forEach((o) => o.classList.toggle("actif", o === b));
    $$(".panneau").forEach((p) => p.classList.toggle("actif", p.id === b.dataset.cible));
  }));

  // ---------- Jauge (SVG) ----------
  const CX = 190, CY = 168, R = 130;
  const point = (s, r = R) => {
    const a = Math.PI * (1 - s);
    return [CX + r * Math.cos(a), CY - r * Math.sin(a)];
  };
  const arc = (s1, s2, r = R) => {
    const [x1, y1] = point(s1, r), [x2, y2] = point(s2, r);
    return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${r} ${r} 0 0 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
  };
  const couleurScore = (s) => (s < seuils.alerte ? "#16a34a" : s < seuils.blocage ? "#d97706" : "#dc2626");

  function dessinerJauge(score, vide = false) {
    const { alerte: sa, blocage: sb } = seuils;
    let svg = "";
    [[0, sa, "#86efac"], [sa, sb, "#fcd34d"], [sb, 1, "#fca5a5"]].forEach(([d, f, c]) => {
      svg += `<path d="${arc(d, f)}" fill="none" stroke="${c}" stroke-width="22"/>`;
    });
    if (!vide && score > 0.002) {
      svg += `<path d="${arc(0, Math.min(score, 0.999))}" fill="none" stroke="${couleurScore(score)}" stroke-width="8" stroke-linecap="round"/>`;
    }
    [sa, sb].forEach((s) => {
      const [x1, y1] = point(s, R + 15), [x2, y2] = point(s, R - 15), [xt, yt] = point(s, R + 28);
      svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#0f172a" stroke-width="2"/>`;
      svg += `<text x="${xt}" y="${yt}" font-size="11" fill="#64748b" text-anchor="middle" dominant-baseline="middle">${fr(s, 2)}</text>`;
    });
    svg += `<text x="${CX - R}" y="${CY + 24}" font-size="12" fill="#94a3b8" text-anchor="middle">0</text>`;
    svg += `<text x="${CX + R}" y="${CY + 24}" font-size="12" fill="#94a3b8" text-anchor="middle">1</text>`;
    if (vide) {
      svg += `<text x="${CX}" y="${CY - 30}" font-size="40" font-weight="600" fill="#94a3b8" text-anchor="middle">—</text>`;
    } else {
      const [xa, ya] = point(score, R - 26);
      svg += `<line x1="${CX}" y1="${CY}" x2="${xa}" y2="${ya}" stroke="#0f172a" stroke-width="4" stroke-linecap="round"/>`;
      svg += `<circle cx="${CX}" cy="${CY}" r="8" fill="#0f172a"/>`;
      svg += `<text x="${CX}" y="${CY - 48}" font-size="34" font-weight="600" fill="${couleurScore(score)}" text-anchor="middle">${fr(score * 100, 1)} %</text>`;
    }
    svg += `<text x="${CX}" y="${CY + 30}" font-size="14" fill="#64748b" text-anchor="middle">score de fraude</text>`;
    $("#jauge").innerHTML = svg;
  }

  function animerJauge(cible) {
    const depart = scoreAffiche, debut = performance.now(), duree = 450;
    const etape = (t) => {
      const p = Math.min(1, (t - debut) / duree), e = 1 - Math.pow(1 - p, 3);
      dessinerJauge(depart + (cible - depart) * e);
      if (p < 1) requestAnimationFrame(etape); else scoreAffiche = cible;
    };
    requestAnimationFrame(etape);
  }

  // ---------- Formulaire ----------
  const champs = () => $$("#formulaire input");

  function lireFormulaire() {
    const transaction = {};
    let premierInvalide = null;
    champs().forEach((input) => {
      const texte = input.value.trim().replace(",", ".").replace(/\s/g, "");
      const valeur = Number(texte);
      const ok = texte !== "" && Number.isFinite(valeur);
      input.classList.toggle("invalide", !ok);
      if (!ok && !premierInvalide) premierInvalide = input;
      transaction[input.name] = valeur;
    });
    if (premierInvalide) {
      premierInvalide.focus();
      throw new Error(`Le champ ${premierInvalide.name === "Amount" ? "Montant" : premierInvalide.name} est vide ou n'est pas un nombre. Remplissez tous les champs ou chargez un exemple.`);
    }
    return transaction;
  }

  function majHeure() {
    const t = Number($("input[name=Time]").value.replace(",", "."));
    $("#heure").textContent = $("input[name=Time]").value.trim() !== "" && Number.isFinite(t) && t >= 0
      ? `→ ${heureTexte(t)} (jour ${Math.floor(t / 86400) + 1})` : "";
  }

  function reinitialiserResultat() {
    scoreAffiche = 0;
    dessinerJauge(0, true);
    $("#badge").className = "badge";
    $("#badge").textContent = "En attente";
    $("#detail").textContent = "Cliquez sur « Analyser la transaction ».";
    $("#realite").className = "realite";
    $("#realite").textContent = "";
    $("#explication").innerHTML = `<p class="vide">Les variables qui ont le plus pesé s'afficheront ici.</p>`;
    $("#explication-texte").textContent = "Contribution de chaque variable au score (valeurs SHAP).";
  }

  champs().forEach((input) => input.addEventListener("input", () => {
    input.classList.remove("invalide");
    if (input.name === "Time") majHeure();
    if (classeReelle !== null) {
      classeReelle = null;
      $("#source").textContent = "Valeurs modifiées à la main : la réalité n'est plus connue.";
    }
  }));

  $$("button[data-exemple]").forEach((b) => b.addEventListener("click", () =>
    tache("Chargement d'une transaction…", async () => {
      const { transaction, classe_reelle } = await api(`api/exemple/?type=${b.dataset.exemple}`);
      champs().forEach((input) => {
        const v = transaction[input.name];
        input.value = input.name === "Amount" ? v.toFixed(2) : input.name === "Time" ? v.toFixed(0) : v.toFixed(6);
        input.classList.remove("invalide");
      });
      classeReelle = classe_reelle;
      majHeure();
      $("#source").textContent = "Vraie transaction de la période de test. La réalité s'affichera après l'analyse.";
      reinitialiserResultat();
    })));

  $("#effacer").addEventListener("click", () => {
    champs().forEach((i) => { i.value = ""; i.classList.remove("invalide"); });
    classeReelle = null;
    $("#source").textContent = "";
    majHeure();
    reinitialiserResultat();
  });

  $("#formulaire").addEventListener("submit", (e) => {
    e.preventDefault();
    let transaction;
    try { transaction = lireFormulaire(); } catch (err) { alert(err.message); return; }
    const classe = classeReelle;
    tache("Analyse en cours…", async () => {
      const r = await api("api/predire/", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(transaction),
      });
      afficherResultat(r, classe);
    });
  });

  function afficherResultat(r, classe) {
    animerJauge(r.score);
    $("#badge").className = `badge ${r.decision}`;
    $("#badge").textContent = r.libelle.toUpperCase();
    $("#detail").textContent = r.detail;
    const realite = $("#realite");
    if (classe === null) {
      realite.className = "realite inconnue";
      realite.textContent = "Réalité inconnue (valeurs saisies à la main)";
    } else {
      const alerte = r.decision !== "accepter", juste = alerte === (classe === 1);
      const reel = classe === 1 ? "FRAUDE" : "transaction NORMALE";
      realite.className = `realite ${juste ? "juste" : "faux"}`;
      realite.textContent = juste ? `✓ Bonne réponse — en réalité : ${reel}`
        : classe === 1 ? `✗ Fraude ratée — en réalité : ${reel}` : `✗ Fausse alerte — en réalité : ${reel}`;
    }
    afficherExplication(r.explication);
  }

  function afficherExplication(expl) {
    const zone = $("#explication");
    if (!expl) {
      zone.innerHTML = `<p class="vide">Explication indisponible (le paquet shap n'est pas installé).</p>`;
      return;
    }
    const contributions = expl.contributions.slice(0, 6);
    const maxi = Math.max(0.05, ...contributions.map((c) => Math.abs(c.contribution)));
    zone.innerHTML = contributions.map((c, i) => {
      const positif = c.contribution > 0, sens = positif ? "positif" : "negatif";
      const largeur = (50 * Math.abs(c.contribution) / maxi).toFixed(1);
      const valeur = fr(c.valeur, 2) + (c.variable === "Montant" ? " €" : "");
      return `<div class="barre"><span class="nom">${echapper(c.variable)} = ${valeur}</span>
        <span class="piste"><span class="remplissage ${sens}" style="width:${largeur}%;animation-delay:${i * 40}ms"></span></span>
        <span class="val ${sens}">${positif ? "+" : "−"}${fr(Math.abs(c.contribution), 3)}</span></div>`;
    }).join("") + `<div class="legende"><span></span><span><b class="n">← vers « normale »</b><b class="f">vers « fraude » →</b></span><span></span></div>`;
    $("#explication-texte").textContent =
      `Score moyen de départ : ${fr(expl.base, 3)}. Chaque variable l'augmente (rouge) ou le diminue (vert).`;
  }

  // ---------- Lot ----------
  function afficherLot(d) {
    const r = d.resume;
    $("#lot-source").textContent = d.source;
    const tuiles = [["Transactions", fr(r.transactions, 0), "#0f172a"], ["Acceptées", fr(r.accepter, 0), "#16a34a"],
      ["À vérifier", fr(r.verifier, 0), "#d97706"], ["Bloquées", fr(r.bloquer, 0), "#dc2626"]];
    if (r.fraudes !== undefined) {
      tuiles.push(["Fraudes détectées", `${r.fraudes_detectees} / ${r.fraudes}`, "#4f46e5"],
        ["Recall", r.fraudes ? `${fr(100 * r.fraudes_detectees / r.fraudes, 1)} %` : "—", "#4f46e5"],
        ["Fausses alertes", fr(r.fausses_alertes, 0), "#64748b"]);
    }
    $("#tuiles").innerHTML = tuiles.map(([t, v, c]) =>
      `<div class="tuile"><small>${t}</small><strong style="color:${c}">${v}</strong></div>`).join("");
    const cle = { "Accepter": "accepter", "Vérifier": "verifier", "Bloquer": "bloquer" };
    $("#tableau").innerHTML = d.lignes.map((l, i) => `<tr class="${cle[l.decision]}"><td>${i + 1}</td>
      <td>${heureTexte(l.time)}</td><td class="d">${fr(l.montant)} €</td><td>${fr(l.score, 3)}</td>
      <td>${l.decision}</td><td>${l.realite ?? "—"}</td></tr>`).join("");
    $("#titre-tableau").hidden = false;
    $("#tableau-cadre").hidden = false;
  }

  $("#rejouer").addEventListener("click", () => tache("Analyse de la période de test…", async () => {
    const corps = new FormData();
    corps.append("source", "test");
    afficherLot(await api("api/lot/", { method: "POST", body: corps }));
  }));

  $("#fichier").addEventListener("change", (e) => {
    const fichier = e.target.files[0];
    if (!fichier) return;
    tache("Analyse du fichier…", async () => {
      const corps = new FormData();
      corps.append("fichier", fichier);
      afficherLot(await api("api/lot/", { method: "POST", body: corps }));
    }).finally(() => { e.target.value = ""; });
  });

  // ---------- Fiche du modèle ----------
  function remplirCles(selecteur, lignes) {
    $(selecteur).innerHTML = lignes.map(([k, v]) => `<dt>${k}</dt><dd>${echapper(v)}</dd>`).join("");
  }

  async function demarrer() {
    dessinerJauge(0, true);
    occupe(true);
    try {
      const infos = await api("api/modele/");
      seuils = { alerte: infos.seuil_alerte, blocage: infos.seuil_blocage };
      dessinerJauge(0, true);
      $("#modele-resume").textContent = `${infos.nom_modele} · ${infos.strategie_desequilibre}\nalerte ≥ ${fr(seuils.alerte, 3)} · blocage ≥ ${fr(seuils.blocage, 3)}`;
      const h = infos.hyperparametres, m = infos.metriques_test, ic = infos.intervalles_confiance_95 || {};
      const avecIc = (n) => `${fr(m[n] * 100, 1)} %` + (ic[n] ? `   (IC 95 % : ${fr(ic[n][0] * 100, 0)} – ${fr(ic[n][1] * 100, 0)} %)` : "");
      remplirCles("#infos-modele", [
        ["Algorithme", infos.nom_modele], ["Gestion du déséquilibre", infos.strategie_desequilibre],
        ["Nombre d'arbres", h.model__n_estimators ?? "—"], ["Profondeur maximale", h.model__max_depth ?? "—"],
        ["Seuil d'alerte (vérifier)", fr(seuils.alerte, 3)], ["Seuil de blocage", fr(seuils.blocage, 3)],
        ["Période d'entraînement", `${fr(infos.periode_entrainement_heures[0], 0)} h à ${fr(infos.periode_entrainement_heures[1], 1)} h`],
        ["Coût d'une vérification", `${fr(infos.hypotheses.cout_verification_eur, 0)} €`],
        ["Capacité de vérification", `${infos.hypotheses.capacite_alertes_jour} alertes / jour`],
        ["Date d'export", String(infos.date).replace("T", " à ")],
      ]);
      remplirCles("#infos-test", [
        ["Fraudes détectées", `${m.TP} sur ${m.TP + m.FN}`], ["Recall", avecIc("Recall")], ["Precision", avecIc("Precision")],
        ["Fausses alertes", `${m.FP} sur ${fr(m.FP + m.TN, 0)} transactions normales`],
        ["PR-AUC", fr(m["PR-AUC"], 3)], ["ROC-AUC", fr(m["ROC-AUC"], 3)],
        ["Alertes par jour", fr(m["Alertes / jour"], 0)], ["Coût total (pertes + vérifications)", `${fr(m["Coût total (€)"], 0)} €`],
      ]);
      statut("Modèle prêt");
      occupe(false);
    } catch (e) {
      statut("Modèle indisponible", "erreur");
      alert(`Impossible de charger le modèle : ${e.message}`);
    }
  }

  demarrer();
})();
