import networkx as nx
import numpy as np
from config import delta, epsilon, max_iter_num
import math
import csv


class Simulater:
    def __init__(self, topo):
        self.current_total_cost = 0.0
        self.previous_total_cost = 0.0
        self.splitting_ratios = {}
        self.loads = {}
        self.r = {}
        self.trees = {}
        self.branches_structuer = {}
        self.branches_cardinality_structure = {}
        self.topo = topo
        self.stack = Stack()
        self.initialize_splitting_ratios_structure()
        self.initialize_r_structure()
        self.initialize_link_loads_structure()
        self.initialize_branches_structure()
        self.initialize_branches_cardinality_structure()

        # with open("splitting_ratios.csv", 'w', newline='') as csvfile:
        #     self.splitting_ratios_writer = csv.writer(csvfile, delimiter=',')
        #
        # self.csvfile = open('splitting_ratios.csv', 'a')
        self.splitting_ratios_rows = []


    def initialize_splitting_ratios_structure(self):
        """
        Initialize the splitting_ratios structure
        Initialization is done here evenly among each outgoing link (1/ num_out_links).
        """

        for dst in self.topo.nodes():
            self.splitting_ratios[dst] = {}
        for dst in self.topo.nodes():

            for current_node in self.topo.nodes():
                if current_node == dst:
                    continue

                neighbors = self.neighbors(current_node)
                outgoing_links = [(current_node, v) for v in neighbors]
                num_out_links = len(outgoing_links)

                for outgoing_link in outgoing_links:
                    self.splitting_ratios[dst][outgoing_link] = 1 / num_out_links
        # print("splitting ratios: ", self.splitting_ratios)

    def neighbors(self, node):
        return list(self.topo.neighbors(node))

    def initialize_branches_cardinality_structure(self):
        for node in self.topo.nodes():
            self.branches_cardinality_structure[node] = {}
            for dst in self.topo.nodes():
                self.branches_cardinality_structure[node][dst] = 1

    def initialize_branches_structure(self):
        """ This is a dictionary where keys are all
         destinations and the value is an inner dictionary
         of two components: list of neighbors
         and count of that list, this structure is used to update
         the branch_cardinality per each node per each dst"""
        # neighbors = []
        # count = 0
        for dst in self.topo.nodes():
            self.branches_structuer[dst] = {}
            for branch in self.topo.nodes():
                # if branch == dst:
                #     continue
                self.branches_structuer[dst][branch] = {}
                self.branches_structuer[dst][branch]['children'] = []
                self.branches_structuer[dst][branch]['count'] = 0
        # print("branches_structure: ", self.branches_structuer)

    def initialize_r_structure(self):
        for src in self.topo.nodes():
            self.r[src] = {}
            for dst in self.topo.nodes():
                if src == dst:
                    continue

                self.r[src][dst] = 0.0

    def initialize_link_loads_structure(self):
        """ link loads structure is per each link per each destination"""
        # print("edges: ", self.topo.edges())
        for link in self.topo.edges():
            self.loads[link] = {}
            for dst in self.topo.nodes():
                self.loads[link][dst] = 0.0

    def simulate(self, tm):

        for i in range(max_iter_num):
            self.update_loads_and_rates(tm)
            # self.test_received_demands(tm)

            # Now recalculating weights to proceed with the algorithm:
            self.update_weights()
            self.update_shortest_path_trees()
            self.update_branches_structure()
            self.update_branches_cardinality()
            self.update_splitting_ratios()
            if abs(self.current_total_cost - self.previous_total_cost) < epsilon:
                print("are we here? current total cost: ", self.current_total_cost, self.previous_total_cost)
                break
            # print("iteration number: ", i, " total cost: ", self.current_total_cost)

        # Todo: put that in a function write_link_loads_to_file()
        for edge in self.loads:
            summ = 0
            for dst in self.loads[edge]:
                summ += self.loads[edge][dst]
            print("load on edge ", edge, " ", summ)


        # Todo: you may need to write this in to a file
        # writing splitting ratios to a file
        # with open("splitting_ratios.csv", 'w', newline='') as csvfile:
        #     writer = csv.writer(csvfile, delimiter=',')
        #     writer.writerows(self.splitting_ratios_rows)


    def update_splitting_ratios(self):
        # print("splitting ratio structure: ", self.splitting_ratios)
        for dst in self.topo.nodes():
            for current_node in self.topo.nodes():
                if dst == current_node:
                    continue
                neighbors = self.neighbors(current_node)
                outgoing_links = [(current_node, v) for v in neighbors]
                shortest_path = self.trees[dst][current_node]
                shortest_path_edges = [(shortest_path[i], shortest_path[i + 1]) for i, _ in
                                       enumerate(shortest_path[:-1])]
                if self.r[current_node][dst] == 0.0:
                    for edge in outgoing_links:
                        if edge in shortest_path_edges:  # if edge is on the shortest path
                            self.splitting_ratios[dst][edge] = 1.0
                        else:
                            self.splitting_ratios[dst][edge] = 0.0
                else:
                    shortest_path_change = 0.0
                    for edge in outgoing_links:
                        if edge not in shortest_path_edges:  # notice the not (we need to accumulate here)
                            change = -1.0 * (self.splitting_ratios[dst][edge] * delta /
                                             self.branches_cardinality_structure[current_node][
                                                 dst] * self.r[current_node][dst])
                            shortest_path_change += change
                            self.splitting_ratios[dst][edge] += change
                        else:
                            shortest_path_edge = edge
                    change = -1.0 * shortest_path_change  # the change of the edge on the shortest path
                    self.splitting_ratios[dst][shortest_path_edge] += change
                    # print(sum([self.splitting_ratios[dst][edge] for edge in outgoing_links]))
                    assert (0.99 < sum([self.splitting_ratios[dst][edge] for edge in outgoing_links]) <= 1.01)

        # todo: write that to function write_splitting_ratios_to_file()
        row = []
        for dst in self.splitting_ratios:
            for outgoing_link in self.splitting_ratios[dst]:
                row.append(self.splitting_ratios[dst][outgoing_link])

        self.splitting_ratios_rows.append(row)
        #self.splitting_ratios_writer.writerow(row)
        # self.csvfile.write(row)
        # print("updated splitting ratios: ", self.splitting_ratios)

    def update_loads_and_rates(self, tm):
        # max_ = 0
        for dst in self.topo.nodes():
            for src in self.topo.nodes():
                if src == dst:
                    continue

                self.stack.push(src)

                while not self.stack.isEmpty():
                    # if self.stack.size() > max_:
                    #     max_ = self.stack.size()
                    current_node = self.stack.pop()
                    if current_node == dst:
                        # self.stack.pop()
                        continue
                    self.update_loads_rate_for_current_node(current_node, dst, tm)

    def update_branches_cardinality(self):

        for dst in self.topo.nodes():
            tree = self.trees[dst]
            for t, path in tree.items():
                if t == dst:
                    continue
                product = 1
                reversed_path = path[::-1]
                for node in reversed_path[:-1]:
                    product *= self.branches_structuer[dst][node]['count']
                self.branches_cardinality_structure[t][dst] = product

        # print("branches_cardinality_structure: ", self.branches_cardinality_structure)

    def update_branches_structure(self):
        # print("tree of dst (3): ", self.trees[3])
        # pass
        for dst in self.trees:
            for node, path in self.trees[dst].items():
                # print(node, path)
                if node == dst:
                    continue
                reversed_path = path[::-1]
                for i, branch in enumerate(reversed_path[:-1]):
                    # Todo: Accessing the dictionary too many times might be time consuming.
                    if reversed_path[i + 1] not in self.branches_structuer[dst][branch]['children']:
                        self.branches_structuer[dst][branch]['children'].append(reversed_path[i + 1])
                        self.branches_structuer[dst][branch]['count'] += 1
        # print("branch structure of dst (3): ", self.branches_structuer[3])

    def update_shortest_path_trees(self):
        for node in self.topo.nodes():
            self.trees[node] = nx.single_target_shortest_path(self.topo, node)

        # path = nx.single_source_shortest_path(self.topo, 0)
        # print("path: ", path)

    def update_weights(self):
        # TODO: There is this idea of assuming there is no
        #  capacity constrain and normalizing link loads
        #  based on the maximum utilized link (min-max normalization).
        #  The reason is that the maximum over-utilized link still
        #  has to have the highest weights (cost) among others.
        #  This might help decreasing the number of iterations.

        # print("In udpate_weights")
        # print(self.loads)

        attrs = {}
        self.previous_total_cost = self.current_total_cost
        self.current_total_cost = 0.0
        for edge in self.topo.edges(data=True):
            # attrs = {(0, 1): {'attr1': 20, 'attr2': 'nothing'},...(1, 2): {'attr2': 3}}
            # nx.set_edge_attributes(G, attrs)

            link = (edge[0], edge[1])
            total_load = sum(list(self.loads[link].values()))
            # print("total load: ", total_load)
            capacity = edge[2]['capacity']
            if total_load >= capacity:
                total_load = capacity - (0.001 * capacity)
            weight = capacity / (capacity - total_load) ** 2  # the derivative of x/(c-x) is c/(c-x)^2
            # weight = math.exp(total_load)
            self.current_total_cost += weight
            # print("total load: ", total_load, "weight: ", weight)
            attrs[link] = {'capacity': edge[2]['capacity'], 'weight': weight}

        # print("total_cost: ", self.total_cost)
        nx.set_edge_attributes(self.topo, attrs)
        # print(self.topo.edges(data=True))

    def test_received_demands(self, tm):
        """
        Testing if sent demands same or close to received demands
        """

        aggregated_sent_demand = {}
        for dst in tm:
            aggregated_sent_demand[dst] = 0.0
        for src in tm:
            for dst in tm:
                aggregated_sent_demand[dst] += tm[src][dst]
        print("aggregated_sent_demand:")
        print(aggregated_sent_demand)

        aggregated_received_demand = {}
        for dst in tm:
            aggregated_received_demand[dst] = 0.0

        for link in self.loads:
            aggregated_received_demand[link[1]] += self.loads[link][link[1]]
        print("aggregated_received_demand:")
        print(aggregated_received_demand)
        print("PCC is: ",
              np.corrcoef(list(aggregated_received_demand.values()), list(aggregated_sent_demand.values()))[0, 1])

    def update_loads_rate_for_current_node(self, current_node, dst, tm):
        neighbors = self.neighbors(current_node)
        incoming_links = [(u, current_node) for u in neighbors]
        outgoing_links = [(current_node, v) for v in neighbors]
        # print("loads: ", self.loads)
        incoming_flow_sum = sum([load for load in [self.loads[link][dst] for link in incoming_links]])
        self.r[current_node][dst] = incoming_flow_sum + tm[current_node][dst]

        for outgoing_link in outgoing_links:
            # print("here")
            # print("dst: ", dst)
            load_before_update = self.loads[outgoing_link][dst]
            self.loads[outgoing_link][dst] = self.r[current_node][dst] * self.splitting_ratios[dst][outgoing_link]

            # print(self.loads[outgoing_link][dst],  self.r[current_node][dst] , self.splitting_ratios[dst][outgoing_link])
            if (outgoing_link[1] != dst) and (self.loads[outgoing_link][dst] - load_before_update > 0.0001):
                self.stack.push(outgoing_link[1])
        # print("self.loads: ", self.loads)


class Stack:
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[len(self.items) - 1]

    def size(self):
        return len(self.items)
