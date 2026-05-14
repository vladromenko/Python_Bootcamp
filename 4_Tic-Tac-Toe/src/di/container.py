from datasource.repository.game_repository import GameRepository
from datasource.repository.game_storage import GameStorage
from domain.service.game_service_impl import GameServiceImpl


class Container:
    def __init__(self) -> None:
        self._storage = GameStorage()
        self._repository = GameRepository(self._storage)
        self._game_service = GameServiceImpl(self._repository)

    @property
    def game_service(self) -> GameServiceImpl:
        return self._game_service
