#!/usr/bin/env python3
"""Simple CLI for the redfin library."""

import argparse
import json
import sys

from redfin.redfin import Redfin


def cmd_estimate(client, args):
    """Get the Redfin estimate for a property ID."""
    result = client.avm_details(args.property_id, "")
    if result.get("resultCode") != 0:
        print(f"Error: {result.get('errorMessage')}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        print(json.dumps(result.get("payload", {}), indent=2))
        return
    payload = result.get("payload", {})
    predicted = payload.get("predictedValue")
    preview = payload.get("sectionPreviewText", "")
    address = payload.get("streetAddress", {}).get("assembledAddress", "Unknown")
    beds = payload.get("numBeds", "?")
    baths = payload.get("numBaths", "?")
    sqft = payload.get("sqFt", {}).get("value", "?")
    last_sold = payload.get("lastSoldPrice")
    lat = payload.get("latLong", {}).get("latitude")
    lng = payload.get("latLong", {}).get("longitude")

    print(f"Address:       {address}")
    print(f"Beds/Baths:    {beds} bed / {baths} bath / {sqft} sqft")
    if predicted:
        print(f"Estimate:      ${predicted:,.0f}")
    if preview:
        print(f"Summary:       {preview}")
    if last_sold is not None:
        print(f"Last Sold:     ${last_sold:,.0f}")
    if lat and lng:
        print(f"Location:      {lat}, {lng}")


def cmd_neighborhood(client, args):
    """Get neighborhood stats (walk/bike/transit scores) for a property ID."""
    result = client.neighborhood_stats(args.property_id)
    if result.get("resultCode") != 0:
        print(f"Error: {result.get('errorMessage')}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        print(json.dumps(result.get("payload", {}), indent=2))
        return
    payload = result.get("payload", {})
    addr_info = payload.get("addressInfo", {})
    city = addr_info.get("city", "?")
    state = addr_info.get("state", "?")
    print(f"City/State:    {city}, {state}")

    try:
        score_data = payload["walkScoreInfo"]["walkScoreData"]
        walk = score_data["walkScore"]["value"]
        walk_desc = score_data["walkScore"].get("shortDescription", "")
        bike = score_data["bikeScore"]["value"]
        transit = score_data["transitScore"]["value"]
        print(f"Walk Score:    {walk:.0f}  ({walk_desc})")
        print(f"Bike Score:    {bike:.0f}")
        print(f"Transit Score: {transit:.0f}")
    except (KeyError, TypeError):
        print("Walk/bike/transit scores not available.")


def main():
    parser = argparse.ArgumentParser(
        prog="redfin",
        description="Query Redfin property data from the command line.",
    )
    parser.add_argument(
        "--user-agent", default=None, help="Override the User-Agent header"
    )
    parser.add_argument(
        "--delay", type=float, default=0, help="Delay between requests (seconds)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # estimate command
    p_estimate = subparsers.add_parser(
        "estimate", help="Get Redfin estimate for a property"
    )
    p_estimate.add_argument("property_id", help="Redfin property ID (numeric)")
    p_estimate.add_argument(
        "--json", action="store_true", help="Output raw JSON payload"
    )

    # neighborhood command
    p_neighborhood = subparsers.add_parser(
        "neighborhood", help="Get walk/bike/transit scores for a property"
    )
    p_neighborhood.add_argument("property_id", help="Redfin property ID (numeric)")
    p_neighborhood.add_argument(
        "--json", action="store_true", help="Output raw JSON payload"
    )

    args = parser.parse_args()
    client = Redfin(user_agent=args.user_agent, request_delay=args.delay)

    if args.command == "estimate":
        cmd_estimate(client, args)
    elif args.command == "neighborhood":
        cmd_neighborhood(client, args)


if __name__ == "__main__":
    main()
