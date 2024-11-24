import os

DATA_DIR = "data"
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
MONITORING_CSV_PATH = os.path.join(OUTPUT_DIR, 'constraint_monitoring.csv')
DER_NAME = None # This will pull all constraints across the network rather than a specific DER
ODP_API_URL = "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/ukpn-constraints-real-time-meter-readings/records"

NUMBER_OF_CONSTRAINTS_TO_PLOT = 10 # The number of constraints to plot on the graph, these will be the constraints with the highest utilisation
MAX_PLOT_HISTORY = 1 # Max number of minutes to plot on the graph