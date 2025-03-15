import os
import json
import random
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import textwrap
from pandas.plotting import parallel_coordinates

# Set a colorful seaborn style and palette
sns.set_theme(style="whitegrid", palette="bright")

# Ensure charts directory exists
CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

# Load SQL results from JSON file
SQL_RESULTS_FILE = "sql_results.json"
if not os.path.exists(SQL_RESULTS_FILE):
    print("Error: sql_results.json not found!")
    sys.exit(1)  # Use sys.exit() instead of exit()

try:
    with open(SQL_RESULTS_FILE, "r") as file:
        sql_results = json.load(file)
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error loading {SQL_RESULTS_FILE}: {e}")
    sys.exit(1)

# Function to truncate long text to a maximum of 30 items for visualization
def truncate_items(items, max_items=30):
    """
    Truncate a list of items to a maximum length for visualization.
    """
    if len(items) > max_items:
        return items[:max_items] + ["..."]
    return items

# Function to wrap long text
def wrap_text(text, width=20):
    """Wrap text to a specified width."""
    return "\n".join(textwrap.wrap(text, width))

# Function to filter large categorical variables
def filter_large_categorical(df):
    """
    Filter out categories with too many unique values for better visualization.
    """
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() > 20:
            top_categories = df[col].value_counts().nlargest(20).index
            df = df[df[col].isin(top_categories)]
    return df

# Function to bias graph type selection based on the number of rows
def choose_graph_type(num_columns, num_items):
    """
    Choose a graph type based on the number of columns and rows, with bias for certain types.
    """
    if num_columns == 1:
        # Univariate graphs
        if num_items > 25:
            # Prefer histograms and box plots for large datasets
            graph_types = ["hist", "box", "violin", "rug", "count"]
        else:
            # Prefer pie charts and count plots for smaller datasets
            graph_types = ["pie", "count", "box", "violin"]
    elif num_columns == 2:
        # Bivariate graphs
        if num_items > 25:
            # Prefer scatter plots and hexbin for large datasets
            graph_types = ["scatter", "hexbin", "reg", "line", "area"]
        else:
            # Prefer bar and line plots for smaller datasets
            graph_types = ["bar", "line", "reg"]
    else:
        # Multivariate graphs
        graph_types = ["heatmap", "pairplot", "stacked_bar", "grouped_bar", "clustermap", "parallel"]

    return random.choice(graph_types)

