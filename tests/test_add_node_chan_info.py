import pytest
nbformat = pytest.importorskip('nbformat')
pd = pytest.importorskip('pandas')


def load_add_node_chan_info():
    nb = nbformat.read('LN Metrics Calculation.ipynb', as_version=4)
    for cell in nb.cells:
        if cell.cell_type == 'code' and 'def add_node_chan_info' in cell.source:
            namespace = {'pd': pd}
            exec(cell.source, namespace)
            return namespace['add_node_chan_info']
    raise AssertionError('Function add_node_chan_info not found')


def test_add_node_chan_info_counts_channels():
    add_node_chan_info = load_add_node_chan_info()

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
