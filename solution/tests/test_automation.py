import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WF_PATH = ROOT / "automation" / "n8n-pauta-segunda.json"
BRIEFS = ROOT / "solution" / "outputs" / "briefs.json"


@pytest.fixture(scope="module")
def wf():
    return json.loads(WF_PATH.read_text())


def test_every_connection_points_to_existing_nodes(wf):
    names = {n["name"] for n in wf["nodes"]}
    assert len(names) == len(wf["nodes"]), "nomes de nó duplicados"
    assert len({n["id"] for n in wf["nodes"]}) == len(wf["nodes"]), "ids de nó duplicados"
    for src, outs in wf["connections"].items():
        assert src in names, src
        for branch in outs["main"]:
            for link in branch:
                assert link["node"] in names, f"{src} → {link['node']}"


def test_both_triggers_feed_the_fetch_and_loop_closes(wf):
    c = wf["connections"]
    targets = lambda n: [l["node"] for b in c[n]["main"] for l in b]  # noqa: E731
    assert targets("Manual Trigger") == ["Buscar briefs.json"]
    assert targets("Toda segunda 8h") == ["Buscar briefs.json"]
    assert targets("Aguardar 5s") == ["Loop Over Items"]
    # saída 0 do loop = fim (Resumo); saída 1 = próximo item (envio)
    assert [l["node"] for l in c["Loop Over Items"]["main"][0]] == ["Resumo"]
    assert [l["node"] for l in c["Loop Over Items"]["main"][1]] == ["Enviar via Whapi"]


def test_schedule_is_monday_8am_sao_paulo(wf):
    sched = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.scheduleTrigger")
    assert sched["parameters"]["rule"]["interval"][0]["expression"] == "0 8 * * 1"
    assert wf["settings"]["timezone"] == "America/Sao_Paulo"


def test_no_secrets_real_phones_or_credential_ids(wf):
    text = WF_PATH.read_text()
    assert "Bearer" not in text and "token" not in text.lower()
    assert not re.findall(r"55\d{10,11}", text), "telefone no arquivo"
    cred = next(n for n in wf["nodes"] if n["name"] == "Enviar via Whapi")["credentials"]["httpHeaderAuth"]
    assert cred == {"name": "Whapi"}


@pytest.mark.skipif(shutil.which("node") is None, reason="node não instalado")
def test_recipients_node_logic(wf):
    """Roda o código do nó 'Destinatários' com o briefs.json real."""
    code = next(n for n in wf["nodes"] if n["name"] == "Destinatários")["parameters"]["jsCode"]
    js = """
const [code, briefsPath] = process.argv.slice(1);
const briefs = JSON.parse(require('fs').readFileSync(briefsPath, 'utf8'));
const run = (c) => new Function('$input', c)({ first: () => ({ json: briefs }) });
const res = {};
try { run(code); } catch (e) { res.placeholder = e.message; }
const filled = code.replace(/55XXXXXXXXXXX/g, '5511999990000');
res.ok = run(filled).map((i) => i.json);
try { run(filled.replace('Zane Levy', 'Fulano')); } catch (e) { res.missing = e.message; }
console.log(JSON.stringify(res));
"""
    out = subprocess.run(["node", "-e", js, code, str(BRIEFS)], capture_output=True, text=True, check=True)
    res = json.loads(out.stdout)
    assert "Telefone inválido" in res["placeholder"]
    assert [(r["type"], r["name"]) for r in res["ok"]] == [("agent", "Zane Levy"), ("manager", "Summer Sewald")]
    assert res["ok"][0]["body"].startswith("Bom dia, Zane!") and res["ok"][1]["body"].startswith("Bom dia, Summer!")
    assert "não existe no briefs.json" in res["missing"] and "Disponíveis" in res["missing"]
