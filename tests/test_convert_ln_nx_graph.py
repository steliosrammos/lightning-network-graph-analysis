import json
import pytest
nbformat = pytest.importorskip('nbformat')
networkx = pytest.importorskip('networkx')


def load_convert_ln_json_to_nx_graph():
    nb = nbformat.read('LN Metrics Calculation.ipynb', as_version=4)
    for cell in nb.cells:
        if cell.cell_type == 'code' and 'def convert_ln_json_to_nx_graph' in cell.source:
            ns = {'networkx': networkx, 'nx': networkx, 'json': json}
            exec(cell.source, ns)
            return ns['convert_ln_json_to_nx_graph']
    raise AssertionError('Function convert_ln_json_to_nx_graph not found')


def test_convert_ln_json_to_nx_graph_last_update(tmp_path):
    convert = load_convert_ln_json_to_nx_graph()
    sample = {
        "nodes": [
            {
                "pub_key": "node1",
                "alias": "Node 1",
                "addresses": [],
                "color": "#fff",
                "last_update": 1
            },
            {
                "pub_key": "node2",
                "alias": "Node 2",
                "addresses": [],
                "color": "#000",
                "last_update": 2
            }
        ],
        "edges": [
            {
                "channel_id": "123",
                "chan_point": "0:1",
                "last_update": 3,
                "capacity": "1000",
                "node1_pub": "node1",
                "node2_pub": "node2",
                "node1_policy": {},
                "node2_policy": {}
            }
        ]
    }
    json_file = tmp_path / "graph.json"
    json_file.write_text(json.dumps(sample))

    G = convert(str(json_file))
    assert G.nodes["node1"]["last_update"] == 1
    assert G.nodes["node2"]["last_update"] == 2
