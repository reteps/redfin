# redfin

[![PyPI](https://img.shields.io/pypi/v/redfin)](https://pypi.org/project/redfin/)
[![Tests](https://github.com/reteps/redfin/actions/workflows/tests.yml/badge.svg)](https://github.com/reteps/redfin/actions/workflows/tests.yml)

A Python wrapper around the unofficial Redfin API.

## Installation

```bash
pip install redfin
```

## Usage

```python
from redfin import Redfin

client = Redfin()

response = client.search('1600 Amphitheatre Pkwy, Mountain View, CA')
url = response['payload']['exactMatch']['url']

initial_info = client.initial_info(url)
property_id = initial_info['payload']['propertyId']

# Get estimated value
avm = client.avm_details(property_id, "")
predicted_value = avm['payload']['predictedValue']
print(f"Estimated value: {predicted_value}")

# Get neighborhood walk/bike/transit scores
stats = client.neighborhood_stats(property_id)
walk_score = stats['payload']['walkScoreInfo']['walkScoreData']['walkScore']['value']
print(f"Walk score: {walk_score}")
```

## Configuration

### Custom User-Agent

```python
client = Redfin(user_agent="MyApp/1.0 (contact@example.com)")
```

### Rate Limiting

Add a delay between requests to avoid hitting Redfin's rate limits:

```python
client = Redfin(request_delay=1.0)  # 1 second between requests
```

The client also automatically handles 429 responses by sleeping the `Retry-After` header duration and retrying once.

## CLI

```bash
redfin estimate <property_id>        # print estimate, beds/baths, last sold price
redfin neighborhood <property_id>    # print walk/bike/transit scores
```

Options:

```bash
redfin --user-agent "MyApp/1.0" estimate 12345   # custom User-Agent
redfin --delay 1.5 neighborhood 12345             # delay between requests
redfin estimate --json 12345                      # raw JSON output
```

## All Methods

### URL-based
- `initial_info(url)`
- `page_tags(url)`
- `primary_region(url)`
- `search(query)`

### Property ID-based
- `avm_details(property_id, listing_id)`
- `neighborhood_stats(property_id)`
- `below_the_fold(property_id)`
- `hood_photos(property_id)`
- `more_resources(property_id)`
- `page_header(property_id)`
- `property_comments(property_id)`
- `building_details_page(property_id)`
- `owner_estimate(property_id)`
- `claimed_home_seller_data(property_id)`
- `cost_of_home_ownership(property_id)`
- `above_the_fold(property_id, listing_id)`
- `info_panel(property_id, listing_id)`
- `similar_listings(property_id, listing_id)`
- `similar_sold(property_id, listing_id)`
- `nearby_homes(property_id, listing_id)`
- `avm_historical(property_id, listing_id)`
- `descriptive_paragraph(property_id, listing_id)`
- `tour_insights(property_id, listing_id)`
- `stats(property_id, listing_id, region_id)`

### Listing ID-based
- `floor_plans(listing_id)`
- `tour_list_date_picker(listing_id)`

### Table ID-based
- `shared_region(table_id)`

## License

MIT — see [LICENSE.txt](LICENSE.txt)
