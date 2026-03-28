import jsonschema

from services.show import ShowService

_import_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "tvmaze_id",
            "title",
            "favorite",
            "source",
            "duration",
            "image_sm_url",
            "image_lg_url",
            "imdb_id",
            "thetvdb_id",
            "seasons",
        ],
        "properties": {
            "tvmaze_id": {"type": "integer"},
            "title": {"type": "string"},
            "favorite": {"type": "boolean"},
            "source": {"type": "string"},
            "duration": {
                "type": "integer",
                "description": "Episode duration in minutes",
            },
            "image_sm_url": {"type": "string", "format": "uri"},
            "image_lg_url": {"type": "string", "format": "uri"},
            "imdb_id": {"type": "string"},
            "thetvdb_id": {"type": "integer"},
            "seasons": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": [
                            "title",
                            "watched",
                            "display_number",
                            "type",
                        ],
                        "properties": {
                            "title": {"type": "string"},
                            "watched": {"type": "boolean"},
                            "display_number": {"type": ["integer", "null"]},
                            "type": {
                                "type": "string",
                                "enum": ["episode", "special"],
                            },
                        },
                        "additionalProperties": False,
                    },
                },
            },
        },
        "additionalProperties": False,
    },
}


class ImportService:
    @classmethod
    def validate_import_data(cls, json: str) -> None:
        """Validates an import data style against the JSON schema.
        Raises an error if validation fails.
        """
        jsonschema.validate(instance=json, schema=_import_json_schema)

    def __init__(self, show_service: ShowService):
        self.show_service = show_service

    def import_shows(self, json: str) -> None:
        self.validate_import_data(json)
        print("importing")
