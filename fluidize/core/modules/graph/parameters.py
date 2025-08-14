from fluidize.core.types.parameters import Parameter


def parse_parameters_from_json(data: dict) -> list[Parameter]:
    # If "parameters" is missing or not a list, treat it as empty
    raw_params = data.get("parameters")
    if not isinstance(raw_params, list):
        raw_params = []
    return [Parameter.model_validate(item) for item in raw_params]
