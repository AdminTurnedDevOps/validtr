# Local Development

## Engine Dev Loop

```bash
cd validtr-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn api.server:app --host 127.0.0.1 --port 4041 --reload
```

## CLI Dev Loop

```bash
cd validtr-cli
go build -o ../validtr .
cd ..
./validtr --help
```

## Docs Dev Loop

```bash
cd docs
npm install
npm run docs:dev
```

## Test Commands

```bash
cd validtr-engine
pytest

cd ../validtr-cli
go test ./...
```
