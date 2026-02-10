"""
<<main.py>>
This project is related to clustering and routing problem in VANET
"""
author: str = "Pouya 'Adrian' Firouzmakan"

import time
import gc
import random

import numpy as np
import pandas as pd

from data_cluster import DataTable
from configs.config import Configs
from zonex import ZoneID


def run_one_case_inplace(configs, veh_trans_range, weights, seed=1234):
    """
    Runs ONE case, resetting by:
      - saving original configs fields
      - setting case fields
      - rebuilding ZoneID + DataTable (fresh state)
      - restoring original configs fields
    This avoids deepcopy recursion errors.
    """

    # ---- reset RNG (if simulation uses randomness)
    random.seed(seed)
    np.random.seed(seed)

    # ---- save original config values we will modify
    old_tr = getattr(configs, "veh_trans_range", None)
    old_w = getattr(configs, "weights", None)

    try:
        # ---- set this case parameters
        configs.veh_trans_range = veh_trans_range
        configs.weights = np.array(weights, dtype=float)

        # ---- rebuild EVERYTHING that can hold state
        area_zones = ZoneID(configs)
        area_zones.zones()

        cluster = DataTable(configs, area_zones, train_mode=False)

        n_chs, n_sav = [], []

        for _ in range(configs.iter):
            cluster.update(configs, area_zones)
            cluster.update_cluster(cluster.veh_table.ids(), configs, area_zones)
            cluster.stand_alones_cluster(configs, area_zones)

            n_chs.append(len(cluster.all_chs))
            n_sav.append(len(cluster.stand_alone))

        eval_cluster = cluster.vcsm(configs)

        res = {
            "TR": configs.veh_trans_range,
            "weights": configs.weights.copy(),
            "n_veh": len(cluster.veh_table.ids()),
            "n_buses": len(cluster.bus_table.ids()),
            "n_sav_avg": float(sum(n_sav) / len(n_sav)) if n_sav else 0.0,
            "n_chs_avg": float(sum(n_chs) / len(n_chs)) if n_chs else 0.0,
            "stab_eval": eval_cluster,
        }

        # ---- hard cleanup
        del cluster
        del area_zones
        gc.collect()

        return res

    finally:
        # ---- restore configs to original state (critical!)
        configs.veh_trans_range = old_tr
        configs.weights = old_w


if __name__ == "__main__":
    configs = Configs().config
    dif_tr = [200]

    # -------------------- Generate weight combinations (sum=1, step=0.1) --------------------
    step = 0.1
    possible_values = [round(i * step, 1) for i in range(int(1 / step) + 1)]
    all_weight_lists = []

    for val1 in possible_values:
        for val2 in possible_values:
            remaining = round(1 - val1 - val2, 1)
            if remaining in possible_values and remaining >= 0:
                all_weight_lists.append([val1, val2, remaining])
    # ---------------------------------------------------------------------------------------

    start_time = time.time()
    num_times = 1

    for veh_tr in dif_tr:
        cols = ['rsu', 'TR', 'weights', 'n_veh', 'n_buses', 'n_sav', 'n_chs', 'stab_eval']
        out_put = pd.DataFrame(columns=cols)

        for w in all_weight_lists:
            # For fair comparison across weights, keep the seed fixed:
            seed = 1234
            # If you want variability per run, use:
            # seed = 1234 + num_times

            res = run_one_case_inplace(configs, veh_tr, w, seed=seed)

            print(num_times, res["TR"], res["weights"], res["n_veh"], res["n_buses"],
                  res["n_sav_avg"], res["n_chs_avg"], res["stab_eval"])
            num_times += 1

            new_row = pd.Series(
                ['no', res["TR"], res["weights"], res["n_veh"], res["n_buses"],
                 res["n_sav_avg"], res["n_chs_avg"], res["stab_eval"]],
                index=cols
            )
            out_put = pd.concat([out_put, new_row.to_frame().T], ignore_index=True)

        out_put.to_csv(f"results/{veh_tr}_DRU.csv", index=False)

    end_time = time.time()
    print("execution time:", end_time - start_time)