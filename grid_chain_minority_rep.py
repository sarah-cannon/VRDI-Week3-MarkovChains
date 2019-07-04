# Template by Sarah Cannon
# Based on simple_chain.py by Darryl DeFord


import random

# import matplotlib
# matplotlib.use('Agg')

import matplotlib.pyplot as plt
from functools import partial
import networkx as nx


from gerrychain import MarkovChain
from gerrychain.constraints import (
    Validator,
    single_flip_contiguous,
    within_percent_of_ideal_population,
)
from gerrychain.proposals import propose_random_flip
from gerrychain.accept import always_accept
from gerrychain.updaters import Election, Tally, cut_edges
from gerrychain.partition import Partition
from gerrychain.proposals import recom
from gerrychain.metrics import mean_median, efficiency_gap


# BUILD GRAPH
n = 10 # side length of grid
k = 10 #Number of Districts
m = n**2/k #Number of nodes per district
rho = 0.4 # Minority Fraction
l = rho * n**2 # Number of minority voters: May run into problems if this isn't an integer

ns = 50 # Node Size for drawing plans

# Create  n x n Grid Graph
graph = nx.grid_graph([n,n])

# this part adds queen adjacency
# for i in range(k*gn-1):
#    for j in range(k*gn):
#        if j<(k*gn-1):
#            graph.add_edge((i,j),(i+1,j+1))
#            graph[(i,j)][(i+1,j+1)]["shared_perim"]=0
#        if j >0:
#            graph.add_edge((i,j),(i+1,j-1))
#            graph[(i,j)][(i+1,j-1)]["shared_perim"]=0




# Initialization steps
for vertex in graph.nodes():
    # Set each vertex in the graph to have population 1
    graph.node[vertex]["population"] = 1
 
    # Seteach vertex as a minority (pink) or majority (purple) voter
    # For different voter distributions, change here: 
#    if vertex[0] < rho*n:
#        graph.node[vertex]["pink"] = 1
#        graph.node[vertex]["purple"] = 0
#    else:
#        graph.node[vertex]["pink"] = 0
#        graph.node[vertex]["purple"] = 1

     #Set each node to be minority or majority with probability 0.4
     # WILL NOT necessarily result in exactly 40 minority nodes
#     p = 0.4
#    if random.random() < p:
#        graph.node[n]["pink"] = 1
#        graph.node[n]["purple"] = 0
#    else:
#        graph.node[n]["pink"] = 0
#        graph.node[n]["purple"] = 1
     
     # The voter configuration called Henry
     # For 10 x 10 grid
    Henry = [[1,1,0,0,0,0,0,0,1,1],[1,1,1,1,1,1,1,1,1,0],[0,1,0,0,0,1,1,1,0,0],[1,0,0,1,1,0,0,0,1,1],[0,0,1,1,1,1,1,0,1,0],[0,1,1,1,0,1,1,1,1,0],[0,1,0,0,0,1,0,1,1,1],[0,1,0,1,1,1,1,1,1,0],[0,1,1,1,0,0,1,1,1,0],[1,1,1,0,1,1,1,1,0,0]]
    if Henry[9-vertex[1]][vertex[0]] == 0:
        graph.node[vertex]["pink"] = 1
        graph.node[vertex]["purple"] = 0
    else:
        graph.node[vertex]["pink"] = 0
        graph.node[vertex]["purple"] = 1    



# ######### BUILD ASSIGNMENT
    # THis is your initial districting plane
# This starts at the columns plan    
cddict = {x: int(x[0] / (n/k)) for x in graph.nodes()}


# #####PLOT GRIDS

cdict = {1: "pink", 0: "purple"}

# Draws dual graph coloring nodes by their vote preference (minority/majority)
plt.figure()
nx.draw(
    graph,
    pos={x: x for x in graph.nodes()},
    node_color=[cdict[graph.node[x]["pink"]] for x in graph.nodes()],
    node_size=ns,
    node_shape="s",
)
plt.show()

# Draws initial districting plan
plt.figure()
nx.draw(
    graph,
    pos={x: x for x in graph.nodes()},
    node_color=[cddict[x] for x in graph.nodes()],
    node_size=ns,
    node_shape="s",
    cmap="tab20",
)
plt.show()


# ###CONFIGURE UPDATERS
def step_num(partition):
    parent = partition.parent
    if not parent:
        return 0
    return parent["step_num"] + 1

def rook_cut_edges(partition):
    cut_edge_set = set()
    assign = partition.assignment
    for vertex in graph.nodes():
        if vertex[0]<n-1:
            neighbor = (vertex[0]+1,vertex[1])
            if assign[vertex]!=assign[neighbor]:
                cut_edge_set.add((vertex,neighbor))
        if vertex[1]<n-1:
            neighbor = (vertex[0],vertex[1]+1)
            if assign[vertex]!=assign[neighbor]:
                cut_edge_set.add((vertex,neighbor))
    return cut_edge_set


updaters = {
    "population": Tally("population"),
    "cut_edges": cut_edges,
    "step_num": step_num,
    "Pink-Purple": Election("Pink-Purple", {"Pink": "pink", "Purple": "purple"}),
    "rook_cut_edges": rook_cut_edges
}


# ########BUILD PARTITION

grid_partition = Partition(graph, assignment=cddict, updaters=updaters)

# ADD CONSTRAINTS
# FOr our 10x10 grid, will only allow districts of exactly 10 vertices
popbound = within_percent_of_ideal_population(grid_partition, 0.1)

# ########Setup Proposal
ideal_population = sum(grid_partition["population"].values()) / len(grid_partition)

tree_proposal = partial(
    recom,
    pop_col="population",
    pop_target=ideal_population,
    epsilon=0.05,
    node_repeats=1,
)

# ######BUILD MARKOV CHAINS
numIters = 10000

recom_chain = MarkovChain(
    tree_proposal,
    Validator([popbound]),
    accept=always_accept,
    initial_state=grid_partition,
    total_steps=numIters,
)




# ########Run MARKOV CHAINS

rsw = []
rmm = []
reg = []
rce = []

expectednumberseats = 0

for part in recom_chain:
    rsw.append(part["Pink-Purple"].wins("Pink"))
    # Caluculate number of ties
    ties = (part["Pink-Purple"].wins("Pink")+ part["Pink-Purple"].wins("Purple") - k)
    # Calculate number of pink seats won, add to expected value
    expectednumberseats += part["Pink-Purple"].wins("Pink") - ties/2
    rmm.append(mean_median(part["Pink-Purple"]))
    reg.append(efficiency_gap(part["Pink-Purple"]))
    rce.append(len(part["cut_edges"]))
    # plt.figure()
    # nx.draw(
    #     graph,
    #     pos={x: x for x in graph.nodes()},
    #     node_color=[dict(part.assignment)[x] for x in graph.nodes()],
    #     node_size=ns,
    #     node_shape="s",
    #     cmap="tab20",
    # )
    # plt.savefig(f"./Figures/recom_{part['step_num']:02d}.png")
    # plt.close()
    
expectednumberseats = expectednumberseats/numIters
print("Based on ", numIters, " recom steps, the expected number of minority seats is ", expectednumberseats)

# Show final districting plan
plt.figure()
nx.draw(
    graph,
    pos={x: x for x in graph.nodes()},
    node_color=[dict(part.assignment)[x] for x in graph.nodes()],
    node_size=ns,
    node_shape="s",
    cmap="tab20",
)
plt.show()

# #################Partisan Plots
# Histogram of number of wins by minority 
plt.hist(rsw) 
plt.title("ReCom Ensemble: Number Minority Seats Won")

plt.show()
