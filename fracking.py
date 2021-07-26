#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 15 July 2020
Program designed to check whether or not counties are fracked in a redistricting
plan created using GerryChain

Program by Charlie Murphy
'''

from gerrychain.constraints import contiguous
from gerrychain.updaters import county_splits
import networkx as nx
import random

# Get name of field with county information
def get_county_field(partition):

    fieldlist = partition.graph.nodes[0].keys()
    
    if 'COUNTYFP10' in fieldlist:
        county_field = 'COUNTYFP10'
    elif 'COUNTYFP20' in fieldlist:
        county_field = 'COUNTYFP20'
    elif 'CTYNAME' in fieldlist:
        county_field = 'CTYNAME'
    elif 'COUNTYFIPS' in fieldlist:
        county_field = 'COUNTYFIPS'
    elif 'COUNTYFP' in fieldlist:
        county_field = 'COUNTYFP'
    elif 'cnty_nm' in fieldlist:
        county_field = 'cnty_nm'
    elif 'county_nam' in fieldlist:
        county_field = 'county_nam'
    elif 'FIPS2' in fieldlist:
        county_field = 'FIPS2'
    elif 'COUNTY' in fieldlist:
        county_field = 'COUNTY'
    elif 'County' in fieldlist:
        county_field = 'County'   
    elif 'CNTY_NAME' in fieldlist:
        county_field = 'CNTY_NAME'
    else:
        print("no county ID info in shapefile")
    
    return county_field

# Return a boolean value on whether or not a possible redistricting plan is 
# fracked. A redistricting plan is consider fracked if at least one district
# is discontinuous within a county
def fracking(partition):

    # Get column with counties
    county_field = get_county_field(partition)

    # Get a dictionary with the number of county splits
    county_splits_dict = county_splits(partition, county_field)(partition)

    # Get the number of pieces if the county was not fracked
    expected_pieces = 0
    for x in county_splits_dict:
        expected_pieces += len(county_splits_dict[x].contains)

    # Get the number of pieces that actually exist in the redistricting plan
    pieces = num_pieces(partition, county_field)

    return pieces - expected_pieces

# If you are also calculating the total number of splits in your chain, it is
# more efficient to compute thesse two numbers together isntead of looping
# through the dictionary of county splits twice
def fracking_total_splits(partition):

    # Get column with counties
    county_field = get_county_field(partition)

    # Get a dictionary with the number of county splits
    county_splits_dict = county_splits(partition, county_field)(partition)

    # Get the number of pieces if the county was not fracked and the total
    # number of county splits
    expected_pieces = split_count = 0
    for x in county_splits_dict:
        districts = len(county_splits_dict[x].contains)
        expected_pieces += districts
        split_count += districts - 1

    # Get the number of pieces that actually exist in the redistricting plan
    pieces = num_pieces(partition, county_field)

    return pieces - expected_pieces, split_count

# This version is for use in chain_xtended_pop_balance and chain_xtended_fracking
def fracking_merge(partition, d1, d2):

    # Get column with counties
    county_field = get_county_field(partition)

    # Get a dictionary with the number of county splits
    county_splits_dict = county_splits(partition, county_field)(partition)

    # Get the number of pieces if the county was not fracked and the total
    # number of county splits
    expected_pieces = split_count = merged_district_count = 0
    for x in county_splits_dict:
        districts = county_splits_dict[x].contains
        district_num = len(districts)
        expected_pieces += district_num
        split_count += district_num - 1

        # Count number of counties split between both districts
        if d1 in districts and d2 in districts:
            merged_district_count += 1

    # Get the number of pieces that actually exist in the redistricting plan
    pieces = num_pieces(partition, county_field)

    return pieces - expected_pieces, merged_district_count, split_count

# Split state by both county and district boundaries
def get_intersections(partition, col_id):

    locality_intersections = {}

    for n in partition.graph.nodes():
        locality = partition.graph.nodes[n][col_id]
        if locality not in locality_intersections:
            locality_intersections[locality] = set(
                [partition.assignment[n]])

        locality_intersections[locality].update([partition.assignment[n]])

    return locality_intersections

# Gets the total number of pieces, where each piece is formed by
# cutting the graph by both county and district boundaries.
# Adapted from locality_split_scores.py
def num_pieces(partition, col_id):
    
    locality_intersections = get_intersections(partition, col_id)

    pieces = 0
    for locality in locality_intersections:
        for d in locality_intersections[locality]:
            subgraph = partition.graph.subgraph(    
                [x for x in partition.parts[d]
                    if partition.graph.nodes[x][col_id] == locality]
            )

            pieces += nx.number_connected_components(subgraph)

    return pieces

# Return the district number of 2 districts that share a county where at least
# one of them is fracked
def get_fracks(partition):
    
    # Get the column with the county information in it
    county_field = get_county_field(partition)

    # Get the pieces splitting by both district and county boundaries
    locality_intersections = get_intersections(partition, county_field)

    # Get a dictionary with the districts within each county
    county_splits_dict = county_splits(partition, county_field)(partition) 

    # Get the subgraph for each county
    for locality in locality_intersections:
        for d in locality_intersections[locality]:
            subgraph = partition.graph.subgraph(    
                [x for x in partition.parts[d]
                    if partition.graph.nodes[x][county_field] == locality]
            )

            # If the county is fracked, return districts in that county
            if nx.number_connected_components(subgraph) != 1:
                for node in subgraph:
                    county = partition.graph.nodes[node][county_field]
                    districts = county_splits_dict[county].contains

                    # If there are only two districts return those districts
                    if len(districts) == 2:
                        return tuple(districts)

                    # Otherwise, find a district that borders frack
                    d1 = partition.assignment[node]
                    while True:
                        edge = random.choice(tuple(partition["cut_edges"]))
                        edge_districts = (partition.assignment[edge[0]], 
                            partition.assignment[edge[1]])
                        edge_counties = (partition.graph.nodes[edge[0]][county_field], 
                            partition.graph.nodes[edge[1]][county_field])
                        if (d1 in edge_districts 
                            and edge_counties == (county, county)):
                            return edge_districts
