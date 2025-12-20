from enum import Enum
from fastapi import FastAPI, Query

app = FastAPI(title="Temperature Converter API")


class Unit(str, Enum):
    celsius = "celsius"
    fahrenheit = "fahrenheit"
    kelvin = "kelvin"


def c_to_f(c: float) -> float:
    return c * 9.0 / 5.0 + 32.0


def c_to_k(c: float) -> float:
    return c + 273.15


def f_to_c(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def k_to_c(k: float) -> float:
    return k - 273.15


def convert_value(value: float, from_unit: Unit, to_unit: Unit) -> float:
    # Normalize to Celsius
    if from_unit == Unit.celsius:
        c = value
    elif from_unit == Unit.fahrenheit:
        c = f_to_c(value)
    elif from_unit == Unit.kelvin:
        c = k_to_c(value)
    else:
        raise ValueError("Unsupported unit")

    # Convert Celsius to target
    if to_unit == Unit.celsius:
        return c
    elif to_unit == Unit.fahrenheit:
        return c_to_f(c)
    elif to_unit == Unit.kelvin:
        return c_to_k(c)
    else:
        raise ValueError("Unsupported unit")


@app.get("/")
def read_root():
    return {"message": "Temperature Converter API. Use /convert?value=...&from=...&to=..."}


@app.get("/convert")
def convert(
    value: float = Query(..., description="numeric temperature value"),
    from_unit: Unit = Query(..., alias="from", description="unit to convert from (celsius|fahrenheit|kelvin)"),
    to_unit: Unit = Query(..., alias="to", description="unit to convert to (celsius|fahrenheit|kelvin)"),
):
    """Convert temperature between Celsius, Fahrenheit and Kelvin."""
    result = convert_value(value, from_unit, to_unit)
    # Return result with reasonable rounding to avoid long floats
    return {
        "input": {"value": value, "unit": from_unit},
        "output": {"value": round(result, 6), "unit": to_unit},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
