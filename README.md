# Python-Redfin

### Installation

```
$ python3 -m pip install python-redfin
```

### Usage

```python3

from redfin import Redfin

client = Redfin()

address = '4544 Radnor St, Detroit Michigan'

response = client.search(address)
url = response['payload']['exactMatch']['url']
initial_info = engine.initial_info(url)

property_id = data['payload']['propertyId']
listing_id = data['payload']['listingId']

mls_data = client.below_the_fold(property_id, listing_id)
```
