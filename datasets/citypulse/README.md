This is the CityPulse dataset.

	http://iot.ee.surrey.ac.uk:8080/datasets.html


files:
- `traffic_feb_jun_2014.tar.gz` => the CSV raw data archive
- `traffic_metadata.csv`        => the metadata

The metadata is slightly altered from the original, we removed
the last 3 columns which were irrelevant for our project.

Traffic data as stored in the .tar.gz are a set of CSV files
named `trafficData<REPORT_ID>.csv`, one per 'reporter' (road chunk)
described in the metadata (`REPORT_ID`, location, entry/exit points).
There are 449 files, each containing 27-32k lines of timestamped data.
