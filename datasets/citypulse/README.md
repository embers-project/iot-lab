This is the CityPulse dataset.

	http://iot.ee.surrey.ac.uk:8080/datasets.html


files:
- `traffic_feb_jun_2014.tar.bz2` => the CSV raw data archive
- `traffic_metadata.csv`         => the metadata

Metadata describes 449 'reporters' (road chunks) identified by a unique
`REPORT_ID` and provides attributes such as location address, entry/exit
points GPS coordinates and distance.  We use this data as is to register
devices into the system ; we mirror all but the last 3 columns.

Traffic data as stored in the .tar.gz are a set of CSV files named
`trafficData<REPORT_ID>.csv`, one per 'reporter' present in the metadata.
There are 449 files, each containing 27-32k lines of timestamped data.
