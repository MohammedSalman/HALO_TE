import time
import numpy as np
import copy
import random
from config import tm_type, tm_scale_factor, num_tms
from config import DEMAND_SOURCE, demand_path
import csv
import fnss as fnss
import pickle
import os
import copy

def counted(f):
    def wrapped(*args, **kwargs):
        wrapped.calls += 1
        return f(*args, **kwargs)

    wrapped.calls = 0
    return wrapped


class TrafficGenerator:
    """
        Generates different types of traffic matrices: Gravity, Bimodal ... etc.
    """

    def __init__(self, topo):

        self.topo = topo

        # self.tm = {}
        # for s in self.topo.nodes():
        #     self.tm[s] = {}
        #     for d in self.topo.nodes():
        #         self.tm[s][d] = 0.0

        # a dictionary with values to make scaling for all models the same

        self.matrices_sequence = []

        self.tm = {}
        if DEMAND_SOURCE == 'generate':
            self.num_tms = num_tms
        if DEMAND_SOURCE == 'file':
            self.read_file()

    def read_file(self):

        print("Fetching demands from: ", demand_path)
        try:

            pickle_in = open(demand_path, "rb")
            self.matrices_sequence = pickle.load(pickle_in)
        except FileNotFoundError:
            print("Demand file doesn't exist!")
            exit(0)

        # TODO: remove this: reducing the magnitude of the volumes:
        # for tm in self.matrices_sequence:
        #     for src in tm:
        #         for dst in tm:
        #             # print(self.matrices_sequence[src])
        #             #if src == dst:
        #             #    continue
        #             tm[src][dst] = tm[src][dst]/15.0

        self.num_tms = len(self.matrices_sequence)
        self.iter_matrices_sequence = iter(self.matrices_sequence)

    def __iter__(self):
        return self

    @counted
    def __next__(self):
        global tm
        if DEMAND_SOURCE == 'generate':

            if tm_type == 'gravity':
                tm = self.generateGravityTM()
            if tm_type == 'bimodal':
                tm = self.generateGravityTM()
            # save that tm to file:
            # save demand to file if this is that was the last tm:
            if self.num_tms == self.__next__.calls:
                print("are we here!")
                self.write_tm_to_file()

        if DEMAND_SOURCE == 'file':
            tm = self.read_from_file()
        return tm

    def write_tm_to_file(self):
        print("got here!")
        filename = time.strftime("%Y%m%d-%H%M%S")
        dirName = 'data/demands/saved_demands/'
        file_path = dirName + filename
        try:
            os.makedirs(dirName)
        except:
            print("directory already exist")

        pickle_out = open(file_path, "wb")
        pickle.dump(self.matrices_sequence, pickle_out)
        pickle_out.close()

    def read_from_file(self):
        return next(self.iter_matrices_sequence)
        # for tm in self.matrices_sequence:
        #     return tm

    def generateBimodalTM(self):

        tm = {}
        for s in self.topo.nodes():
            tm[s] = {}
            for d in self.topo.nodes():
                tm[s][d] = 0.0
        Cap = {}

        for src in self.topo.nodes():
            cap = 0
            for neighbour in self.topo[src]:
                cap += self.topo[src][neighbour]['capacity']
            Cap[src] = cap

        # for n in range(self.num_tms):
        for src in tm:
            outgoing = Cap[src]
            for dst in tm:
                if src == dst:
                    tm[src][dst] = 0.0
                    continue
                if np.random.random() > 0.2:
                    mu = 0.0009 * outgoing
                    std = outgoing / 6.0

                    while True:
                        rnd = np.random.normal(mu, std)
                        while rnd < 0.0:
                            rnd = np.random.normal(mu, std)
                        break
                    # tm[src][dst] = ((rnd - min_) / (max_ - min_)) * outgoing * self.network_load
                    tm[src][dst] = rnd * tm_scale_factor
                    assert (tm[src][dst] >= 0.0)
                    # print("current volume ", tm[src][dst])
                else:
                    mu = 0.001 * outgoing
                    std = outgoing / 6.0

                    while True:
                        rnd = np.random.normal(mu, std)
                        while rnd < 0.0:
                            rnd = np.random.normal(mu, std)
                        break

                    # tm[src][dst] = ((rnd - min_) / (max_ - min_)) * outgoing * self.network_load
                    tm[src][dst] = rnd * tm_scale_factor
                    assert (tm[src][dst] >= 0.0)
        self.matrices_sequence.append(copy.deepcopy(self.tm))
        return self.tm

    def generateGravityTM(self):

        for s in self.topo.nodes():
            self.tm[s] = {}
            for d in self.topo.nodes():
                self.tm[s][d] = 0.0

        Cap = {}
        totalcap = 0
        for src in self.topo.nodes():
            cap = 0
            for neighbour in self.topo[src]:
                cap += self.topo[src][neighbour]['capacity']
            Cap[src] = cap
            totalcap += cap

        weight = {}
        for s in self.topo.nodes():
            weight[s] = {}
            for d in self.topo.nodes():
                weight[s][d] = 0.0

        for src in weight:
            outgoing = Cap[src]
            cap = totalcap - Cap[src]
            for dst in weight:
                if dst != src:
                    weight[src][dst] = (tm_scale_factor * outgoing * Cap[dst] / cap)  # * random.gauss(100, 20)
        # for _ in range(self.num_tms):
        for src in self.tm:
            for dst in self.tm:
                if dst != src:
                    # tm[src][dst] = random.gauss(weight[src][dst], weight[src][dst] / 10)  # std = tm[src][dst]/10

                    a, m = 4.0, weight[src][dst]  # shape and mode for pareto distribution
                    self.tm[src][dst] = ((np.random.pareto(a, 1) + 1) * m)[0]  # std = tm[src][dst]/5

        self.matrices_sequence.append(copy.deepcopy(self.tm))
        return self.tm