from __future__ import annotations

import aiohttp

from .const import MOONRAKER_PORT

_TIMEOUT = aiohttp.ClientTimeout(total=8)


class CannotConnect(Exception):
    pass


class InvalidResponse(Exception):
    pass


class AceDryerAPI:
    def __init__(self, host: str, port: int = MOONRAKER_PORT) -> None:
        self._base = f"http://{host}:{port}"
        self._session: aiohttp.ClientSession | None = None

    def _session_(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_mmu_machine(self) -> dict:
        """Return the mmu_machine subtree from /server/mmu-ace."""
        try:
            async with self._session_().get(
                f"{self._base}/server/mmu-ace", timeout=_TIMEOUT
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["result"]["status"]["mmu_machine"]
        except aiohttp.ClientConnectorError as err:
            raise CannotConnect(str(err)) from err
        except (KeyError, TypeError) as err:
            raise InvalidResponse(str(err)) from err

    async def start_drying(
        self, unit_id: int, temp: int, duration: int, fan_speed: int
    ) -> None:
        async with self._session_().post(
            f"{self._base}/server/filament_hub/start_drying",
            json={"id": unit_id, "temp": temp, "duration": duration, "fan_speed": fan_speed},
            timeout=_TIMEOUT,
        ) as resp:
            resp.raise_for_status()

    async def stop_drying(self, unit_id: int) -> None:
        async with self._session_().post(
            f"{self._base}/server/filament_hub/stop_drying",
            json={"id": unit_id},
            timeout=_TIMEOUT,
        ) as resp:
            resp.raise_for_status()

    async def set_fan_speed(self, unit_id: int, speed: int) -> None:
        async with self._session_().post(
            f"{self._base}/server/filament_hub/set_fan_speed",
            json={"id": unit_id, "fan_speed": speed},
            timeout=_TIMEOUT,
        ) as resp:
            resp.raise_for_status()

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
