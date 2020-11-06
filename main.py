from config import num_tms
from topology import Topology
from trafficgeenrator import TrafficGenerator
from simulator import Simulater
from config import n, l
import time

def main():
    topo_obj = Topology(n, l)
    topo = topo_obj.topo
    traffic_generator_obj = TrafficGenerator(topo)

    simulator_obj = Simulater(topo)

    for i in range(traffic_generator_obj.num_tms):
        tm = next(traffic_generator_obj)

        print("tm number: ", i)
        print(tm)
        time.sleep(0.5)
        simulator_obj.simulate(tm)


if __name__ == '__main__':
    main()
