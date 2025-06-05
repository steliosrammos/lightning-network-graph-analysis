"""Utilities for analyzing Lightning Network graphs.

This module provides helper functions to convert the raw JSON Lightning
Network dump into NetworkX or graph-tool graphs and to compute a few
basic statistics.  It also exposes a small CLI so the module can be
invoked directly with ``python -m analysis``.
"""
from __future__ import annotations

from pathlib import Path
import json
import argparse
from datetime import datetime


__all__ = [
    "convert_ln_json_to_nx_graph",
    "convert_ln_json_to_gt_graph",
    "add_node_chan_info",
    "get_distance_measures",
]


def convert_ln_json_to_nx_graph(json_file_path: str | Path):
    """Convert a Lightning Network JSON file into a NetworkX graph."""
    import networkx as nx

    with open(json_file_path, "r") as f:
        graph_json = json.load(f)

    g = nx.Graph()

    for node in graph_json["nodes"]:
        g.add_node(
            node["pub_key"],
            alias=node.get("alias"),
            addresses=node.get("addresses"),
            color=node.get("color"),
            last_update=node.get("last_update"),
        )

    for edge in graph_json["edges"]:
        g.add_edge(
            edge["node1_pub"],
            edge["node2_pub"],
            channel_id=edge["channel_id"],
            chan_point=edge["chan_point"],
            last_update=edge["last_update"],
            capacity=edge["capacity"],
            node1_policy=edge["node1_policy"],
            node2_policy=edge["node2_policy"],
        )

    return g


def convert_ln_json_to_gt_graph(
    json_file_path: str | Path | None = None,
    *,
    nx_graph=None,
    internal_properties: bool = True,
    directed: bool = False,
):
    """Convert a Lightning Network JSON or NetworkX graph into a graph-tool graph."""
    import graph_tool as gt
    import networkx as nx

    if nx_graph is None:
        if json_file_path is None:
            raise ValueError("Provide json_file_path or nx_graph")
        nx_graph = convert_ln_json_to_nx_graph(json_file_path)
    else:
        if isinstance(nx_graph, (str, Path)):
            nx_graph = nx.read_gpickle(nx_graph)

    g = gt.Graph(directed=directed)

    v_pub_key = g.new_vertex_property("string")
    v_last_update = g.new_vertex_property("int")
    v_alias = g.new_vertex_property("string")
    v_addresses = g.new_vertex_property("string")
    v_color = g.new_vertex_property("string")

    e_channel_id = g.new_edge_property("object")
    e_chan_point = g.new_edge_property("object")
    e_last_update = g.new_edge_property("int")
    e_capacity = g.new_edge_property("object")
    e_node1_pub = g.new_edge_property("object")
    e_node2_pub = g.new_edge_property("object")
    e_node1_policy = g.new_edge_property("object")
    e_node2_policy = g.new_edge_property("object")

    v_indices: dict[str, int] = {}

    for node, data in nx_graph.nodes(data=True):
        v = g.add_vertex()
        v_indices[node] = g.vertex_index[v]
        v_pub_key[v] = node
        v_alias[v] = data.get("alias")
        v_addresses[v] = data.get("addresses")
        v_color[v] = data.get("color")
        v_last_update[v] = data.get("last_update", 0)

    for node1, node2, data in nx_graph.edges(data=True):
        v_index = v_indices[node1]
        target_index = v_indices[node2]

        v = g.vertex(v_index)
        target = g.vertex(target_index)
        e = g.add_edge(v, target)

        e_channel_id[e] = data.get("channel_id")
        e_chan_point[e] = data.get("chan_point")
        e_last_update[e] = data.get("last_update", 0)
        e_capacity[e] = data.get("capacity")
        e_node1_pub[e] = node1
        e_node2_pub[e] = node2
        e_node1_policy[e] = data.get("node1_policy")
        e_node2_policy[e] = data.get("node2_policy")

    if internal_properties:
        g.vertex_properties["pub_key"] = v_pub_key
        g.vertex_properties["alias"] = v_alias
        g.vertex_properties["addresses"] = v_addresses
        g.vertex_properties["color"] = v_color
        g.vertex_properties["last_update"] = v_last_update

        g.edge_properties["channel_id"] = e_channel_id
        g.edge_properties["chan_point"] = e_chan_point
        g.edge_properties["last_update"] = e_last_update
        g.edge_properties["node1_pub"] = e_node1_pub
        g.edge_properties["node2_pub"] = e_node2_pub
        g.edge_properties["node1_policy"] = e_node1_policy
        g.edge_properties["node2_policy"] = e_node2_policy

    return g


