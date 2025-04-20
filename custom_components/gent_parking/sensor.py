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
    """Coordinator to fetch and store parking data."""

    def __init__(self, hass, garages):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )
        self.garages = garages

    async def _async_update_data(self):
        params = {"limit": 100}
        resp = await self.hass.async_add_executor_job(
            requests.get, API_URL, params
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records") or data.get("results") or []
        result = {}
        for rec in records:
            # Handle both v1 and v2 response shapes
            if "record" in rec and isinstance(rec["record"], dict):
                f = rec["record"].get("fields", {})
            elif "fields" in rec:
                f = rec["fields"]
            else:
                f = rec
            name = f.get("naam")
            if name in self.garages:
                result[name] = {
                    "available": f.get("vrije_plaatsen"),
                    "capacity": f.get("totaal_aantal_plaatsen"),
                    "address": f.get("adres"),
                    "operator": f.get("beheerder", "Unknown")
                }
        return result

class ParkingSensor(CoordinatorEntity):
    """Sensor representing a single garage's available spots."""

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
