n = 11  # number of nodes
l = 14  # number of links
delta = 0.0001  # Step size
tm_type = 'gravity'  # 'gravity' or 'bimodal'
tm_scale_factor = 0.0175
num_tms = 1  # number of traffic matrices
epsilon = 0.000001  # stopping criteria
max_iter_num = 3000  # maximum number of iterations


'''other settings '''

TOPOLOGY_SOURCE = 'random'  # 'file', 'random'
TOPOLOGY_PATH = 'data/topologies/random/random_topo2020-09-01-H18-M49-S18.pickle'


DEMAND_SOURCE = 'generate'  # 'file' or 'generate'
demand_path = 'data/demands/saved_demands/20200901-185349'
# demand_path = 'data/demands/dot/demand_AttMpls.dot