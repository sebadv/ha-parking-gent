import logging
from datetime import timedelta
from typing import Any

import requests

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import API_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)
ATTRIBUTION = "Data provided by Stad Gent"


def _fetch_parking_payload() -> dict[str, Any]:
    """Fetch the Gent parking dataset. Runs outside the event loop."""
    resp = requests.get(API_URL, params={"limit": 100}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("Unexpected parking API response")
    return data


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for each selected garage."""
    garages = hass.data[DOMAIN][entry.entry_id]
    coordinator = ParkingDataCoordinator(hass, entry, garages)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [ParkingSensor(coordinator, gid) for gid in garages],
        update_before_add=True,
    )


class ParkingDataCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetches and stores the latest garage data."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, garages: list[str]
    ) -> None:
        """Initialize the coordinator with the config entry that owns it."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )
        self.garages = garages

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        data = await self.hass.async_add_executor_job(_fetch_parking_payload)
        records = data.get("records") or data.get("results") or []
        result: dict[str, dict[str, Any]] = {}

        for rec in records:
            # unified fields extraction
            if "record" in rec and isinstance(rec["record"], dict):
                f = rec["record"].get("fields", {})
            else:
                f = rec.get("fields", rec)

            name = f.get("naam") or f.get("name")
            if name not in self.garages:
                continue

            available = (
                f.get("vrije_plaatsen")
                or f.get("availablecapacity")
                or f.get("available_capacity")
            )
            capacity = f.get("totaal_aantal_plaatsen") or f.get("totalcapacity")
            address = f.get("adres") or f.get("address") or f.get("description", "")
            operator = (
                f.get("beheerder")
                or f.get("operator")
                or f.get("operatorinformation")
                or "Unknown"
            )

            result[name] = {
                "available": available,
                "capacity": capacity,
                "address": address,
                "operator": operator,
            }

        return result


class ParkingSensor(CoordinatorEntity[ParkingDataCoordinator], SensorEntity):
    """Sensor for one garage."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: ParkingDataCoordinator, garage_id: str) -> None:
        """Initialize a sensor for a single garage."""
        super().__init__(coordinator)
        self.garage_id = garage_id
        self._attr_name = f"{garage_id} Parking"
        self._attr_unique_id = f"gent_parking_{garage_id}"

    @property
    def native_value(self) -> int | float | str | None:
        """Return the number of free parking spaces."""
        return self.coordinator.data.get(self.garage_id, {}).get("available")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return capacity, address and operator for this garage."""
        data = self.coordinator.data.get(self.garage_id, {})
        return {
            "capacity": data.get("capacity"),
            "address": data.get("address"),
            "operator": data.get("operator"),
        }
