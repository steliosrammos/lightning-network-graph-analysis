import json
import pandas as pd
from pandas import json_normalize


def convert_ln_json_to_df(json_file_path):
    """Convert Lightning Network JSON graph data to pandas DataFrames.

    Parameters
    ----------
    json_file_path : str
        Path to the JSON graph file.

    Returns
    -------
    tuple(pd.DataFrame, pd.DataFrame)
        DataFrame of nodes and DataFrame of channels.
    """
    with open(json_file_path, 'r') as f:
        graph_json = json.load(f)

    df_nodes = json_normalize(graph_json['nodes'])
    df_channels = json_normalize(graph_json['edges'])
    df_channels.channel_id = df_channels.channel_id.astype(int)
    df_channels.capacity = df_channels.capacity.astype(int)

    return df_nodes, df_channels
