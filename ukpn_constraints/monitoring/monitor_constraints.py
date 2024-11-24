"""
This module provides functionality to monitor constraints by fetching constraint data
from UKPN's Open Data Portal and visualizing the results on an interactive plot which
updates in real-time.

Usage:
    This module can be run as a script to monitor constraints or it's functions can be
    imported and used in other modules.

Summary:
When run as a script, the module performs the following steps:
    1. Creates the output directory if it doesn't exist.
    2. Initializes a live plot in interactive mode.
    3. Enters an infinite loop to:
        a. Fetch raw data from an API and store it in a dataframe.
        b. Check if the dataframe is not empty.
        c. Process the data to add a constraint utilization column.
        d. Save the processed data into a CSV file.
        e. Update the live plot with the new data.
        f. Wait for a specified interval before repeating the process.
    The function handles keyboard interrupts to allow graceful termination.
"""
import os
import requests
import time

import dotenv
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('wxagg') # We use this for functionality to maximise plot window
import matplotlib.pyplot as plt

from ukpn_constraints import config

dotenv.load_dotenv()

ODP_API_URL = config.ODP_API_URL
ODP_API_KEY = os.getenv("ODP_API_KEY")
DER_NAME = config.DER_NAME
OUTPUT_DIR = config.OUTPUT_DIR
MONITORING_CSV_PATH = config.MONITORING_CSV_PATH
NUMBER_OF_CONSTRAINTS_TO_PLOT = config.NUMBER_OF_CONSTRAINTS_TO_PLOT
MAX_PLOT_HISTORY = config.MAX_PLOT_HISTORY

def update_graph(df, lines, num_constraints_to_plot, max_plot_history):
    """
    Updates a graph with the given data.

    Parameters:
    df (pandas.DataFrame): DataFrame containing the data to plot. Must include 'timestamp', 'constraint_description', and 'utilisation' columns.
    lines (list): List of line objects representing the current lines on the plot.
    num_constraints_to_plot (int): Number of top constraints to plot based on utilisation.
    max_plot_history (int): Maximum number of data points to display on the plot.

    Returns:
    list: Updated list of line objects representing the lines on the plot.
    """
    # Extract the columns we need
    usecols = ['timestamp', 'constraint_description', 'utilisation']
    df = df[usecols]
    # Sort from most heavily utilised
    df = df.sort_values('utilisation', ascending=False)
    df.reset_index(inplace=True, drop=True)
    # Limit to the top n constraints
    df = df.head(num_constraints_to_plot)
    # Current timestamp
    current_timestamp = df['timestamp'].iloc[0]
    # Add a row for the allowable utilisation which equals 1 (for display on the plot) at the top of dataframe
    new_row_dict = {'timestamp': current_timestamp, 'constraint_description': 'Allowable utilisation', 'utilisation': 1}
    df = pd.concat([pd.DataFrame([new_row_dict]), df])
    # Get list of constraints
    constraints = df['constraint_description'].unique()
    # Get a colour map
    colors = plt.cm.jet(np.linspace(0,1,num_constraints_to_plot))
    colors = colors[::-1] # Reverse the color map so that the most heavily utilised constraint is red
    if not lines:
        for i, constraint in enumerate(constraints):
            constraint_label = constraint[:50]
            # Subset for setting up our graph
            subset = df[df['constraint_description'] == constraint]
            x = subset['timestamp']
            y = subset['utilisation']
            # Set the color to black if it's the allowable utilisation, otherwise use the color map
            color = 'k' if i == 0 else colors[i-1]
            line = plt.plot(x, y, marker='o', c=color, markersize=6, label=constraint_label)[0]
            # Use a dashed line for the allowable utilisation
            if i == 0:
                line.set_dashes([2, 2])
            lines.append(line)

        plt.ylabel('Constraint Utilisation', fontsize=12)
        plt.xticks(rotation=30)
        plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1), ncols=4, fontsize=8)
        plt.pause(0.5)
    else:
        # Create a mapping for the constraints that have already been plotted
        constraints_plotted_dict = {line.get_label(): line for line in lines[1:]}
        if current_timestamp not in lines[0].get_xdata():
            for i, constraint in enumerate(constraints):
                constraint_label = constraint[:50]
                if i == 0:
                    x_new = [current_timestamp]
                    y_new = [1]
                    color = 'k' # Set the color to black if it's the allowable utilisation
                    x = lines[i].get_xdata().tolist() + x_new
                    y = lines[i].get_ydata().tolist() + y_new
                else:
                    subset = df[df['constraint_description'] == constraint]
                    x_new = subset['timestamp'].tolist()
                    y_new = subset['utilisation'].tolist()
                    color = colors[i-1] # Use the colormap if not the allowable utilisation line
                    if constraint[:50] in constraints_plotted_dict:
                        # If the constraint has already been plotted, we just need to update the data
                        x = constraints_plotted_dict[constraint_label].get_xdata().tolist() + x_new
                        y = constraints_plotted_dict[constraint_label].get_ydata().tolist() + y_new
                    else:
                        # If the constraint hasn't been plotted yet, we need to start a new line
                        x = x_new
                        y = y_new

                # We a show maximum number of minutes of data as specified by max_plot_history
                x = x[-max_plot_history:]
                y = y[-max_plot_history:]
                # Removes the existing plot and replaces it with the new one
                lines[i].remove()
                lines[i] = plt.plot(x, y, marker='o', c=color, markersize=6, label=constraint_label)[0]
                if i == 0:
                    lines[i].set_dashes([2, 2])
                    x_lower_lim = x[0]
                    x_upper_lim = x[-1]

            plt.ylabel('Constraint Utilisation', fontsize=12)
            plt.xticks(rotation=30)
            plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1), ncols=4, fontsize=8)
            plt.xlim(x_lower_lim, x_upper_lim)
            plt.pause(0.5)

    return lines

