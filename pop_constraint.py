#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Population constraint that uses the same population deviation calculation used
in Dave's Redistricting App

Program by Charlie Murphy
'''

from gerrychain.constraints import deviation_from_ideal
from fracking import get_intersections, get_county_field

# Population Deviation
def pop_deviation(partition):
    deviation = deviation_from_ideal(partition)
    key_max = max(deviation.keys(), key = (lambda k: deviation[k]))
    key_min = min(deviation.keys(), key = (lambda k: deviation[k]))
    popdev = abs(deviation[key_max] + abs(deviation[key_min]))
    return popdev

# Population Constraint
def pop_constraint(max_pop_deviation):
    return lambda p: pop_deviation(p) <= max_pop_deviation

# Find edge between the districts with the maximum population deviation
def get_edge(partition):
    return max(partition["cut_edges"], key=lambda x: 
        abs(abs(partition["population"][partition.assignment[x[1]]]) - 
        abs(partition["population"][partition.assignment[x[0]]])) )

# Get districts with the greatest population deviation
def get_districts(partition):
    edge = get_edge(partition)
    return (partition.assignment[edge[0]], partition.assignment[edge[1]])

# Get subgraph of counties that the districts split
def get_pop_subgraph(partition):

    # Get the name of the column with county information
    county_field = get_county_field(partition)

    pop_field = 'POP20'

    # Get the pieces splitting by both district and county boundaries
    locality_intersections = get_intersections(partition, county_field)

    # Get the districts and county with the greatest population deviation
    edge = get_edge(partition)
    districts = (partition.assignment[edge[0]], partition.assignment[edge[1]])
    county = partition.graph.nodes[edge[0]][county_field]

    # Get the subgraph
    pop_subgraph = []
    for locality in locality_intersections:
        for d in locality_intersections[locality]:
            subgraph = partition.graph.subgraph(    
                [x for x in partition.parts[d]
                    if partition.graph.nodes[x][county_field] == locality]
            )
            
            # Add nodes if they are in the districts and county
            for node in subgraph:
                if (partition.assignment[node] in districts and 
                    subgraph.nodes[node][county_field] == county):
                    pop_subgraph.append(subgraph.nodes)
                break

    # Calculate population target for each district
    pop_target = (partition["population"][districts[0]] + \
        partition["population"][districts[1]]) / 2

    # Get the current population of each subgrpah
    populations = []
    for subgraph in pop_subgraph:
        current_pop = 0
        for node in subgraph:
            current_pop += partition.graph.nodes[node][pop_field]
        populations.append(current_pop)

    # Find the target population for the portion of the district in each 
    # subgraph
    new_pop = []
    for i in range(2):
        goal = pop_target - partition["population"][districts[i]] + populations[i]
        if goal <= 0:
            print("Error: Nonpositive population target")
        new_pop.append(goal)

    return districts, partition.graph.subgraph(
        pop_subgraph[0] | pop_subgraph[1]), new_pop
