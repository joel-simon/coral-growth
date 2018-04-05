from __future__ import print_function

import copy
import warnings

from MultiNEAT import *

try:
    import graphviz
except ImportError:
    graphviz = None
    warnings.warn('Could not import optional dependency graphviz.')

import matplotlib.pyplot as plt
import numpy as np


def draw_net(network, in_names, out_names, view=False, filename=None):
    """ Receives a genome and draws a neural network with arbitrary topology. """
    names = dict(enumerate(in_names+out_names))

    # Attributes for network nodes.
    node_attrs = {
        'shape': 'circle',
        'fontsize': '12',
        'height': '0.2',
        'width': '0.2'}

    # Attributes for network input nodes.
    input_attrs = {
        'style': 'filled',
        'shape': 'circle'}

    # Attributes for network output nodes.
    output_attrs = {
        'style': 'filled',
        'color': 'lightblue'}

    dot = graphviz.Digraph(format='svg', node_attr=node_attrs)
    # dot.graph_attr['rankdir'] = 'LR'
    dot.graph_attr['ranksep'] = '1.5'

    print(names)

    for nid, neuron in enumerate(network.neurons):
        name = names.get(nid, str(nid))
        if neuron.type == NeuronType.INPUT or neuron.type == NeuronType.BIAS:
            dot.node(name, _attributes=input_attrs)
        else:
            dot.node(name, _attributes=output_attrs)
        # elif neuron.type == NeuronType.OUTPUT:
            # dot.node(out_names[nid - len(in_names)], _attributes=output_attrs)

    for connection in network.connections:
        a = names.get(connection.source_neuron_idx, str(connection.source_neuron_idx))
        b = names.get(connection.target_neuron_idx, str(connection.target_neuron_idx))
        # b = out_names[connection.target_neuron_idx - len(in_names)]
        style = 'solid'
        color = 'darkgreen' if connection.weight > 0 else 'red'
        width = str(0.2 + abs(connection.weight)/2)
        dot.edge(a, b, _attributes={'style': style, 'color': color, 'penwidth': width})

    return dot.render(filename, view=view)
