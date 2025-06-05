import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conversion import convert_ln_json_to_df


def test_convert_ln_json_to_df(tmp_path):
    sample_data = {
        "nodes": [
            {
                "pub_key": "node1",
                "alias": "Node 1",
                "addresses": [],
                "color": "#ffffff",
                "last_update": 1
            },
            {
                "pub_key": "node2",
                "alias": "Node 2",
                "addresses": [],
                "color": "#000000",
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

    json_file = tmp_path / "sample.json"
    json_file.write_text(json.dumps(sample_data))

    df_nodes, df_channels = convert_ln_json_to_df(str(json_file))

    expected_node_columns = {"pub_key", "alias", "addresses", "color", "last_update"}
    expected_channel_columns = {
        "channel_id",
        "chan_point",
        "last_update",
        "capacity",
        "node1_pub",
        "node2_pub",
    }

    assert expected_node_columns.issubset(df_nodes.columns)
    assert expected_channel_columns.issubset(df_channels.columns)
