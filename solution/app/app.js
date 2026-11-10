/* App estático. Não calcula nada: filtra, ordena por campos já exportados e exibe.
   Todo número e todo texto vêm de window.SCORES (gerado por `python run.py export`). */
(function () {
  "use strict";
  var D = window.SCORES;
  var view = document.getElementById("view");
  if (!D) { view.textContent = "data.js não encontrado. Rode: python run.py export"; return; }

  // ---- formatação (só apresentação) ---------------------------------------
  var nf = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
  var money = function (x) { return "US$ " + nf.format(x); };
  var pct = function (x, d) { return (x * 100).toFixed(d == null ? 0 : d).replace(".", ","); };
  var signed = function (x) { return (x >= 0 ? "+" : "−") + pct(Math.abs(x), 1) + "%"; };
  var dateBR = function (iso) { var p = iso.split("-"); return p[2] + "/" + p[1] + "/" + p[0]; };
  var NO_ACC = "conta não cadastrada";

  // ---- helpers de DOM ------------------------------------------------------
  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    for (var k in (attrs || {})) {
      if (k === "class") e.className = attrs[k];
      else if (k === "text") e.textContent = attrs[k];
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== false && attrs[k] != null) e.setAttribute(k, attrs[k]);
    }
    [].concat(kids || []).forEach(function (c) {
      if (c == null || c === false) return;
      e.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return e;
  }

  // ---- estado --------------------------------------------------------------
  var S = { tab: "vendedor", region: "", manager: "", agent: "Zane Levy", queue: "Agir", shown: 20,
            sort: { key: "expected_value_sum", dir: "descending" } };
  var agentsByName = {};
  D.agents.forEach(function (a) { agentsByName[a.sales_agent] = a; });
  if (!agentsByName[S.agent]) S.agent = D.agents[0].sales_agent;

  function uniq(a) { return a.filter(function (v, i) { return a.indexOf(v) === i; }).sort(); }
  function visibleAgents() {
    return D.agents.filter(function (a) {
      return (!S.region || a.regional_office === S.region) && (!S.manager || a.manager === S.manager);
    });
  }

  // ---- filtros encadeados --------------------------------------------------
  var fRegion = document.getElementById("f-region");
  var fManager = document.getElementById("f-manager");
  var fAgent = document.getElementById("f-agent");

  function fill(sel, opts, value, allLabel) {
    sel.textContent = "";
    if (allLabel) sel.appendChild(h("option", { value: "", text: allLabel }));
    opts.forEach(function (o) { sel.appendChild(h("option", { value: o, text: o })); });
    sel.value = value;
  }

  function syncFilters() {
    fill(fRegion, uniq(D.agents.map(function (a) { return a.regional_office; })), S.region, "Todas");
    var mans = uniq(D.agents.filter(function (a) { return !S.region || a.regional_office === S.region; })
      .map(function (a) { return a.manager; }));
    if (S.manager && mans.indexOf(S.manager) < 0) S.manager = "";
    fill(fManager, mans, S.manager, "Todos");
    var names = visibleAgents().map(function (a) { return a.sales_agent; }).sort();
    if (S.tab === "vendedor") {
      if (names.indexOf(S.agent) < 0) S.agent = names[0] || "";
      fill(fAgent, names, S.agent);
    } else {
      if (S.agent && names.indexOf(S.agent) < 0) S.agent = "";
      fill(fAgent, names, S.agent, "Todos");
    }
  }
  fRegion.addEventListener("change", function () { S.region = fRegion.value; S.agent = S.tab === "vendedor" ? S.agent : ""; S.shown = 20; render(); });
  fManager.addEventListener("change", function () { S.manager = fManager.value; S.agent = S.tab === "vendedor" ? S.agent : ""; S.shown = 20; render(); });
  fAgent.addEventListener("change", function () { S.agent = fAgent.value; S.shown = 20; render(); });

  // ---- abas ----------------------------------------------------------------
  var tabBtns = [].slice.call(document.querySelectorAll(".tabs button"));
  tabBtns.forEach(function (b) {
    b.addEventListener("click", function () { go(b.getAttribute("data-tab")); });
    b.addEventListener("keydown", function (ev) {
      var i = tabBtns.indexOf(b), n = ev.key === "ArrowRight" ? i + 1 : ev.key === "ArrowLeft" ? i - 1 : null;
      if (n == null) return;
      var t = tabBtns[(n + tabBtns.length) % tabBtns.length]; t.focus(); go(t.getAttribute("data-tab"));
    });
  });
  var lastAgent = S.agent;
  function go(tab) {
    if (S.tab === "vendedor" && S.agent) lastAgent = S.agent;
    S.tab = tab; S.shown = 20;
    S.agent = tab === "vendedor" ? (S.agent || lastAgent) : (S.tab === "gestor" && S.agent === lastAgent ? "" : S.agent);
    render();
  }
  document.getElementById("asof").textContent = "base de " + dateBR(D.as_of);

  // ---- vendedor ------------------------------------------------------------
  function kpi(label, value, note) {
    return h("div", { class: "kpi" }, [h("div", { class: "l", text: label }), h("div", { class: "v", text: value }),
      h("div", { class: "n", text: note || " " })]);
  }

  var QHELP = {
    Agir: "Deals vivos, do maior valor esperado para o menor.",
    Qualificar: "Deals em prospecção, sem data de início. Faça o primeiro contato.",
    Decidir: "Deals além do limite histórico de " + D.wall_days + " dias. Reative com data ou dê como perdidos."
  };

  function ageBar(age) {
    var W = D.wall_days, MAX = W + 30;
    var seg = [[0, 90, "var(--green)"], [90, 120, "var(--amber)"], [120, W, "var(--red)"], [W, MAX, "var(--gray)"]];
    var track = h("div", { class: "track", role: "img",
      "aria-label": "Idade de " + age + " dias; limite histórico de " + W + " dias" },
      seg.map(function (s) { return h("i", { style: "width:" + ((s[1] - s[0]) / MAX * 100) + "%;background:" + s[2] }); }));
    track.appendChild(h("span", { class: "marker", style: "left:" + (Math.min(age, MAX) / MAX * 100) + "%" }));
    return h("div", { class: "age" }, [track, h("div", { class: "lbl" }, [
      h("span", { text: age + " dias" }), h("span", { text: "limite: " + W + " dias" })])]);
  }

  function dealCard(d) {
    var acc = d.account || NO_ACC;
    var isAgir = d.queue === "Agir";
    var head = h("div", { class: "head" }, [
      h("div", {}, [h("span", { class: "rank", text: "#" + d.rank_in_agent }),
        h("span", { class: "title", text: d.account ? d.product + " · " + d.account : d.product }),
        d.account ? null : h("span", { class: "tag", text: NO_ACC })]),
      h("div", { class: "ev" }, [h("b", { text: money(isAgir ? d.expected_value : d.sales_price) }),
        h("span", { text: isAgir ? "esperados em 90 dias" : "a preço de lista" })])
    ]);
    return h("article", { class: "card", "aria-label": d.product + " · " + acc }, [
      head,
      d.age != null ? ageBar(d.age) : null,
      h("p", { class: "reason", text: d.reason }),
      h("div", { class: "next" }, [h("strong", { text: "Próximo passo: " }), d.action]),
      h("div", { class: "code" }, ["cód ", h("code", { text: d.opportunity_id })])
    ]);
  }

  function copy(text, btn) {
    function done() { var o = btn.textContent; btn.textContent = "Copiado ✓"; setTimeout(function () { btn.textContent = o; }, 1800); }
    function fallback() {
      var t = h("textarea", { style: "position:fixed;opacity:0" }); t.value = text; document.body.appendChild(t);
      t.select(); try { document.execCommand("copy"); done(); } catch (e) { btn.textContent = "Selecione e copie"; }
      document.body.removeChild(t);
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, fallback); else fallback();
  }

  function bubble(text) {
    var b = h("div", { class: "bubble", tabindex: "0", role: "region", "aria-label": "Mensagem de WhatsApp" });
    text.split(/(\*[^*]+\*)/).forEach(function (p) {
      b.appendChild(/^\*[^*]+\*$/.test(p) ? h("strong", { text: p.slice(1, -1) }) : document.createTextNode(p));
    });
    return b;
  }

  function renderVendedor() {
    var a = agentsByName[S.agent];
    if (!a) { view.appendChild(h("div", { class: "empty", text: "Nenhum vendedor para esses filtros." })); return; }
    var first = a.sales_agent.split(" ")[0];
    view.appendChild(h("h1", { text: "Bom dia, " + first + "." }));
    view.appendChild(h("p", { class: "sub", text: "Sua semana, com base em " + dateBR(D.as_of) + " · " + a.manager + " · " + a.regional_office }));
    view.appendChild(h("div", { class: "kpis" }, [
      kpi("Deals vivos", nf.format(a.alive), "fila Agir"),
      kpi("Valor esperado (90 dias)", money(a.expected_value_sum), "soma da fila Agir"),
      kpi("Para decidir", nf.format(a.decide_count), money(a.decide_value) + " parados"),
      kpi("Para qualificar", nf.format(a.qualify_count), "sem primeiro contato")
    ]));

    var counts = { Agir: a.alive, Qualificar: a.qualify_count, Decidir: a.decide_count };
    var qt = h("div", { class: "qtabs", role: "tablist", "aria-label": "Filas" },
      ["Agir", "Qualificar", "Decidir"].map(function (q) {
        return h("button", { role: "tab", "aria-selected": String(S.queue === q), onclick: function () { S.queue = q; S.shown = 20; render(); },
          text: q + " (" + counts[q] + ")" });
      }));
    var deals = D.deals.filter(function (d) { return d.sales_agent === S.agent && d.queue === S.queue; })
      .sort(function (x, y) { return x.rank_in_agent - y.rank_in_agent; });
    var list = h("div", {}, [qt, h("p", { class: "qhelp", text: QHELP[S.queue] })]);
    if (!deals.length) list.appendChild(h("div", { class: "empty", text: "Nada nesta fila. 🎉" }));
    deals.slice(0, S.shown).forEach(function (d) { list.appendChild(dealCard(d)); });
    if (deals.length > S.shown) {
      list.appendChild(h("button", { class: "more", text: "Mostrar mais (" + (deals.length - S.shown) + ")",
        onclick: function () { S.shown += 20; render(); } }));
    }

    var btn = h("button", { class: "btn", text: "Copiar mensagem" });
    btn.addEventListener("click", function () { copy(a.brief, btn); });
    var side = h("aside", { class: "panel sticky", "aria-label": "Pauta no WhatsApp" }, [
      h("h2", { text: "Pauta no WhatsApp" }),
      h("p", { class: "qhelp", text: "É isto que chega na segunda de manhã, gerado pelo mesmo motor." }),
      h("div", { class: "wa" }, [bubble(a.brief)]), btn]);
    view.appendChild(h("div", { class: "layout" }, [list, side]));
  }

  // ---- gestor --------------------------------------------------------------
  var COLS = [
    ["sales_agent", "Vendedor", "text"], ["alive", "Vivos"], ["expected_value_sum", "Valor esperado"],
    ["decide_count", "Decidir (n)"], ["decide_value", "Parado (US$)"], ["qualify_count", "Qualificar"],
    ["missing_account_count", "Sem conta (todos abertos)"]
  ];
  function cell(key, r) {
    if (key === "expected_value_sum" || key === "decide_value") return money(r[key]);
    return nf.format(r[key]);
  }

  // A linha de totais vem pronta do Python (agente, manager, região ou base inteira).
  function totalRow() {
    if (S.agent) return { label: "Total · " + S.agent, row: agentsByName[S.agent] };
    if (S.manager) return { label: "Total · " + S.manager, row: D.managers.filter(function (m) { return m.manager === S.manager; })[0] };
    if (S.region) return { label: "Total · " + S.region, row: D.regions.filter(function (m) { return m.regional_office === S.region; })[0] };
    return { label: "Total · todos", row: D.totals };
  }

  function filteredDeals() {
    return D.deals.filter(function (d) {
      return (!S.region || d.regional_office === S.region) && (!S.manager || d.manager === S.manager) && (!S.agent || d.sales_agent === S.agent);
    });
  }

  function exportCsv() {
    var cols = ["opportunity_id", "sales_agent", "manager", "regional_office", "product", "account", "queue", "rank_in_agent",
      "age", "days_to_wall", "sales_price", "chance_90d", "expected_value", "reason", "action"];
    var q = function (v) { v = v == null ? "" : String(v); return /[",\n;]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var lines = [cols.join(",")].concat(filteredDeals().map(function (d) { return cols.map(function (c) { return q(d[c]); }).join(","); }));
    var blob = new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8" });
    var a = h("a", { href: URL.createObjectURL(blob), download: "deals_filtrados.csv" });
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  }

  function renderGestor() {
    var rows = visibleAgents().filter(function (a) { return !S.agent || a.sales_agent === S.agent; });
    var k = S.sort.key, dir = S.sort.dir === "ascending" ? 1 : -1;
    rows.sort(function (x, y) { return (typeof x[k] === "string" ? x[k].localeCompare(y[k]) : x[k] - y[k]) * dir; });

    view.appendChild(h("h1", { text: "Visão do gestor" }));
    view.appendChild(h("p", { class: "sub", text: "Quem tem deal vivo, quem tem deal parado e onde o CRM está incompleto." }));
    // Faixa de decisão: números e frase vêm prontos do Python para o escopo filtrado (nada é somado aqui).
    var sc = totalRow(), r = sc.row;
    view.appendChild(h("section", { class: "decision", "aria-label": "Faixa de decisão" }, [
      h("div", { class: "kpis kpis3" }, [
        kpi("Valor esperado do time (90 dias)", money(r.expected_value_sum), sc.label.replace("Total · ", "")),
        kpi("Parado além de " + D.wall_days + " dias", nf.format(r.decide_count) + " deals · " + money(r.decide_value), "fila Decidir"),
        kpi("Abertos sem conta", nf.format(r.missing_account_count) + " de " + nf.format(r.open_count), "todas as filas")]),
      h("p", { class: "reco" }, [h("strong", { text: "Recomendação: " }), r.headline])]));
    view.appendChild(h("div", { class: "toolbar" }, [
      h("span", { class: "sub", text: rows.length + " vendedores" }),
      h("button", { class: "btn alt", text: "Exportar CSV (" + nf.format(filteredDeals().length) + " deals)", onclick: exportCsv })]));

    var head = h("tr", {}, COLS.map(function (c) {
      return h("th", { scope: "col", "aria-sort": S.sort.key === c[0] ? S.sort.dir : "none" }, [
        h("button", { text: c[1], onclick: function () {
          S.sort = { key: c[0], dir: S.sort.key === c[0] && S.sort.dir === "descending" ? "ascending" : "descending" }; render();
        } })]);
    }));
    var body = rows.map(function (r) {
      return h("tr", {}, COLS.map(function (c) {
        if (c[0] === "sales_agent") {
          return h("td", {}, [h("button", { class: "link", text: r.sales_agent, onclick: function () {
            S.agent = r.sales_agent; S.region = ""; S.manager = ""; S.queue = "Agir"; go("vendedor"); } }),
            h("br"), h("small", { text: r.manager + " · " + r.regional_office })]);
        }
        return h("td", { text: cell(c[0], r) });
      }));
    });
    var t = totalRow();
    var foot = h("tr", { class: "total" }, COLS.map(function (c, i) {
      return h("td", { text: i === 0 ? t.label : cell(c[0], t.row) });
    }));
    view.appendChild(h("div", { class: "tablewrap" }, [h("table", {}, [
      h("caption", { class: "skip", text: "Resumo por vendedor" }), h("thead", {}, head), h("tbody", {}, body), h("tfoot", {}, foot)])]));
  }

  // ---- como funciona -------------------------------------------------------
  var STRAT = { score: "Score (este app)", valor: "Valor (preço)", obvia: "“Óbvia”: preço × win rate", mais_novo: "Mais novo primeiro", sorteio: "Sorteio" };

  function renderComo() {
    var maxP = Math.max.apply(null, D.curve.map(function (c) { return c.p; }));
    var bars = D.curve.map(function (c) {
      var cls = c.age_bin === "139+" ? "bar dead" : c.age_bin === "121-138" ? "bar wall" : "bar";
      return h("div", { class: cls }, [h("span", { text: c.age_bin + " d" }),
        h("div", { class: "b" }, [h("i", { style: "width:" + (c.p / maxP * 100) + "%" })]), h("span", { text: pct(c.p) + "%" })]);
    });
    var curve = h("section", { class: "panel" }, [
      h("h2", { text: "Chance de ganhar em 90 dias, por idade do deal" }),
      h("div", { class: "bars", role: "list" }, bars),
      h("p", { class: "callout", text: "Nenhum deal da base fechou depois de " + D.wall_days + " dias. Acima disso a chance é 0% e o deal vai para a fila Decidir." })]);

    var B = D.backtest;
    var rows = B.summary.map(function (r) {
      return h("tr", {}, [h("td", { text: STRAT[r.strategy] || r.strategy }), h("td", { text: pct(r.share, 1) + "%" }),
        h("td", { text: r.strategy === "valor" ? "—" : signed(r.vs_valor) })]);
    });
    var bt = h("section", { class: "panel" }, [
      h("h2", { text: "Teste em semanas passadas" }),
      h("p", { class: "big", text: "Testado em " + B.weeks + " segundas de 2017: o top " + B.k + " de cada vendedor capturou " +
        signed(B.lift_point) + " mais receita que ordenar por valor (IC 90%: " + signed(B.ci90[0]) + " a " + signed(B.ci90[1]) + ")." }),
      h("div", { class: "tablewrap" }, [h("table", { style: "min-width:0" }, [
        h("thead", {}, h("tr", {}, [h("th", { scope: "col", text: "Ordenação" }), h("th", { scope: "col", text: "Receita capturada" }), h("th", { scope: "col", text: "vs. valor" })])),
        h("tbody", {}, rows)])])]);

    var no = h("section", { class: "panel" }, [
      h("h2", { text: "O que não usamos, e por quê" }),
      h("ul", { class: "plain" }, [
        h("li", {}, [h("strong", { text: "Produto, setor, região, vendedor e porte. " }), "Não separam ganho de perda: AUC de 0,51 em teste no tempo, ou seja, cara ou coroa."]),
        h("li", {}, [h("strong", { text: "Vendedor × produto. " }), "A diferença entre as taxas de ganho cabe no ruído estatístico."]),
        h("li", {}, [h("strong", { text: "Lógica “óbvia”. " }), "Preço × win rate do vendedor e do produto acaba ordenando por preço: empata com a ordenação por valor."])])]);

    var A = D.audit;
    var facts = [
      ["Deals na base", nf.format(A.deals_total)], ["Deals abertos", nf.format(A.open_deals)],
      ["Abertos sem conta cadastrada", nf.format(A.open_without_account)],
      ["Prospecting sem data de início", nf.format(A.prospecting_without_engage_date)],
      ["Maior ciclo já concluído", A.max_closed_cycle_days + " dias"],
      ["Em Engaging além desse limite", nf.format(A.engaging_beyond_wall) + " de " + nf.format(A.engaging)],
      ["Win rate dos deals fechados", pct(A.win_rate_closed, 1) + "%"]
    ];
    var dl = h("dl", { class: "facts" });
    facts.forEach(function (f) { dl.appendChild(h("dt", { text: f[0] })); dl.appendChild(h("dd", { text: f[1] })); });
    var q = h("section", { class: "panel" }, [h("h2", { text: "Qualidade dos dados" }), dl]);

    view.appendChild(h("h1", { text: "Como funciona" }));
    view.appendChild(h("p", { class: "sub", text: "Score = preço de lista × chance de ganhar em 90 dias, dada a idade do deal. Só isso, e é suficiente." }));
    view.appendChild(h("div", { class: "how" }, [curve, bt, no, q]));
  }

  // ---- render --------------------------------------------------------------
  function render() {
    syncFilters();
    tabBtns.forEach(function (b) { b.setAttribute("aria-selected", String(b.getAttribute("data-tab") === S.tab)); });
    document.querySelector(".filters").style.display = S.tab === "como" ? "none" : "";
    view.textContent = "";
    if (S.tab === "vendedor") renderVendedor(); else if (S.tab === "gestor") renderGestor(); else renderComo();
  }
  render();
})();
