# Python-Redfin

### Installation

```
$ python3 -m pip install redfin
```

### Usage

```python3

from redfin import Redfin

client = Redfin()

address = '4544 Radnor St, Detroit Michigan'

response = client.search(address)
url = response['payload']['exactMatch']['url']
initial_info = client.initial_info(url)

property_id = initial_info['payload']['propertyId']
listing_id = initial_info['payload']['listingId']

mls_data = client.below_the_fold(property_id, listing_id)
```