def add_node_chan_info(df_nodes, df_channels):
    """Augment node DataFrame with channel statistics."""
    import pandas as pd

    df_nodes = pd.concat(
        [
            df_nodes,
            pd.DataFrame(
                columns=[
                    "num_enabled_channels",
                    "num_channels",
                    "percent_enabled_chan",
                    "total_node_capacity",
                ]
            ),
        ],
        sort=False,
    )

    for index, node in df_nodes.iterrows():
        pub_key = node["pub_key"]
        node_channels = df_channels[
            (df_channels.node1_pub == pub_key) | (df_channels.node2_pub == pub_key)
        ]

        enabled_channels = 0
        total_capacity = 0

        for _, channel in node_channels.iterrows():
            total_capacity += channel.capacity
            if channel.node1_pub == pub_key:
                disabled = channel.loc["node1_policy.disabled"]
            else:
                disabled = channel.loc["node2_policy.disabled"]

            if disabled is not None and not disabled:
                enabled_channels += 1

        df_nodes.loc[index, "num_enabled_channels"] = enabled_channels
        df_nodes.loc[index, "num_channels"] = node_channels.shape[0]
        if node_channels.shape[0] > 0:
            df_nodes.loc[index, "percent_enabled_chan"] = enabled_channels / node_channels.shape[0]
        df_nodes.loc[index, "total_node_capacity"] = total_capacity

    return df_nodes


def get_distance_measures(
    graph,
    directed: bool = False,
    pseudo_diameter: bool = False,
    return_dist: bool = False,
):
    """Compute average distance, diameter and radius of a graph-tool graph."""
    import numpy as np
    import pandas as pd
    from graph_tool.all import shortest_distance
    import graph_tool as gt

    dist_map = shortest_distance(graph, directed=directed)
    shortest_paths = pd.DataFrame(dist_map)

    average = shortest_paths.replace(0, np.nan).mean(skipna=True).mean()
    print(f"Average shortest distance: {round(average, 2)}")

    if pseudo_diameter:
        diameter, _ = gt.topology.pseudo_diameter(graph)
        print(f"Diameter: {diameter}")
    else:
        diameter = shortest_paths.values.max()
        print(f"Pseudo-diameter: {diameter}")

    radius = shortest_paths.replace(0, np.nan).max(skipna=True).min()
    print(f"Radius: {radius}")

    if return_dist:
        return shortest_paths, average, diameter, radius

    return average, diameter, radius


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run basic Lightning Network analysis")
    parser.add_argument("json_file", nargs="?", help="Path to the Lightning Network JSON file")
    parser.add_argument(
        "--nx-graph",
        help="Path to a saved NetworkX graph (gpickle). If provided the JSON file is ignored",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print distance statistics using graph-tool if available",
    )

    args = parser.parse_args(argv)

    g_nx = None
    if args.nx_graph:
        import networkx as nx
        nx_path = Path(args.nx_graph)
        if not nx_path.exists():
            print(f"NetworkX graph {args.nx_graph} not found")
            return
        g_nx = nx.read_gpickle(nx_path)
    elif args.json_file:
        g_nx = convert_ln_json_to_nx_graph(args.json_file)
        import networkx as nx
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = Path(f"nx_graph_{timestamp}.gpickle")
        nx.write_gpickle(g_nx, out_path)
        print(f"Saved NetworkX graph to {out_path}")
    else:
        print("Please provide a JSON file or --nx-graph")
        return

    try:
        from conversion import convert_ln_json_to_df
    except Exception:
        convert_ln_json_to_df = None

    if args.json_file and convert_ln_json_to_df and Path(args.json_file).exists():
        nodes, channels = convert_ln_json_to_df(args.json_file)
        nodes = add_node_chan_info(nodes, channels)
        print(nodes.head())

    if args.stats:
        try:
            g_gt = convert_ln_json_to_gt_graph(nx_graph=g_nx)
        except Exception as exc:
            print(f"Unable to compute distance measures: {exc}")
        else:
            get_distance_measures(g_gt)


if __name__ == "__main__":
    main()
