#!/usr/bin/env python3
import boto3
import yaml
import csv
from datetime import datetime
from pathlib import Path
from botocore.exceptions import ClientError


class AWSResourceInventory:
    def __init__(self):
        self.session = boto3.Session(region_name="us-east-1")
        self.account_id = self.session.client("sts").get_caller_identity()["Account"]
        self.regions = self._get_regions()
        self.run_dir = Path("inventory") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir.mkdir(parents=True, exist_ok=True)

        with open("config.yaml") as f:
            self.config = yaml.safe_load(f)

    def _get_regions(self):
        try:
            ec2 = self.session.client("ec2")
            return [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
        except ClientError:
            return ["us-east-1"]

    def _get_value(self, item, path):
        value = item
        try:
            for key in path.split("."):
                value = value[key] if isinstance(value, dict) else ""
        except (KeyError, TypeError):
            value = ""
        return value.isoformat() if hasattr(value, "isoformat") else value

    def _get_items_from_response(self, response, path):
        items = [response]
        for part in path.split("."):
            if part == "[]":
                items = [item for sublist in items for item in sublist]
            else:
                items = [item[part] for item in items if isinstance(item, dict)]
        return items

    def _get_resource_data(self, service_name, region, config):
        try:
            client = boto3.client(config["service"], region_name=region)
            method = getattr(client, config["method"])
            response = method()
            items = self._get_items_from_response(response, config["response_key"])

            resources = []
            for item in items:
                try:
                    if "detail_method" in config:
                        detail = config["detail_method"]
                        params = {detail["param"]: item}
                        item = self._get_items_from_response(
                            getattr(client, detail["name"])(**params), detail["response_key"]
                        )[0]

                    data = {"Region": region}
                    for field in config["fields"]:
                        source, target = field.split(":") if ":" in field else (field, field)
                        data[target] = self._get_value(item, source)
                    resources.append(data)
                except ClientError:
                    continue

            return resources
        except ClientError as e:
            print(f"Skipping {service_name} in {region}: {e.response['Error']['Code']}")
            return []

    def collect_resources(self):
        print(f"Starting inventory for Account: {self.account_id}")

        for service_name, config in self.config["resources"].items():
            print(f"Collecting {service_name} resources...")
            all_resources = []

            regions = ["us-east-1"] if config["service"] == "s3" else self.regions
            all_resources = sum(
                [self._get_resource_data(service_name, region, config) for region in regions], []
            )

            if all_resources:
                with open(self.run_dir / f"{service_name}.csv", "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=all_resources[0].keys())
                    writer.writeheader()
                    writer.writerows(all_resources)


def main():
    inventory = AWSResourceInventory()
    inventory.collect_resources()


if __name__ == "__main__":
    main()
