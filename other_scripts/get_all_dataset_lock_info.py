import csv
from dateutil import tz
from dateutil.parser import parse
import json
import os
import requests
import time
# Import RT python module to get info from emails


# From user get installation URL, apiToken, directory to save CSV file
installationUrl = ''
apiToken = ''
directoryPath = ''

# List lock types. See https://guides.dataverse.org/en/5.10/api/native-api.html?highlight=locks#list-locks-across-all-datasets
lockTypesList = ['Ingest', 'finalizePublication']


def convert_to_local_tz(timestamp, shortDate=False):
    # Save local timezone to localTimezone variable
    localTimezone = tz.tzlocal()
    # Convert string to datetime object
    timestamp = parse(timestamp)
    # Convert timestamp to local timezone
    timestamp = timestamp.astimezone(localTimezone)
    if shortDate is True:
        # Return timestamp in YYYY-MM-DD format
        timestamp = timestamp.strftime('%Y-%m-%d')
    return timestamp


currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

datasetPids = []

# Get dataset PIDs of datasets that have any of the lock types in lockTypesList
for lockType in lockTypesList:

    datasetLocksApiEndpoint = f'{installationUrl}/api/datasets/locks?type={lockType}'
    response = requests.get(
        datasetLocksApiEndpoint,
        headers={'X-Dataverse-key': apiToken})
    data = response.json()

    if data['status'] == 'OK':
        for lock in data['data']:
            datasetPid = lock['dataset']
            datasetPids.append(datasetPid)

# Use set function to deduplicate datasetPids list and convert set to a list again
datasetPids = list(set(datasetPids))

total = len(datasetPids)

if total == 0:
    print('No locked datasets found.')

elif total > 0:

    count = 0

    # Create CSV file and header row
    csvOutputFile = 'dataset_locked_status_%s.csv' % (currentTime)
    csvOutputFilePath = os.path.join(directoryPath, csvOutputFile)

    with open(csvOutputFilePath, mode='w', newline='') as f:
        f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        f.writerow(['dataset_pid', 'dataset_url', 'lock_reason', 'locked_date', 'user_name'])

        # For each dataset, write to the CSV file info about each lock the dataset has
        for datasetPid in datasetPids:
            url = f'{installationUrl}/api/datasets/:persistentId/locks?persistentId={datasetPid}'
            data = requests.get(url).json()

            count += 1

            # Use an API endpoint to get the dataset's title metadata and contact email 

            # Use the Search API to see if any different datasets with the same title have already been created. 
            # Save any matches as a list of dataset PIDs

            # Use the RT python module to check RT to see if the depositor has ever emailed
            # support. The depositor might have already emailed support about the locked dataset
            # Save any matches as a list of RT ticket IDs

            for lock in data['data']:
                datasetUrl = f'{installationUrl}/dataset.xhtml?persistentId={datasetPid}'
                reason = lock['lockType']
                lockedDate = convert_to_local_tz(lock['date'], shortDate=True)
                userName = lock['user']
                f.writerow([datasetPid, datasetUrl, reason, lockedDate, userName])

            print('%s of %s datasets: %s' % (count, total, datasetPid))
