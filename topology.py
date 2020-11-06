import networkx as nx
import fnss as fnss
from config import TOPOLOGY_SOURCE, TOPOLOGY_PATH
import pickle
import copy
import re
import time


class Topology:
    """
    Stores network topology graph, configures capacities, visualize graph.
    """

    def __init__(self, num_nodes, num_links):
        self.num_nodes = num_nodes
        self.num_links = num_links
        self.topo = None

        if TOPOLOGY_SOURCE == 'file':
            if TOPOLOGY_PATH.endswith('dot'):
                self.read_dot_topology_from_file()
            if TOPOLOGY_PATH.endswith('graphml'):
                self.read_graphml_topology_from_file()
            if TOPOLOGY_PATH.endswith('pickle'):
                pickle_in = open(TOPOLOGY_PATH, "rb")
                self.topo = pickle.load(pickle_in)
            self.topology_file_name = TOPOLOGY_PATH.split('/')[-1]
        else:
            self.create_random_topology(num_nodes, num_links, seed=1)
            self.topo = self.topo.to_directed()
            self.set_capacities()
            fnss.set_weights_inverse_capacity(self.topo)
            # pickle out to a file
            random_file_name = "random_topo" + time.strftime("%Y-%m-%d-H%H-M%M-S%S") + ".pickle"
            pickle_out = open("data/topologies/random/" + random_file_name, "wb")
            pickle.dump(self.topo, pickle_out)
            pickle_out.close()

        # print("topo is: ", self.topo.edges())
        # self.visualizeGraph('spring', node_size=175, show_edge_labels=True)
        # assert (nx.is_connected(self.topo)) # doesn't work for directed topology!

    # @staticmethod
    def create_random_topology(self, n, l, seed):
        if l < n:
            print("l < n, cannot create disconnected topology")
            return None

        self.topo = nx.dense_gnm_random_graph(n, l, seed)

    def set_capacities(self):
        fnss.set_capacities_edge_betweenness(self.topo, [5], 'Gbps')  # default 5 Gbps for each link

    def read_dot_topology_from_file(self):
        g = nx.networkx.drawing.nx_pydot.read_dot(TOPOLOGY_PATH)
        # g = nx.read_graphml(TOPOLOGY_PATH) # node_type=int)
        # print(g.edges(data=True))

        nodes_to_delete = []
        for tuple in g.edges(data=True):
            if 'h' in tuple[0]:
                nodes_to_delete.append(tuple[0])
            if 'h' in tuple[1]:
                nodes_to_delete.append(tuple[1])
        for node in set(nodes_to_delete):
            g.remove_node(node)
        # visualizeGraph(g, 'spring', show_edge_labels=False)
        g = nx.convert_node_labels_to_integers(g, first_label=0, ordering='default', label_attribute=None)
        # adding 'weight' attribute
        for source, target in g.edges():
            cost = int(g[source][target][0]['cost'])
            if cost == 0:
                cost = 1
            g[source][target][0]['weight'] = cost
        # removing unneeded properties in the graph
        unneeded_att_list = ['dst_port', 'src_port', 'cost']
        for n1, n2, d in g.edges(data=True):
            for att in unneeded_att_list:
                d.pop(att, None)
        # cleaning capacities
        for source, target in g.edges():
            strr = g[source][target][0]['capacity']
            temp = re.findall(r'\d+', strr)
            res = list(map(int, temp))
            g[source][target][0]['capacity'] = res[0]
        # visualizeGraph(g, 'spring', show_edge_labels=False)
        # converting graph from multigraph to single graph

        g = nx.Graph(g)
        g = nx.to_directed(g)
        # print(g.edges(data=True))
        self.topo = copy.deepcopy(g)

    def read_graphml_topology_from_file(self):
        # g = nx.networkx.drawing.nx_pydot.read_dot(TOPOLOGY_PATH)
        g = nx.read_graphml(TOPOLOGY_PATH)  # node_type=int)
        g = nx.convert_node_labels_to_integers(g, first_label=0, ordering='default', label_attribute=None)
        for source, target in g.edges():
            g[source][target]['weight'] = 1.0

        # setting capacities
        for source, target in g.edges():
            strr = g[source][target]['LinkSpeedRaw']
            # temp = re.findall(r'\d+', strr)
            # res = list(map(int, temp))
            g[source][target]['capacity'] = float(strr) / 1000000000.0

        # removing unneeded properties in the graph
        # 'LinkType': 'Fibre', 'LinkSpeed': '10', 'LinkLabel': 'Lit
        # Fibre (10 Gbps)', 'LinkSpeedRaw': 10000000000.0, 'LinkNote': 'Lit  ( )'
        unneeded_att_list = list(list(g.edges(data=True))[0][2].keys())  # [0][1][2].keys()
        unneeded_att_list.remove('weight')
        unneeded_att_list.remove('capacity')
        # print("this is the unnedded list", unneeded_att_list)
        # print(g.edges(data=True))
        for n1, n2, d in g.edges(data=True):
            for att in unneeded_att_list:
                d.pop(att, None)

        g = nx.Graph(g)
        g = nx.to_directed(g)
        self.topo = copy.deepcopy(g)
