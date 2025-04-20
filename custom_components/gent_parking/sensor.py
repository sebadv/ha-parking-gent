import logging
import requests

from datetime import timedelta
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, CoordinatorEntity
)
from homeassistant.const import ATTR_ATTRIBUTION
from .const import DOMAIN, API_URL

_LOGGER = logging.getLogger(__name__)
ATTRIBUTION = "Data provided by Stad Gent"

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors for each selected garage."""
    garages = hass.data[DOMAIN][entry.entry_id]
    coordinator = ParkingDataCoordinator(hass, garages)
    await coordinator.async_config_entry_first_refresh()

    entities = [ParkingSensor(coordinator, gid) for gid in garages]
    async_add_entities(entities, update_before_add=True)

class ParkingDataCoordinator(DataUpdateCoordinator):
    """Fetches and stores the latest garage data."""

    def __init__(self, hass, garages):
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=1)
        )
        self.garages = garages

    async def _async_update_data(self):
        resp = await self.hass.async_add_executor_job(
            requests.get, API_URL, {"limit": 100}
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records") or data.get("results") or []
        result = {}

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

class ParkingSensor(CoordinatorEntity):
    """Sensor for one garage."""

    def __init__(self, coordinator, garage_id):
        super().__init__(coordinator)
        self.garage_id = garage_id
        self._attr_name = f"{garage_id} Parking"
        self._attr_unique_id = f"gent_parking_{garage_id}"

    @property
    def state(self):
        return self.coordinator.data.get(self.garage_id, {}).get("available")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.garage_id, {})
        return {
            "capacity": data.get("capacity"),
            "address": data.get("address"),
            "operator": data.get("operator"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
