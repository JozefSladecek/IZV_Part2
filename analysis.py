#!/usr/bin/env python3
# coding=utf-8

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import zipfile

# muzete pridat libovolnou zakladni knihovnu ci knihovnu predstavenou na prednaskach
# dalsi knihovny pak na dotaz

# Ukol 1: nacteni dat ze ZIP souboru


def load_data(filename : str, ds : str) -> pd.DataFrame:

    years = ['2023', '2024', '2025']

    dataframe = []

    with (zipfile.ZipFile(filename, "r")) as zip_file:
        for year in years:
            file_path = f"{year}/I{ds}.xls"
            with zip_file.open(file_path) as file:
                df = pd.read_html(file, encoding='cp1250')[0]

                dataframe.append(df) # append dataframe to array

    result = pd.concat(dataframe, ignore_index=True)

    result = result.loc[:, ~result.columns.str.contains('^Unnamed')] # delete unnamed

    # print(f"\n=== Načítanie datasetu '{ds}' ===")
    # print(f"Tvar (riadky, stĺpce): {result.shape}")
    # print(f"Počet riadkov: {len(result)}")
    # print(f"Počet stĺpcov: {len(result.columns)}")
    # print(f"\nNázvy stĺpcov:\n{result.columns.tolist()}")
    # print(f"\nPrvých 5 riadkov:\n{result.head()}")
    # print(f"\nInfo o stĺpcoch:")
    # print(result.info())

    return result


# Ukol 2: zpracovani dat


def parse_data(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:

    new_df = df.copy()
    new_df['date'] = pd.to_datetime(new_df['p2a'], format='%d.%m.%Y') # add date column

    region = {
        0: "PHA", 1: "STC", 2: "JHC", 3: "PLK", 4: "ULK", 5: "HKK",
        6: "JHM", 7: "MSK", 14: "OLK", 15: "ZLK", 16: "VYS", 17: "PAK",
        18: "LBK", 19: "KVK"
    }

    new_df['region'] = new_df['p4a'].map(region) # add region column
    # print(new_df.head())
    new_df = new_df.drop_duplicates(subset='p1').reset_index(drop=True)

    if verbose:
        memory_bytes = new_df.memory_usage(deep=True).sum()

        memory_mb = memory_bytes / 1_000_000 # 10^6
        print(f"new_size={memory_mb:.1f} MB")

# Ukol 3: počty nehod v jednotlivých regionech podle stavu řidiče
def plot_state(df: pd.DataFrame, df_vehicles : pd.DataFrame, fig_location: str = None,
                    show_figure: bool = False):
    merged = df.merge(df_vehicles, on='p1', how='inner') # join tables on same rows

    pass

# Ukol4: alkohol a roky v krajích
def plot_alcohol(df: pd.DataFrame, df_consequences : pd.DataFrame, 
                 fig_location: str = None, show_figure: bool = False):
    pass

# Ukol 5: Podmínky v čase
def plot_conditions(df: pd.DataFrame, fig_location: str = None,
                    show_figure: bool = False):
    pass


if __name__ == "__main__":
    # zde je ukazka pouziti, tuto cast muzete modifikovat podle libosti
    # skript nebude pri testovani pousten primo, ale budou volany konkreni
    # funkce.

    # df = load_data("data_23_25.zip", "nehody")
    # df.to_pickle("df_nehody.pkl")
    # df_consequences = load_data("data_23_25.zip", "nasledky")
    # df_consequences.to_pickle("df_nasledky.pkl")
    # df_vehicles = load_data("data_23_25.zip", "Vozidla")
    # df_vehicles.to_pickle("df_vozidla.pkl")

    # ĎALEJ - používaj toto (rýchle načítanie):
    df = pd.read_pickle("df_nehody.pkl")
    df_consequences = pd.read_pickle("df_nasledky.pkl")
    df_vehicles = pd.read_pickle("df_vozidla.pkl")

    df2 = parse_data(df, True)

    plot_state(df2, df_vehicles, "01_state.png")
    #plot_alcohol(df2, df_consequences, "02_alcohol.png", True)
    plot_conditions(df2, "03_conditions.png")

# Poznamka:
# pro to, abyste se vyhnuli castemu nacitani muzete vyuzit napr
# VS Code a oznaceni jako bunky (radek #%%% )
# Pak muzete data jednou nacist a dale ladit jednotlive funkce
# Pripadne si muzete vysledny dataframe ulozit nekam na disk (pro ladici
# ucely) a nacitat jej naparsovany z disku
