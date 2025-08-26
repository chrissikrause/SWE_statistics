import pandas as pd
from pathlib import Path

# Path to the folder
folder_path = Path(r"C:\Users\schi_sm\Downloads\Trend_Data\Trend_Data\trend_swe_params")

# Initialize empty DataFrames
df_trends = pd.DataFrame()
df_means = pd.DataFrame()

# Loop through all CSV files in the folder
for csv_file in folder_path.glob("trend_results_*.csv"):
    # Extract variable name from the filename
    variable_name = csv_file.stem.replace("trend_results_", "")
    
    # Load CSV
    df = pd.read_csv(csv_file)
    
    # --- Trends: take trend_percent ---
    df_trend = df[['basin_id', 'trend_percent']].rename(columns={'trend_percent': variable_name})
    
    # --- Means: take mean ---
    df_mean = df[['basin_id', 'mean']].rename(columns={'mean': variable_name})
    
    # Merge into trends DataFrame
    if df_trends.empty:
        df_trends = df_trend
    else:
        df_trends = pd.merge(df_trends, df_trend, on='basin_id', how='outer')
    
    # Merge into means DataFrame
    if df_means.empty:
        df_means = df_mean
    else:
        df_means = pd.merge(df_means, df_mean, on='basin_id', how='outer')

# Optional: set basin_id as index
df_trends.set_index('basin_id', inplace=True)
df_means.set_index('basin_id', inplace=True)

# Show results
print("Trends DataFrame:")
print(df_trends.head())
print("\nMeans DataFrame:")
print(df_means.head())

# List of basins to remove
basins_to_remove = [4012, 4018, 4021, 4025]

# Drop from both DataFrames
df_trends = df_trends.drop(basins_to_remove, errors='ignore')
df_means = df_means.drop(basins_to_remove, errors='ignore')

# Drop specific columns from both DataFrames
columns_to_remove = ['min_swe', 'day_of_min_swe']
df_trends = df_trends.drop(columns=columns_to_remove, errors='ignore')
df_means = df_means.drop(columns=columns_to_remove, errors='ignore')


#%%% correlation matrix
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Build cross correlation matrix (rows = trends, cols = means)
cross_corr = pd.DataFrame(index=df_trends.columns, columns=df_means.columns, dtype=float)
for trend_var in df_trends.columns:
    for mean_var in df_means.columns:
        cross_corr.loc[trend_var, mean_var] = df_trends[trend_var].corr(df_means[mean_var])

# Custom colormap with user-defined stops
colors = [
    (0.0, "#6B2737"),  # deep red
    (0.05, "#A63C54"), # intermediate red
    (0.47, "#F4E1E5"), # light red
    (0.5, "#FEFAEF"),  # off-white
    (0.53, "#DCEDF6"), # light blue
    (0.95, "#29749C"), # intermediate blue
    (1.0, "#18435A"),  # deep blue
]
cmap = LinearSegmentedColormap.from_list("custom_corr", colors, N=256)

# Plot
plt.figure(figsize=(10, 8))
im = plt.imshow(cross_corr, cmap=cmap, vmin=-1, vmax=1)

plt.xticks(range(len(cross_corr.columns)), cross_corr.columns, rotation=90)
plt.yticks(range(len(cross_corr.index)), cross_corr.index)

# Axis labels
plt.xlabel("Means", fontsize=12)
plt.ylabel("Trends", fontsize=12)

# Colorbar
cbar = plt.colorbar(im)
cbar.set_label("Correlation")
cbar.set_ticks([-1, -0.5, 0, 0.5, 1])

plt.tight_layout()
plt.show()


#%%%

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Custom colormap
colors = [
    (0.0, "#6B2737"),  # deep red
    (0.05, "#A63C54"), # intermediate red
    (0.47, "#F4E1E5"), # light red
    (0.5, "#FEFAEF"),  # off-white
    (0.53, "#DCEDF6"), # light blue
    (0.95, "#29749C"), # intermediate blue
    (1.0, "#18435A"),  # deep blue
]
cmap = LinearSegmentedColormap.from_list("custom_corr", colors, N=256)

# Compute correlation matrices
corr_means = df_means.corr()
corr_trends = df_trends.corr()

