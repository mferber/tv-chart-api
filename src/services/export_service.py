import json
from typing import Any

from models.show import EpisodeDescriptor, Show
from services.show_service import ShowService


class ExportService:
    def __init__(self, show_service: ShowService):
        self.show_service = show_service

    async def export(self) -> str:
        shows = await self.show_service.get_shows()
        exportable = [self.__exportable_show(show) for show in shows.values()]
        return json.dumps(exportable)

    def __exportable_show(self, show: Show) -> dict[str, Any]:
        show_dict = show.__dict__.copy()
        del show_dict["id"]
        show_dict["image_lg_url"] = str(show_dict["image_lg_url"])
        show_dict["image_sm_url"] = str(show_dict["image_sm_url"])
        show_dict["seasons"] = [
            [self.__exportable_episode(ep) for ep in season]
            for season in show_dict["seasons"]
        ]
        return show_dict

    def __exportable_episode(self, episode: EpisodeDescriptor) -> dict[str, Any]:
        return {
            "title": episode.title,
            "watched": episode.watched,
            "ep_num": episode.ep_num,
        }
