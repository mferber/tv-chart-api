from typing import Any

from pydantic import BaseModel, ValidationError

from models.show import Show, ShowCreate
from services.show_service import ShowService


class InvalidImportDataError(Exception):
    def __init__(self, message: str, details: Any) -> None:
        self.message = message
        self.details = details


class InvalidImportVersionError(Exception):
    pass


class ImportModel(BaseModel):
    version: str
    shows: list[ShowCreate]


class ImportService:
    """Service for importing previously updated data files, replacing the user's
    current show data.
    """

    @classmethod
    def validate_import_data(cls, json_data: str) -> ImportModel:
        """Validates an import data file (string) against the JSON schema.

        Publicly accessible for use in export tests. Otherwise should not ordinarily
        be called from outside this class.

        Returns:
            The parsed, validated JSON object.

        Raises:
            InvalidImportDataException: if the import data is malformed JSON or fails
            schema validation
        """

        return ImportModel.model_validate_json(json_data, strict=True, extra="forbid")

    def __init__(self, show_service: ShowService):
        self.show_service = show_service

    async def import_(self, data: str) -> list[Show]:
        try:
            data_parsed = self.validate_import_data(data)

            match data_parsed.version:
                case "0.0.1":
                    return await self._import_v0_0_1(data_parsed)
                case _:
                    raise InvalidImportVersionError

        except Exception as e:
            message = ""
            details: str | None = None
            if isinstance(e, ValidationError):
                message = "Import file validation failed"
                details = str(e)
            if isinstance(e, InvalidImportVersionError):
                message = (
                    f'Unknown import file version identifier: "{data_parsed.version}"'
                )
                details = None
            raise InvalidImportDataError(message=message, details=details) from e

    async def _import_v0_0_1(self, data_parsed: ImportModel) -> list[Show]:
        # replace all saved shows with the new ones
        await self.show_service.delete_all_shows()
        shows = await self.show_service.add_many_shows(data_parsed.shows)
        return shows