# Plot Means vs Means
plt.figure(figsize=(10, 8))
im1 = plt.imshow(corr_means, cmap=cmap, vmin=-1, vmax=1)
plt.xticks(range(len(corr_means.columns)), corr_means.columns, rotation=90)
plt.yticks(range(len(corr_means.index)), corr_means.index)
plt.xlabel("Means", fontsize=12)
plt.ylabel("Means", fontsize=12)
cbar = plt.colorbar(im1)
cbar.set_label("Correlation")
plt.title("Means vs Means")
plt.tight_layout()
plt.show()

# Plot Trends vs Trends
plt.figure(figsize=(10, 8))
im2 = plt.imshow(corr_trends, cmap=cmap, vmin=-1, vmax=1)
plt.xticks(range(len(corr_trends.columns)), corr_trends.columns, rotation=90)
plt.yticks(range(len(corr_trends.index)), corr_trends.index)
plt.xlabel("Trends", fontsize=12)
plt.ylabel("Trends", fontsize=12)
cbar = plt.colorbar(im2)
cbar.set_label("Correlation")
plt.title("Trends vs Trends")
plt.tight_layout()
plt.show()

#%%  boxplots

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

df_means = df_means.copy()
df_trends = df_trends.copy()
common_idx = df_means.index.intersection(df_trends.index)
df_means = df_means.loc[common_idx]
df_trends = df_trends.loc[common_idx]

def tertile_groups(series, labels=('low','medium','high')):
    s = series.copy()
    try:
        groups = pd.qcut(s, q=3, labels=labels)
    except ValueError:
        groups = pd.cut(s.rank(method='first'), bins=3, labels=labels)
    return groups

mean_cols = df_means.select_dtypes(include=[np.number]).columns.tolist()
trend_cols = df_trends.select_dtypes(include=[np.number]).columns.tolist()

for mean_col in mean_cols:
    groups = tertile_groups(df_means[mean_col])
    plot_df = df_trends.copy()
    plot_df['group'] = groups

    melt = plot_df.melt(id_vars=['group'], value_vars=trend_cols,
                        var_name='trend_variable', value_name='trend_value')
    melt = melt.dropna(subset=['trend_value','group'])

    n = len(trend_cols)
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(cols*4, rows*3.2), squeeze=False)
    axes = axes.flatten()

    for i, trend in enumerate(trend_cols):
        ax = axes[i]
        data = melt[melt['trend_variable'] == trend]

        sns.boxplot(
            x='group', y='trend_value', data=data, order=['low','medium','high'],
            width = 0.15,
            showcaps=False,                     # remove horizontal cap lines
            boxprops=dict(facecolor='none', edgecolor='black', linewidth=3.0),
            whiskerprops=dict(color='black', linewidth=3.0),   # whiskers kept but without caps
            capprops=dict(color='black', linewidth=3.0),       # ignored when showcaps=False
            medianprops=dict(color='black', linewidth=2.5),
            flierprops=dict(marker='o', markerfacecolor='black', markeredgecolor='black', markersize=4, alpha=1.0),
            ax=ax
        )

        # keep group labels
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(['low', 'medium', 'high'], fontsize=9)

        # minimal tick styling for axes (not boxplot caps)
        ax.tick_params(axis='both', which='both', length=0)
        ax.xaxis.set_minor_locator(mticker.NullLocator())
        ax.yaxis.set_minor_locator(mticker.NullLocator())
        ax.set_yticklabels([])

        # spines styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('black')
        ax.spines['bottom'].set_color('black')
        ax.spines['left'].set_linewidth(1.6)
        ax.spines['bottom'].set_linewidth(1.6)

        ax.axhline(0, color='grey', linestyle='--', linewidth=1.0)
        ax.set_title(trend, fontsize=10, pad=6)
        ax.set_xlabel('')
        ax.set_ylabel('')

    for j in range(n, len(axes)):
        fig.delaxes(axes[j])

    fig.suptitle(f"Trends grouped by tertiles of mean: {mean_col}", fontsize=12)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    plt.show()
    
#%%%
import numpy as np
import pandas as pd
import math
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib import cm

# custom colormap (same as before)
colors = [
    (0.0, "#6B2737"),
    (0.05, "#A63C54"),
    (0.47, "#F4E1E5"),
    (0.5, "#FEFAEF"),
    (0.53, "#DCEDF6"),
    (0.95, "#29749C"),
    (1.0, "#18435A"),
]
cmap = LinearSegmentedColormap.from_list("custom_corr", colors, N=256)
norm = Normalize(vmin=-1, vmax=1)