def save_data_into_csv(df, csv_file_path):
    """
        This function saves the response data to a csv file at the specified path
        Parameters
        ----------
            df: data from the response object
    """
    if df.empty:
        print("DataFrame is empty, no data in response.")
        return

    if not os.path.exists(csv_file_path):
        # Append DataFrame to CSV (handle potential errors)
        try:
            df.to_csv(csv_file_path, mode="w", header=True, index=False)
            print("Data saved to CSV successfully.")
        except Exception as e:
            print(f"Error saving data to CSV: {e}")

    else:
        # Append DataFrame to CSV (handle potential errors)
        try:
            existing_df=pd.read_csv(csv_file_path)
            df = pd.concat([df,existing_df])
            df.drop_duplicates(inplace=True)
            df.reset_index(inplace=True,drop=True)
            df.to_csv(csv_file_path, mode="w", header=True, index=False)
            print("Data saved to CSV successfully.")
        except Exception as e:
            print(f"Error saving data to CSV: {e}")
    return

def clean_data_and_add_utilisation(df):
    """
        This function cleans the data and adds a new column for constraint utilisation. This is a measure of how much electrical load is going through the constraint as a proportion of its capacity.
        Values above +1 indicate the constraint is overloaded.
    """
    # Fill any missing readings with 0
    df['present_amps_value'].fillna(0, inplace=True)
    # Remove timezone info from timestamp and convert back to string for plotting
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None).dt.strftime('%Y-%m-%d %H:%M')
    # Add a column for constraint utilisation metric
    df['utilisation'] = df['present_amps_value'] / df['trim_amps']
    return df

def hit_api_and_return_data(api_base_url, api_key, der_name=None):
    """
    Fetches data from the API for a particular DER.

    Parameters
    ----------
    api_base_url : str
        The base URL for the API endpoint.
    api_key : str
        The API key for UKPN's ODP.
    der_name : str, optional
        The DER name present on UKPN's ODP. If not provided, defaults to pulling all constraints across the network.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the fetched data with columns: 'timestamp', 'constraint_id', 'present_amps_value', 'trim_amps', 'release_limit_amps', 'breach_flag', 'constraint_description', 'der_name'.
        Returns an empty DataFrame if there is an error or no data is returned.

    Raises
    ------
    Exception
        If the API key is not provided.
    """
    if not api_key:
        raise Exception("API key is required to fetch data from the API.")

    if not der_name:
        der_name = "REDACTED" # This will pull all constraints across the network

    params = {'apikey': api_key,'refine':f'der_name:{der_name}'}
    resp = requests.get(api_base_url, params=params)
    data = resp.json()
    # Create DataFrame from data (handle potential errors)
    try:
        df = pd.DataFrame(data["results"],columns=['timestamp', 'constraint_id','present_amps_value','trim_amps','release_limit_amps','breach_flag','constraint_description','der_name'])
    except Exception as e:
        print(f"Error creating DataFrame, no results in response: {e}")
        df = pd.DataFrame()

    return df

def main():
    """
    Main function to monitor constraints by fetching data from an API, processing it, saving it to a CSV file, and updating a live plot.
    The function performs the following steps:
    1. Creates the output directory if it doesn't exist.
    2. Initializes a live plot in interactive mode.
    3. Enters an infinite loop to:
        a. Fetch raw data from an API and store it in a dataframe.
        b. Check if the dataframe is not empty.
        c. Process the data to add a constraint utilization column.
        d. Save the processed data into a CSV file.
        e. Update the live plot with the new data.
        f. Wait for a specified interval before repeating the process.
    The function handles keyboard interrupts to allow graceful termination.
    """

    # Create the output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
    # Initialize the plot once outside the loop
        plt.ion()  # turning interactive mode on
        mng = plt.get_current_fig_manager()
        mng.frame.Maximize(True) # maximise the window
        lines = []
        while True:
            # Get the raw data and put it in a dataframe
            df = hit_api_and_return_data(ODP_API_URL, ODP_API_KEY, DER_NAME)
            # Check for successful response
            if not df.empty:
                # Add a column for constraint utilisation. A measure of how much electrical load is going through the constraint as a proportion of its capacity.
                df = clean_data_and_add_utilisation(df)
                # Extract data from response
                try:
                    save_data_into_csv(df, MONITORING_CSV_PATH)
                except Exception as e:
                    print(f"Saving to csv didn't work due to {e}")
            else:
                print(f"API request failed, no data in response.")
                time.sleep(30)
                continue
            # Update the graph
            lines = update_graph(df, lines, NUMBER_OF_CONSTRAINTS_TO_PLOT, MAX_PLOT_HISTORY)
            # Wait for the specified interval
            time.sleep(30)
    except KeyboardInterrupt as e:
        print('You have stopped now')


if __name__ == "__main__":
    main()