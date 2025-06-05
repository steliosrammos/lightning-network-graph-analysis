import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis import add_node_chan_info


def test_add_node_chan_info_counts_channels():

    df_nodes = pd.DataFrame({'pub_key': ['A', 'B', 'C']})
    df_channels = pd.DataFrame({
        'node1_pub': ['A', 'B', 'C'],
        'node2_pub': ['B', 'C', 'A'],
        'capacity': [10, 20, 30],
        'node1_policy.disabled': [False, None, False],
        'node2_policy.disabled': [True, False, False]
    })

    result = add_node_chan_info(df_nodes.copy(), df_channels)

    a = result[result['pub_key'] == 'A'].iloc[0]
    assert a['num_channels'] == 2
    assert a['num_enabled_channels'] == 2
    assert a['total_node_capacity'] == 40

    b = result[result['pub_key'] == 'B'].iloc[0]
    assert b['num_channels'] == 2
    assert b['num_enabled_channels'] == 0
    assert b['total_node_capacity'] == 30
