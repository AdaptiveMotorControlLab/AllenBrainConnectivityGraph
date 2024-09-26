# modules/data_processing.py

import allensdk
from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
import networkx as nx
from tqdm import tqdm
import numpy as np

# Initialize the MouseConnectivityCache
mcc = MouseConnectivityCache(manifest_file='connectivity/mouse_connectivity_manifest.json')
structure_tree = mcc.get_structure_tree()

def get_filtered_experiments(source_id):
    all_experiments = mcc.get_experiments(injection_structure_ids=[source_id])

    filtered_experiments = [
        exp for exp in all_experiments
        if exp['injection_volume'] >= 0.1  # Minimum injection volume in nL
    ]

    return filtered_experiments

def get_projection_data(source_id, target_id, proj_measure='projection_volume', include_descendants=False, print_regions=False):
    # Get experiments with injections in the source structure
    experiments = get_filtered_experiments(source_id)

    projection_unit = 0
    count = 0

    for exp in tqdm(experiments, desc=f'Processing experiments for source {source_id}', leave=False):
        exp_id = exp['id']

        # Get structure unionizes for the target region
        unionizes = mcc.get_experiment_structure_unionizes(
            experiment_id=exp_id,
            is_injection=False,
            structure_ids=[target_id],
            hemisphere_ids=[3],
            include_descendants=include_descendants
        )

        if print_regions:
            included_structure_ids = unionizes['structure_id'].unique()
            included_structures = structure_tree.get_structures_by_id(included_structure_ids)
            for struct in included_structures:
                print(f"ID: {struct['id']}, Name: {struct['name']}, Acronym: {struct['acronym']}")

        for index, u in unionizes.iterrows():
            projection_unit += u[proj_measure]
            count += 1

    if count > 0:
        avg_ = projection_unit / count
    else:
        avg_ = 0

    return avg_
