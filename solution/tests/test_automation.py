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


def _targets(wf, name, branch=None):
    outs = wf["connections"][name]["main"]
    sel = outs if branch is None else [outs[branch]]
    return [link["node"] for b in sel for link in b]


def test_every_connection_points_to_existing_nodes(wf):
    names = {n["name"] for n in wf["nodes"]}
    assert len(names) == len(wf["nodes"]), "nomes de nó duplicados"
    assert len({n["id"] for n in wf["nodes"]}) == len(wf["nodes"]), "ids de nó duplicados"
    for src, outs in wf["connections"].items():
        assert src in names, src
        for branch in outs["main"]:
            for link in branch:
                assert link["node"] in names, f"{src} → {link['node']}"


def test_both_triggers_feed_config_and_loop_closes(wf):
    assert _targets(wf, "Rodar agora (demo)") == ["Config (telefones da demo)"]
    assert _targets(wf, "Toda segunda 8h") == ["Config (telefones da demo)"]
    assert _targets(wf, "Pausa 5s (antispam)") == ["Um por vez"]
    assert _targets(wf, "Um por vez", 0) == ["Resumo do envio"]   # saída 0 = fim
    assert _targets(wf, "Um por vez", 1) == ["Enviar via Whapi"]  # saída 1 = próximo item


def test_schedule_is_monday_8am_sao_paulo(wf):
    sched = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.scheduleTrigger")
    assert sched["parameters"]["rule"]["interval"][0]["expression"] == "0 8 * * 1"
    assert wf["settings"]["timezone"] == "America/Sao_Paulo"


def test_send_node_targets_whapi_text_endpoint(wf):
    send = next(n for n in wf["nodes"] if n["name"] == "Enviar via Whapi")
    assert send["parameters"]["url"] == "https://gate.whapi.cloud/messages/text"
    assert send["parameters"]["genericAuthType"] == "httpBearerAuth"


def test_no_secrets_real_phones_or_credential_ids(wf):
    text = WF_PATH.read_text()
    assert not re.findall(r"55\d{10,11}", text), "telefone no arquivo"
    cred = next(n for n in wf["nodes"] if n["name"] == "Enviar via Whapi")["credentials"]["httpBearerAuth"]
    assert cred == {"name": "Whapi"}, "credencial deve ir só pelo nome, sem id"


@pytest.mark.skipif(shutil.which("node") is None, reason="node não instalado")
def test_montar_mensagens_logic(wf):
    """Roda o código do nó 'Montar mensagens' com o briefs.json real."""
    code = next(n for n in wf["nodes"] if n["name"] == "Montar mensagens")["parameters"]["jsCode"]
    js = r"""
const [code, briefsPath] = process.argv.slice(1);
const briefs = JSON.parse(require('fs').readFileSync(briefsPath, 'utf8'));
const run = (cfg) => new Function('$input', '$', code)(
  { first: () => ({ json: briefs }) },
  () => ({ first: () => ({ json: cfg }) })
);
const base = { agent_name: 'Zane Levy', manager_name: 'Summer Sewald' };
const res = {};
try { run({ ...base, agent_phone: '55XXXXXXXXXXX', manager_phone: '55XXXXXXXXXXX' }); } catch (e) { res.placeholder = e.message; }
res.ok = run({ ...base, agent_phone: '5511999990000', manager_phone: '5511999990001' }).map((i) => i.json);
try { run({ ...base, agent_name: 'Fulano', agent_phone: '5511999990000', manager_phone: '5511999990001' }); } catch (e) { res.missing = e.message; }
console.log(JSON.stringify(res));
"""
    out = subprocess.run(["node", "-e", js, code, str(BRIEFS)], capture_output=True, text=True, check=True)
    res = json.loads(out.stdout)
    assert "Telefone inválido" in res["placeholder"]
    assert [(r["type"], r["name"]) for r in res["ok"]] == [("agent", "Zane Levy"), ("manager", "Summer Sewald")]
    assert res["ok"][0]["body"].startswith("Bom dia, Zane!") and res["ok"][1]["body"].startswith("Bom dia, Summer!")
    assert "não existe no briefs.json" in res["missing"] and "Disponíveis" in res["missing"]