# Function to generate and save a graph
def generate_graph(df, output_prefix):
    """
    Generates a random graph based on the number of columns in df and saves it as a PNG.
    Uses a variety of graph types and colorful palettes.
    """
    df = filter_large_categorical(df)
    num_columns = len(df.columns)
    num_items = len(df)

    # Choose a graph type with bias based on the number of rows
    chosen_graph = choose_graph_type(num_columns, num_items)
    print(f"Chosen graph type: {chosen_graph}")
    col_names = df.columns.tolist()

    try:
        plt.figure(figsize=(8, 6))

        if chosen_graph == "hist":
            col = col_names[0]
            sns.histplot(df[col], bins=10, color="skyblue")
            plt.xlabel(col)
            plt.ylabel("Frequency")
            plt.title(f"Histogram of {col}")
        
        elif chosen_graph == "box":
            col = col_names[0]
            sns.boxplot(y=df[col], color="lightgreen")
            plt.ylabel(col)
            plt.title(f"Box Plot of {col}")
            
        elif chosen_graph == "violin":
            col = col_names[0]
            sns.violinplot(y=df[col], color="orchid")
            plt.ylabel(col)
            plt.title(f"Violin Plot of {col}")
            
        elif chosen_graph == "pie":
            col = col_names[0]
            value_counts = df[col].value_counts()
            if len(value_counts) > 30:
                top_values = value_counts.nlargest(30)
                labels = truncate_items(top_values.index.tolist())
                sizes = top_values.values
            else:
                labels = value_counts.index.tolist()
                sizes = value_counts.values
            plt.pie(sizes, labels=labels, autopct="%1.1f%%", colors=sns.color_palette("bright"))
            plt.title(f"Pie Chart of {col}")
            
        elif chosen_graph == "rug":
            col = col_names[0]
            sns.rugplot(df[col], color="purple")
            plt.xlabel(col)
            plt.title(f"Rug Plot of {col}")
            
        elif chosen_graph == "count":
            col = col_names[0]
            value_counts = df[col].value_counts()
            if len(value_counts) > 30:
                top_values = value_counts.nlargest(30)
                labels = truncate_items(top_values.index.tolist())
                counts = top_values.values
            else:
                labels = value_counts.index.tolist()
                counts = value_counts.values
            sns.barplot(x=labels, y=counts, palette="bright")
            plt.xlabel(col)
            plt.ylabel("Count")
            plt.title(f"Count Plot of {col}")
            
        elif chosen_graph == "scatter":
            if num_items > 25:  # Only use scatter plots for larger datasets
                x_col, y_col = col_names[:2]
                sns.scatterplot(x=df[x_col], y=df[y_col], color="dodgerblue")
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.title(f"Scatter Plot: {x_col} vs {y_col}")
            else:
                print("Skipping scatter plot for small dataset.")
                return
            
        elif chosen_graph == "bar":
            x_col, y_col = col_names[:2]
            sns.barplot(x=df[x_col], y=df[y_col], palette="bright")
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title(f"Bar Chart: {x_col} vs {y_col}")
            
        elif chosen_graph == "line":
            x_col, y_col = col_names[:2]
            sns.lineplot(x=df[x_col], y=df[y_col], color="seagreen")
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title(f"Line Plot: {x_col} vs {y_col}")
            
        elif chosen_graph == "reg":
            x_col, y_col = col_names[:2]
            sns.regplot(x=df[x_col], y=df[y_col], scatter_kws={"color": "orange"}, line_kws={"color": "blue"})
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title(f"Regression Plot: {x_col} vs {y_col}")
            
        elif chosen_graph == "area":
            x_col, y_col = col_names[:2]
            plt.fill_between(df[x_col], df[y_col], color="skyblue", alpha=0.5)
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title(f"Area Plot: {x_col} vs {y_col}")
            
        elif chosen_graph == "hexbin":
            x_col, y_col = col_names[:2]
            plt.hexbin(df[x_col], df[y_col], gridsize=25, cmap="Blues")
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title(f"Hexbin Plot: {x_col} vs {y_col}")
            
        elif chosen_graph == "joint":
            if num_items > 25:  # Only use joint plots for larger datasets
                x_col, y_col = col_names[:2]
                jp = sns.jointplot(x=df[x_col], y=df[y_col], kind="scatter", color="magenta")
                jp.fig.suptitle(f"Joint Plot: {x_col} vs {y_col}", y=1.02)
                output_path = os.path.join(CHARTS_DIR, f"{output_prefix}_{chosen_graph}.png")
                jp.fig.tight_layout()
                jp.fig.savefig(output_path)
                plt.close('all')
                print(f"Graph saved: {output_path}")
                return
            else:
                print("Skipping joint plot for small dataset.")
                return
            
        elif chosen_graph == "heatmap":
            numeric_df = df.select_dtypes(include=["number"])
            if len(numeric_df.columns) >= 2:
                sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt=".2f")
                plt.title("Heatmap of Correlation")
            else:
                print("Not enough numeric columns for heatmap.")
                return
            
        elif chosen_graph == "pairplot":
            numeric_df = df.select_dtypes(include=["number"])
            if len(numeric_df.columns) >= 2:
                pp = sns.pairplot(numeric_df, palette="bright")
                pp.fig.suptitle("Pairplot of Numeric Features", y=1.02)
                output_path = os.path.join(CHARTS_DIR, f"{output_prefix}_{chosen_graph}.png")
                pp.fig.tight_layout()
                pp.fig.savefig(output_path)
                plt.close('all')
                print(f"Graph saved: {output_path}")
                return
            else:
                print("Not enough numeric columns for pairplot.")
                return
            
        elif chosen_graph == "stacked_bar":
            if num_columns >= 3:
                x_col, y_col, z_col = col_names[:3]
                grouped = df.groupby([x_col, y_col])[z_col].sum().unstack().fillna(0)
                grouped.plot(kind="bar", stacked=True, colormap="Paired")
                plt.xlabel(x_col)
                plt.ylabel(z_col)
                plt.title(f"Stacked Bar Chart: {x_col} vs {z_col} by {y_col}")
            else:
                print("Not enough columns for stacked bar chart.")
                return
            
        elif chosen_graph == "grouped_bar":
            if num_columns >= 3:
                x_col, y_col, z_col = col_names[:3]
                grouped = df.groupby([x_col, y_col])[z_col].sum().unstack().fillna(0)
                grouped.plot(kind="bar", colormap="Set2")
                plt.xlabel(x_col)
                plt.ylabel(z_col)
                plt.title(f"Grouped Bar Chart: {x_col} vs {z_col} by {y_col}")
            else:
                print("Not enough columns for grouped bar chart.")
                return
            
        elif chosen_graph == "clustermap":
            numeric_df = df.select_dtypes(include=["number"])
            if len(numeric_df.columns) >= 2:
                sns.clustermap(numeric_df.corr(), cmap="vlag", annot=True)
                plt.title("Clustermap of Correlation")
            else:
                print("Not enough numeric columns for clustermap.")
                return
            
        elif chosen_graph == "parallel":
            if num_columns >= 3:
                class_col = df.columns[0]
                parallel_coordinates(df, class_col, colormap=plt.get_cmap("Set1"))
                plt.title("Parallel Coordinates Plot")
            else:
                print("Not enough columns for parallel coordinates plot.")
                return
            
        else:
            print(f"Graph type '{chosen_graph}' not implemented.")
            return
        
        # Save the plot (for plots created using plt.figure())
        output_path = os.path.join(CHARTS_DIR, f"{output_prefix}_{chosen_graph}.png")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        print(f"Graph saved: {output_path}")
        
    except Exception as e:
        print(f"Error generating {chosen_graph} graph: {e}")
        plt.close()

# Process each SQL query result and generate a graph
for i, query_result in enumerate(sql_results):
    query = query_result.get("query", f"query_{i+1}")
    rows = query_result.get("rows", [])
    
    if not rows:
        print(f"No data for query: {query}, skipping.")
        continue
    
    df = pd.DataFrame(rows)
    
    if df.empty or len(df.columns) < 1:
        print(f"Skipping empty dataset for query: {query}.")
        continue
    
    # Check if there is at least one numeric column
    if df.select_dtypes(include=["number"]).empty:
        print(f"Skipping {query} – No numeric data to plot.")
        continue
    
    # Convert columns to numeric when possible
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except ValueError:
            pass  # Leave non-numeric columns as is
    
    # Generate and save the graph
    generate_graph(df, f"query_{i+1}")

print("Graph generation completed.")