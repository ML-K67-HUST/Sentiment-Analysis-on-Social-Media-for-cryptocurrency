# Requirements for local development
# Use UV for faster installation: uv pip install -r requirements.txt

## Run này để setup:
```bash
# Xóa venv cũ (nặng)
rm -rf venv/

# Install UV nếu chưa có
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt

# Chạy consumer
./scripts/run_consumer.sh sentiment
```

## Hoặc dùng pip thông thường:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
