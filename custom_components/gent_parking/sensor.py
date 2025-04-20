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
    garages = entry.data["selected_garages"]
    coordinator = ParkingDataCoordinator(hass, garages)
    await coordinator.async_config_entry_first_refresh()

    entities = [
        ParkingSensor(coordinator, garage_id)
        for garage_id in garages
    ]
    async_add_entities(entities, update_before_add=True)

class ParkingDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, garages):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )
        self.garages = garages
        self.data = {}

    async def _async_update_data(self):
        params = {"limit": 100}
        resp = await self.hass.async_add_executor_job(requests.get, API_URL, params)
        resp.raise_for_status()
        records = resp.json()["records"]
        result = {}
        for rec in records:
            f = rec["record"]["fields"]
            name = f["naam"]
            if name in self.garages:
                result[name] = {
                    "available": f["vrije_plaatsen"],
                    "capacity": f["totaal_aantal_plaatsen"],
                    "address": f["adres"],
                    "operator": f.get("beheerder", "Unknown")
                }
        return result

class ParkingSensor(CoordinatorEntity):
    def __init__(self, coordinator, garage_id):
        super().__init__(coordinator)
        self.garage_id = garage_id
        self._attr_name = f"{garage_id} Parking"
        self._attr_unique_id = f"gent_parking_{garage_id}"

    @property
    def state(self):
        data = self.coordinator.data.get(self.garage_id) or {}
        return data.get("available")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.garage_id) or {}
        return {
            "capacity": data.get("capacity"),
            "address": data.get("address"),
            "operator": data.get("operator"),
            ATTR_ATTRIBUTION: ATTRIBUTION
        }