def matrix_boxplots_cell_bg(df_means, df_trends, group_labels=('low','medium','high'),
                            cell_size=(2.2, 1.6), savepath=None, dpi=300):
    # align indices and numeric-only
    common_idx = df_means.index.intersection(df_trends.index)
    df_means = df_means.loc[common_idx].copy()
    df_trends = df_trends.loc[common_idx].copy()
    mean_cols = df_means.select_dtypes(include=[np.number]).columns.tolist()
    trend_cols = df_trends.select_dtypes(include=[np.number]).columns.tolist()
    if not mean_cols or not trend_cols:
        raise ValueError("No numeric columns in means or trends.")

    # compute cross-correlation (trend rows, mean cols)
    cross_corr = pd.DataFrame(index=trend_cols, columns=mean_cols, dtype=float)
    for t in trend_cols:
        for m in mean_cols:
            cross_corr.loc[t, m] = df_trends[t].corr(df_means[m])

    # robust tertile grouping
    def tertile_groups(s):
        try:
            return pd.qcut(s, 3, labels=group_labels)
        except ValueError:
            ranks = s.rank(method="first")
            return pd.cut(ranks, bins=3, labels=group_labels)

    n_rows = len(mean_cols)
    n_cols = len(trend_cols)
    fig_w = max(6, n_cols * cell_size[0])
    fig_h = max(4, n_rows * cell_size[1])
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_w, fig_h), squeeze=False)

    for i, mean_col in enumerate(mean_cols):
        groups = tertile_groups(df_means[mean_col])
        df_temp = df_trends.copy()
        df_temp['group'] = groups

        for j, trend_col in enumerate(trend_cols):
            ax = axes[i][j]
            data = df_temp[[trend_col, 'group']].dropna()
            if data.empty:
                ax.set_axis_off()
                continue

            # determine color from cross-correlation (trend_row, mean_col)
            corr_val = cross_corr.loc[trend_col, mean_col]
            bg_color = cmap(norm(corr_val))
            # choose edgecolor for elements depending on bg luminance for contrast
            # simple contrast test: compute perceived luminance
            r, g, b, _ = matplotlib.colors.to_rgba(bg_color)
            luminance = 0.299*r + 0.587*g + 0.114*b
            edgecolor = 'black' if luminance > 0.5 else 'white'

            # fill cell background: draw a rectangle spanning axes coordinates
            ax.set_facecolor(bg_color)
            # remove grid/background patch border visibility if desired
            ax.patch.set_alpha(0.9)

            # draw boxplot on top (use transparent box face so background shows)
            order = list(group_labels)
            sns.boxplot(x='group', y=trend_col, data=data, order=order,
                        width=0.4,
                        showcaps=False,
                        boxprops=dict(facecolor='none', edgecolor=edgecolor, linewidth=2),
                        whiskerprops=dict(color=edgecolor, linewidth=2),
                        medianprops=dict(color=edgecolor, linewidth=2),
                        flierprops=dict(marker='o', markerfacecolor=edgecolor, markeredgecolor=edgecolor, markersize=3, alpha=0.9),
                        ax=ax)

            # ensure artists exist and set line colors
            fig.canvas.draw()
            for line in ax.lines:
                line.set_color(edgecolor)
                line.set_linewidth(0.6)

            # keep x labels only on bottom row, y labels only on first column
            if i < n_rows - 1:
                ax.set_xticklabels([])
            else:
                ax.set_xticklabels(order, fontsize=6)
            if j > 0:
                ax.set_yticklabels([])
            else:
                ax.tick_params(axis='y', labelsize=6)

            ax.set_xlabel('' if i < n_rows - 1 else mean_col, fontsize=7,rotation=0)
            ax.set_ylabel('' if j > 0 else trend_col, fontsize=7, rotation=0, labelpad=30)
            ax.yaxis.set_label_position("left")
            ax.axhline(0, color=edgecolor, linestyle='--', linewidth=0.5, alpha=0.6)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(0.6)
            ax.spines['bottom'].set_linewidth(0.6)

    # add colorbar for correlation scale
    cax = fig.add_axes([0.92, 0.1, 0.02, 0.8])
    cb = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax)
    cb.set_label('Cross-correlation (trend vs mean)')

    fig.subplots_adjust(wspace=0.45, hspace=0.6)
    fig.tight_layout(rect=[0, 0.03, 0.9, 0.98])

    if savepath:
        fig.savefig(savepath, dpi=dpi, bbox_inches='tight')
    plt.show()

# Example usage:
matrix_boxplots_cell_bg(df_means, df_trends, cell_size=(2.0,1.4), savepath="matrix_bg.png", dpi=300)
