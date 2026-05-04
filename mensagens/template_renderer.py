import json
import re

VARIABLE_REGEX = r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}"


def extract_template_variables(text):
    if not text:
        return []

    return sorted(set(re.findall(VARIABLE_REGEX, text)))


def parse_variables_payload(raw_text):
    if not raw_text:
        return {}

    raw_text = raw_text.strip()

    if not raw_text:
        return {}

    try:
        data = json.loads(raw_text)
        if not isinstance(data, dict):
            raise ValueError("As variáveis precisam estar em formato de objeto JSON.")
        return {str(key): str(value) for key, value in data.items()}
    except json.JSONDecodeError:
        variables = {}

        for line in raw_text.splitlines():
            line = line.strip()

            if not line:
                continue

            if "=" not in line:
                raise ValueError(
                    "Use JSON válido ou linhas no formato chave=valor."
                ) from None

            key, value = line.split("=", 1)
            variables[key.strip()] = value.strip()

        return variables


def render_message_text(text, variables):
    if not text:
        return ""

    def replace(match):
        variable_name = match.group(1).strip()
        return variables.get(variable_name, match.group(0))

    return re.sub(VARIABLE_REGEX, replace, text)


def get_missing_variables(text, variables):
    required = extract_template_variables(text)
    provided = set(variables.keys())

    return [variable for variable in required if variable not in provided]
