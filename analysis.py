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

    return new_df

# Ukol 3: počty nehod v jednotlivých regionech podle stavu řidiče
def plot_state(df: pd.DataFrame, df_vehicles: pd.DataFrame, fig_location: str = None,
               show_figure: bool = False):
    # Merge accident data with vehicle data on accident ID
    merged = df.merge(df_vehicles[['p1', 'p57']], on='p1', how='inner')

    # Filter only states 3-8 (excluding state 9 as it has minimal data)
    merged_filtered = merged[merged['p57'].isin([3, 4, 5, 6, 7, 8, 9])].copy()
    state_titles = {
        3: 'Stav řidiče: pod vlivem léků, narkotik',
        4: 'Stav řidiče: pod vlivem alkoholu do 0,99 ‰',
        5: 'Stav řidiče: pod vlivem alkoholu 1 ‰ a více',
        6: 'Stav řidiče: nemoc, úraz apod.',
        7: 'Stav řidiče: invalida',
        8: 'Stav řidiče: řidič při jízdě zemřel (infarkt apod.)',
    }

    # Aggregate: count accidents for each (region, p57) combination
    grouped = merged_filtered.groupby(['region', 'p57']).size().reset_index(name='count')

    # Create figure with 6 subplots
    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(12, 10))
    fig.patch.set_facecolor('#E8F4F8')  # light blue
    axes = axes.flatten()

    # Define colors for each region (14 regions total)
    regions = ['HKK', 'JHC', 'JHM', 'KVK', 'LBK', 'MSK', 'OLK',
               'PAK', 'PHA', 'PLK', 'STC', 'ULK', 'VYS', 'ZLK']
    colors = plt.cm.tab20(range(14))  # 14 distinct colors
    region_colors = dict(zip(regions, colors))

    # Create subplot
    for idx, state in enumerate([3, 4, 5, 6, 7, 8]):
        ax = axes[idx]

        # Filter data for current state
        state_data = grouped[grouped['p57'] == state]

        # Prepare data for bar chart: X-axis = regions, Y-axis = accident count
        x_positions = range(len(regions))
        heights = []
        for reg in regions:
            reg_data = state_data[state_data['region'] == reg]
            if len(reg_data) > 0:
                heights.append(reg_data['count'].values[0])
            else:
                heights.append(0)

        bar_colors = [region_colors[reg] for reg in regions]

        # Draw bar chart
        ax.bar(x_positions, heights, color=bar_colors, width=0.8)

        ax.set_title(state_titles[state], fontsize=10, pad=10)

        # Configure X-axis
        ax.set_xticks(x_positions)
        ax.set_xticklabels(regions, fontsize=8)
        ax.set_xlabel('Kraj', fontsize=9)

        # Configure Y-axis
        ax.set_ylabel('Počet nehod', fontsize=9)
        ax.tick_params(axis='y', labelsize=8)

        # Set subplot background and grid
        ax.set_facecolor('#E8F4F8')
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)

    # Adjust layout and spacing
    plt.tight_layout()

    if fig_location:
        plt.savefig(fig_location, dpi=150, bbox_inches='tight')

    if show_figure:
        plt.show()
    else:
        plt.close()


# Ukol4: alkohol a roky v krajích
def plot_alcohol(df: pd.DataFrame, df_consequences : pd.DataFrame,
                 fig_location: str = None, show_figure: bool = False):

    merged = df.merge(df_consequences[['p1', 'p59g']], on='p1', how='inner')

    merged_alcohol = merged[merged['p11'] >= 3].copy() # filter

    # Extract year and month
    merged_alcohol['year'] = merged_alcohol['date'].dt.year
    merged_alcohol['month'] = merged_alcohol['date'].dt.month

    merged_filtered = merged_alcohol[merged_alcohol['month'] <= 10].copy() #exclude december, november

    injury_map = {
        1: 'Usmrcení',
        2: 'Těžké zranění',
        3: 'Lehké zranění',
        4: 'Bez zranění'
    }
    merged_filtered['injury_type'] = merged_filtered['p59g'].map(injury_map)

    grouped = merged_filtered.groupby(['region', 'year', 'injury_type']).size().reset_index(name='count') # agregation
    g = sns.catplot(
        data=grouped,
        x='region',
        y='count',
        hue='year',
        col='injury_type',
        kind='bar',
        col_wrap=2,  # 2 columns
        col_order=['Usmrcení', 'Těžké zranění', 'Lehké zranění', 'Bez zranění'],
        height=4,
        aspect=1.5,
        sharey=False, #Independent Y-axes!
        palette=['#6B4C9A', '#45B7B8', '#F4D03F'],  # Purple, Teal, Yellow
        legend=True  # Custom
    )

    for ax, injury_type in zip(g.axes.flat, injury_map.values()):
        ax.set_title(f'Následky nehody: {injury_type}', fontsize=12, pad=10)
        ax.set_xlabel('Kraj', fontsize=10)
        ax.set_ylabel('Počet nehod pod vlivem', fontsize=10)
        ax.tick_params(axis='x', labelsize=8, rotation=0)
        ax.tick_params(axis='y', labelsize=8)
        ax.set_facecolor('#E8E8F0')  # Light purple background
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)

    if g.legend:
        g.legend.remove()

    g.fig.legend(
        title='Rok',
        loc='center right',
        bbox_to_anchor=(0.99, 0.5),
        fancybox=False,
        shadow=False,
        frameon=False,
        fontsize=10,
        title_fontsize=11
    )
    # Layout to prevent overlap
    g.fig.tight_layout()
    g.fig.subplots_adjust(top=0.95)
    g.fig.subplots_adjust(right=0.9)

    if fig_location:
        g.fig.savefig(fig_location, dpi=150, bbox_inches='tight')

    if show_figure:
        plt.show()
    else:
        plt.close()

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
    plot_alcohol(df2, df_consequences, "02_alcohol.png", True)
    plot_conditions(df2, "03_conditions.png")
    with zipfile.ZipFile("data_23_25.zip", 'r') as zip_file:
        with zip_file.open("2023/Inasledky.xls") as file:
            df_sample = pd.read_html(file, encoding='cp1250')[0]


# Poznamka:
# pro to, abyste se vyhnuli castemu nacitani muzete vyuzit napr
# VS Code a oznaceni jako bunky (radek #%%% )
# Pak muzete data jednou nacist a dale ladit jednotlive funkce
# Pripadne si muzete vysledny dataframe ulozit nekam na disk (pro ladici
# ucely) a nacitat jej naparsovany z disku
