import json
from typing import Any, cast

import jsonschema
from pydantic import HttpUrl

from models.show import Show, ShowCreate
from services.show_service import ShowService


class InvalidImportDataError(Exception):
    pass


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
                            "ep_num",
                        ],
                        "properties": {
                            "title": {"type": "string"},
                            "watched": {"type": "boolean"},
                            "ep_num": {"type": ["integer", "null"]},
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
    """Service for importing previously updated data files, replacing the user's
    current show data.
    """

    @classmethod
    def schema_validate_import_data(cls, json_data: str) -> list[dict[str, Any]]:
        """Validates an import data file (string) against the JSON schema.

        Publicly accessible for use in export tests. Otherwise should not ordinarily
        be called from outside this class.

        Returns:
            The parsed, validated JSON object.

        Raises:
            InvalidImportDataException: if the import data is malformed JSON or fails
            schema validation
        """

        instance = json.loads(json_data)
        jsonschema.validate(instance=json.loads(json_data), schema=_import_json_schema)

        # once it's passed validation, we know it's a list of dicts, so this is a safe cast
        return cast(list[dict[str, Any]], instance)

    def __init__(self, show_service: ShowService):
        self.show_service = show_service

    async def import_shows(self, data: str) -> list[Show]:
        try:
            data_parsed: list[dict[str, Any]] = self.schema_validate_import_data(data)
        except Exception as e:
            raise InvalidImportDataError() from e

        # map JSON show serializations to ShowCreate objs we can add to the db
        new_shows = [
            ShowCreate(
                tvmaze_id=json_show["tvmaze_id"],
                title=json_show["title"],
                favorite=json_show["favorite"],
                source=json_show["source"],
                duration=json_show["duration"],
                image_sm_url=HttpUrl(
                    json_show["image_sm_url"],
                ),
                image_lg_url=HttpUrl(
                    json_show["image_lg_url"],
                ),
                imdb_id=json_show["imdb_id"],
                thetvdb_id=json_show["thetvdb_id"],
                seasons=json_show["seasons"],
            )
            for json_show in data_parsed
        ]

        # replace all saved shows with the new ones
        await self.show_service.delete_all_shows()
        shows = await self.show_service.add_many_shows(new_shows)
        return shows
