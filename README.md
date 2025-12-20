# simple-temperature-converter
A simple temperature converter API

---

## Usage 🔧

- Install dependencies:

```bash
python -m pip install -r requirements.txt
```

- Run the app locally:

```bash
uvicorn main:app --reload
```

- Example request:

```bash
curl "http://127.0.0.1:8000/convert?value=0&from=celsius&to=fahrenheit"
# => {"input":{"value":0.0,"unit":"celsius"},"output":{"value":32.0,"unit":"fahrenheit"}}
```

- Run tests:

```bash
pytest -q
```

## Endpoints

- `GET /` — basic info message
- `GET /convert` — query params: `value` (float), `from` (celsius|fahrenheit|kelvin), `to` (celsius|fahrenheit|kelvin)

---

## Docker

Build locally:

```bash
docker build -t simple-temperature-converter:latest .
```

Run the container:

```bash
docker run --rm -p 8000:8000 simple-temperature-converter:latest
# then visit http://127.0.0.1:8000
```

## CI (GitHub Actions)

A workflow is included at `.github/workflows/ci.yml` that runs the test suite on push and pull requests and builds the Docker image after tests pass.

---

Happy converting! ✅
