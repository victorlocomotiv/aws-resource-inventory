# AWS Resource Inventory

Simple script to inventory AWS resources across all regions. Output is saved as CSV files in timestamped folders.

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit
pip install pre-commit
pre-commit install
```

## Usage

Just run:
```bash
python3 aws_inventory.py
```

Output will be saved in `inventory/YYYYMMDD_HHMMSS/*.csv`

## Adding New Resources

Edit `config.yaml` to add new AWS resources. Example format:

```yaml
resources:
  service_name:
    service: aws_service_name
    method: aws_method_name
    response_key: ResponseKey.[].Items.[]
    fields:
      - FieldName
      - NestedField.Path:AliasName
      - Tags

  # Example for services needing detail calls
  service_with_details:
    service: aws_service
    method: list_items
    response_key: Items.[]
    detail_method:
      name: describe_item
      param: ItemName
      response_key: ItemDetails
    fields:
      - Field1
      - Field2.Path:Alias
```

## Pre-commit

Run checks manually:
```bash
pre-commit run --all-files
```

Run specific check:
```bash
pre-commit run black --all-files
```
