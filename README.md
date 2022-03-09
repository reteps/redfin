# Python-Redfin

A wrapper around redfin's unofficial API. Anything on the redfin site can be accessed through this module without screen scraping.

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
mls_data = client.below_the_fold(property_id)

listing_id = initial_info['payload']['listingId']
avm_details = client.avm_details(property_id, listing_id)


```
### Usage Notes

+ sometimes `below_the_fold` lacks propertyHistoryInfo -- see [#11](https://github.com/reteps/redfin/issues/11) if this is needed

### Documentation

See the file for all functions, pop open requests on redfin to see which one you want.
