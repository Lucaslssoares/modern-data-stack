"""Cria o dashboard da clima-api no Kibana (dashboard como código).

Uso: python observability/dashboard.py [http://localhost:5601]
Cria os objetos via Saved Objects API (sobrescreve) e exporta observability/dashboard.ndjson,
importável em outro Kibana em Stack Management → Saved Objects → Import.
"""
import json
import sys
import urllib.request
from pathlib import Path

KIBANA = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5601"
DATA_VIEW = "clima-api-logs"
QUERY = {"query": 'service.name : "clima-api"', "language": "kuery"}


def col_time():
    return {"label": "@timestamp", "dataType": "date", "operationType": "date_histogram",
            "sourceField": "@timestamp", "isBucketed": True, "scale": "interval",
            "params": {"interval": "auto", "includeEmptyRows": True}}


def col_terms(field, label, order_by):
    return {"label": label, "dataType": "string", "operationType": "terms", "sourceField": field,
            "isBucketed": True, "scale": "ordinal",
            "params": {"size": 10, "orderBy": {"type": "column", "columnId": order_by},
                       "orderDirection": "desc", "otherBucket": True, "missingBucket": False}}


def col_metric(op, label, field="___records___", **params):
    col = {"label": label, "dataType": "number", "operationType": op, "sourceField": field,
           "isBucketed": False, "scale": "ratio", "params": params, "customLabel": True}
    return col


def lens(obj_id, title, vis_type, columns, visualization):
    return {
        "id": obj_id, "type": "lens",
        "attributes": {
            "title": title, "visualizationType": vis_type,
            "state": {
                "datasourceStates": {"formBased": {"layers": {"l1": {
                    "columns": columns, "columnOrder": list(columns), "incompleteColumns": {}}}}},
                "visualization": visualization, "query": QUERY, "filters": [],
            },
        },
        "references": [{"type": "index-pattern", "id": DATA_VIEW,
                        "name": "indexpattern-datasource-layer-l1"}],
    }


def xy(series, x, accessors, split=None):
    layer = {"layerId": "l1", "layerType": "data", "seriesType": series, "xAccessor": x,
             "accessors": accessors}
    if split:
        layer["splitAccessor"] = split
    return {"legend": {"isVisible": True, "position": "right"}, "preferredSeriesType": series,
            "layers": [layer]}


objects = [
    {"id": DATA_VIEW, "type": "index-pattern",
     "attributes": {"title": "filebeat-*", "timeFieldName": "@timestamp", "name": "clima-api logs"},
     "references": []},

    {"id": "clima-logs-tempo-real", "type": "search",
     "attributes": {
         "title": "clima-api — logs em tempo real",
         "columns": ["log.level", "http.response.status_code", "url.path",
                     "http.response.duration_ms", "message"],
         "sort": [["@timestamp", "desc"]],
         "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps({
             "query": QUERY, "filter": [],
             "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"})}},
     "references": [{"type": "index-pattern", "id": DATA_VIEW,
                     "name": "kibanaSavedObjectMeta.searchSourceJSON.index"}]},

    lens("clima-req-status", "Requisições por status code", "lnsXY",
         {"t": col_time(),
          "s": col_terms("http.response.status_code", "Status", "c"),
          "c": col_metric("count", "Requisições", emptyAsNull=True)},
         xy("bar_stacked", "t", ["c"], split="s")),

    lens("clima-latencia", "Tempo de resposta (ms)", "lnsXY",
         {"t": col_time(),
          "p50": col_metric("median", "p50", "http.response.duration_ms"),
          "p95": col_metric("percentile", "p95", "http.response.duration_ms", percentile=95)},
         xy("line", "t", ["p50", "p95"])),

    lens("clima-por-rota", "Requisições e latência por rota", "lnsDatatable",
         {"r": col_terms("url.path", "Rota", "c"),
          "c": col_metric("count", "Requisições", emptyAsNull=True),
          "a": col_metric("average", "Latência média (ms)", "http.response.duration_ms")},
         {"layerId": "l1", "layerType": "data",
          "columns": [{"columnId": "r"}, {"columnId": "c"}, {"columnId": "a"}]}),

    lens("clima-erros-5xx", "Erros 5xx", "lnsMetric",
         {"e": {**col_metric("count", "Erros 5xx", emptyAsNull=False),
                "filter": {"query": "http.response.status_code >= 500", "language": "kuery"}}},
         {"layerId": "l1", "layerType": "data", "metricAccessor": "e"}),
]

# Layout do dashboard (grade de 48 colunas)
panels = [
    ("clima-erros-5xx", "lens", 0, 0, 12, 10),
    ("clima-req-status", "lens", 12, 0, 36, 10),
    ("clima-latencia", "lens", 0, 10, 24, 12),
    ("clima-por-rota", "lens", 24, 10, 24, 12),
    ("clima-logs-tempo-real", "search", 0, 22, 48, 16),
]
panels_json, refs = [], []
for i, (obj_id, kind, x, y, w, h) in enumerate(panels, 1):
    p = f"p{i}"
    panels_json.append({"type": kind, "panelIndex": p, "panelRefName": f"panel_{p}",
                        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": p},
                        "embeddableConfig": {"enhancements": {}}})
    refs.append({"name": f"{p}:panel_{p}", "type": kind, "id": obj_id})

objects.append({
    "id": "clima-api-dashboard", "type": "dashboard",
    "attributes": {
        "title": "clima-api — Observabilidade",
        "panelsJSON": json.dumps(panels_json),
        "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
        "timeRestore": True, "timeFrom": "now-15m", "timeTo": "now",
        "refreshInterval": {"pause": False, "value": 5000},
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(
            {"query": {"query": "", "language": "kuery"}, "filter": []})},
    },
    "references": refs,
})



def call(path, payload):
    req = urllib.request.Request(
        f"{KIBANA}{path}", data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"kbn-xsrf": "true", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


# bulk_create assume o formato atual (o _import migraria como se fosse versão antiga)
created = json.loads(call("/api/saved_objects/_bulk_create?overwrite=true", objects))
erros = [o for o in created["saved_objects"] if "error" in o]
print(f"{len(objects) - len(erros)}/{len(objects)} objetos criados", erros or "")

# Exporta a versão oficial (com versões de migração) — importável em outro Kibana
exported = call("/api/saved_objects/_export", {
    "objects": [{"type": "dashboard", "id": "clima-api-dashboard"}],
    "includeReferencesDeep": True})
Path(__file__).with_name("dashboard.ndjson").write_text(exported, encoding="utf-8")
print(f"Dashboard: {KIBANA}/app/dashboards#/view/clima-api-dashboard")
