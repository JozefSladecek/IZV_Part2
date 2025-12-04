#!/usr/bin/env python3
# coding=utf-8

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import zipfile

from matplotlib.dates import MonthLocator


# muzete pridat libovolnou zakladni knihovnu ci knihovnu predstavenou na prednaskach
# dalsi knihovny pak na dotaz

# Ukol 1: nacteni dat ze ZIP souboru


def load_data(filename : str, ds : str) -> pd.DataFrame:
    """
    Load data from ZIP file containing XLS files (in HTML format).

    Args:
        filename: Path to the ZIP file
        ds: Dataset name without "I" prefix (e.g. "nehody", "nasledky")

    Returns:
        DataFrame containing merged data from all years 2023-2025
    """
    years = ['2023', '2024', '2025']
    dataframe = []

    with zipfile.ZipFile(filename, "r") as zip_file:
        for year in years:
            file_path = f"{year}/I{ds}.xls"
            with zip_file.open(file_path) as file:
                df = pd.read_html(file, encoding='cp1250')[0]

                dataframe.append(df)

    result = pd.concat(dataframe, ignore_index=True)
    result = result.loc[:, ~result.columns.str.contains('^Unnamed')] #delete

    return result


# Ukol 2: zpracovani dat
def parse_data(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    """
    Parse and clean accident data, add date and region columns.

    Creates a new DataFrame with added 'date' and 'region' columns,
    removes duplicates by accident ID (p1), and optionally prints
    memory usage information.

    Args:
        df: Raw dataframe from load_data with ds="nehody"
        verbose: If True, print memory usage information

    Returns:
        Cleaned DataFrame with added 'date' and 'region' columns
    """
    new_df = df.copy()
    new_df['date'] = pd.to_datetime(new_df['p2a'], format='%d.%m.%Y')

    region = {
        0: "PHA", 1: "STC", 2: "JHC", 3: "PLK", 4: "ULK", 5: "HKK",
        6: "JHM", 7: "MSK", 14: "OLK", 15: "ZLK", 16: "VYS", 17: "PAK",
        18: "LBK", 19: "KVK"
    }

    new_df['region'] = new_df['p4a'].map(region)
    new_df = new_df.drop_duplicates(subset='p1').reset_index(drop=True)

    if verbose:
        memory_bytes = new_df.memory_usage(deep=True).sum()
        memory_mb = memory_bytes / 1_000_000
        print(f"new_size={memory_mb:.1f} MB")

    return new_df

# Ukol 3: počty nehod v jednotlivých regionech podle stavu řidiče
def plot_state(df: pd.DataFrame, df_vehicles: pd.DataFrame,
               fig_location: str = None, show_figure: bool = False):
    """
    Plot accident counts by driver state across regions.

    Creates a 3x2 grid of bar charts showing accident counts for
    driver states 3-8 (p57 column) across all Czech regions.

    Args:
        df: Parsed accident dataframe from parse_data()
        df_vehicles: Vehicle dataframe containing driver state (p57)
        fig_location: Path to save figure (optional)
        show_figure: If True, display the figure
    """
    merged = df.merge(df_vehicles[['p1', 'p57']], on='p1', how='inner')
    merged_filtered = merged[merged['p57'].isin([3, 4, 5, 6, 7, 8])].copy()

    state_titles = {
        3: 'Stav řidiče: pod vlivem léků, narkotik',
        4: 'Stav řidiče: pod vlivem alkoholu do 0,99 ‰',
        5: 'Stav řidiče: pod vlivem alkoholu 1 ‰ a více',
        6: 'Stav řidiče: nemoc, úraz apod.',
        7: 'Stav řidiče: invalida',
        8: 'Stav řidiče: řidič při jízdě zemřel (infarkt apod.)',
    }

    grouped = merged_filtered.groupby(['region', 'p57']).size().reset_index(name='count')

    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(12, 10))
    fig.patch.set_facecolor('#E8F4F8')
    axes = axes.flatten()

    regions = ['HKK', 'JHC', 'JHM', 'KVK', 'LBK', 'MSK', 'OLK',
               'PAK', 'PHA', 'PLK', 'STC', 'ULK', 'VYS', 'ZLK']
    colors = plt.cm.tab20(range(14))
    region_colors = dict(zip(regions, colors))

    for idx, state in enumerate([3, 4, 5, 6, 7, 8]):
        ax = axes[idx]
        state_data = grouped[grouped['p57'] == state]

        x_positions = range(len(regions))
        heights = []
        for reg in regions:
            reg_data = state_data[state_data['region'] == reg]
            if len(reg_data) > 0:
                heights.append(reg_data['count'].values[0])
            else:
                heights.append(0)

        bar_colors = [region_colors[reg] for reg in regions]

        ax.set_facecolor('#E8F4F8')
        ax.grid(axis='y', alpha=0.7, linestyle='--', linewidth=0.5, zorder=0)
        ax.bar(x_positions, heights, color=bar_colors, width=0.8, zorder=3)

        ax.set_xlim(-0.5, len(regions) - 0.5)
        ax.set_title(state_titles[state], fontsize=10, pad=10)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(regions, fontsize=8)
        ax.set_xlabel('Kraj', fontsize=9)
        ax.set_ylabel('Počet nehod', fontsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

        ax.tick_params(axis='both', which='both', length=0)

    plt.tight_layout()
    fig.patch.set_facecolor('white')

    if fig_location:
        plt.savefig(fig_location, dpi=150, bbox_inches='tight')

    if show_figure:
        plt.show()
    else:
        plt.close()

# Ukol 4: alkohol a roky v krajích
def plot_alcohol(df: pd.DataFrame, df_consequences: pd.DataFrame,
                 fig_location: str = None, show_figure: bool = False):
    """
    Plot alcohol-related accidents by injury type, region and year.

    Creates a 2x2 grid of bar charts showing counts of alcohol-related
    accidents (p11 >= 3) for each injury type (p59g) across regions
    and years. Only includes data up to October to ensure fair comparison.

    Args:
        df: Parsed accident dataframe from parse_data()
        df_consequences: Consequences dataframe with injury types (p59g)
        fig_location: Path to save figure (optional)
        show_figure: If True, display the figure
    """
    merged = df.merge(df_consequences[['p1', 'p59g']], on='p1', how='inner')
    merged_alcohol = merged[merged['p11'] >= 3].copy()

    merged_alcohol['year'] = merged_alcohol['date'].dt.year
    merged_alcohol['month'] = merged_alcohol['date'].dt.month
    merged_filtered = merged_alcohol[merged_alcohol['month'] <= 10].copy()

    injury_map = {
        1: 'Usmrcení',
        2: 'Těžké zranění',
        3: 'Lehké zranění',
        4: 'Bez zranění'
    }
    merged_filtered['injury_type'] = merged_filtered['p59g'].map(injury_map)

    grouped = merged_filtered.groupby(['region', 'year', 'injury_type']).size().reset_index(name='count')

    col_order_list = ['Bez zranění', 'Lehké zranění', 'Těžké zranění', 'Usmrcení']

    g = sns.catplot(
        data=grouped,
        x='region',
        y='count',
        hue='year',
        col='injury_type',
        kind='bar',
        col_wrap=2,
        col_order=col_order_list,
        height=4,
        aspect=1.5,
        sharey=False,
        palette=['#6B4C9A', '#45B7B8', '#F4D03F'],
        legend=True
    )

    for ax, injury_type in zip(g.axes.flat, col_order_list):
        ax.set_title(f'Následky nehody: {injury_type}', fontsize=12, pad=10)
        ax.set_xlabel('Kraj', fontsize=10)
        ax.set_ylabel('Počet nehod pod vlivem', fontsize=10)
        ax.tick_params(axis='x', labelsize=8, rotation=0, length=0)
        ax.tick_params(axis='y', labelsize=8, length=0)
        ax.set_facecolor('#E8E8F0')
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5, zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

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

    g.fig.tight_layout()
    g.fig.subplots_adjust(top=0.95, right=0.9)

    if fig_location:
        g.fig.savefig(fig_location, dpi=150, bbox_inches='tight')

    if show_figure:
        plt.show()
    else:
        plt.close()

# Ukol 5: Podmínky v čase
def plot_conditions(df: pd.DataFrame, fig_location: str = None,
                    show_figure: bool = False):
    selected_regions = ['JHM', 'MSK', 'OLK', 'ZLK']
    df_filtered = df[df['region'].isin(selected_regions)].copy()

    conditions_map = {
        0: 'jiné',
        1: 'neztížené',
        2: 'mlha',
        3: 'na počátku deště',
        4: 'déšť',
        5: 'sněžení',
        6: 'náledí',
        7: 'vítr'
    }

    custom_palette = {
        'neztížené': '#E74C3C',
        'déšť': '#3498DB',
        'sněžení': '#2ECC71',
        'mlha': '#F39C12',
        'na počátku deště': '#9B59B6',
        'náledí': '#16A085',
        'vítr': '#D35400',
        'jiné': '#7F8C8D'
    }

    df_filtered['condition'] = df_filtered['p18'].map(conditions_map)
    df_filtered['count'] = 1

    grouped = df_filtered.groupby([pd.Grouper(key='date', freq='MS'), 'region', 'condition'])[
        'count'].sum().reset_index()
    grouped = grouped[(grouped['date'] >= '2023-01-01') & (grouped['date'] <= '2025-01-01')]

    g = sns.relplot(
        data=grouped,
        x='date',
        y='count',
        hue='condition',
        col='region',
        col_order=['JHM', 'MSK', 'OLK', 'ZLK'],
        kind='line',
        col_wrap=2,
        height=4,
        aspect=1.75,
        linewidth=1.5,
        facet_kws={'xlim': (pd.Timestamp('2023-01-01'), pd.Timestamp('2025-01-01'))},
        palette=custom_palette
    )

    from matplotlib.dates import num2date



    for ax in g.axes.flat:
        ax.set_ylabel('Počet nehod', fontsize=10)
        ax.tick_params(labelbottom=True)
        ax.set_yticks(range(0, 1100, 200))
        ax.set_ylim(0, 1000)
        ax.tick_params(axis='both', which='both', length=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.set_xlim(pd.Timestamp('2023-01-01'), pd.Timestamp('2025-01-01'))


        # num2date
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: num2date(x).strftime('%m/%y') if x else ''))
        ax.tick_params(axis='x', pad=10)
        ax.grid(True, color='white', linewidth=2)
        ax.set_facecolor('#F5F5FF')

    g.set_titles('Kraj: {col_name}', fontsize=12)
    g.legend.set_title('Podmínky')

    plt.tight_layout()
    g.fig.subplots_adjust(right=0.85)

    if fig_location:
        g.fig.savefig(fig_location, dpi=150, bbox_inches='tight')

    if show_figure:
        plt.show()
    else:
        plt.close()


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

    plot_state(df2, df_vehicles, "01_state.png",True)
    #plot_alcohol(df2, df_consequences, "02_alcohol.png",True)
    #plot_conditions(df2, "03_conditions.png",True)
    with zipfile.ZipFile("data_23_25.zip", 'r') as zip_file:
        with zip_file.open("2023/Inasledky.xls") as file:
            df_sample = pd.read_html(file, encoding='cp1250')[0]


# Poznamka:
# pro to, abyste se vyhnuli castemu nacitani muzete vyuzit napr
# VS Code a oznaceni jako bunky (radek #%%% )
# Pak muzete data jednou nacist a dale ladit jednotlive funkce
# Pripadne si muzete vysledny dataframe ulozit nekam na disk (pro ladici
# ucely) a nacitat jej naparsovany z disku
