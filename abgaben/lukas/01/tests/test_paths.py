from pathlib import Path

from hydro.paths import find_data_root, observation_csv, simulation_csv, topography_csv


def test_find_data_root_walks_upwards(tmp_path: Path):
    data = tmp_path / "data" / "camels_ch"
    data.mkdir(parents=True)
    start = tmp_path / "abgaben" / "lukas" / "01"
    start.mkdir(parents=True)
    assert find_data_root(start) == data


def test_paths_follow_camels_layout(tmp_path: Path):
    assert observation_csv(tmp_path, 2303) == (
        tmp_path / "timeseries" / "observation_based" / "CAMELS_CH_obs_based_2303.csv"
    )
    assert simulation_csv(tmp_path, 2303) == (
        tmp_path / "timeseries" / "simulation_based" / "CAMELS_CH_sim_based_2303.csv"
    )
    assert topography_csv(tmp_path).name == "CAMELS_CH_topographic_attributes.csv"
