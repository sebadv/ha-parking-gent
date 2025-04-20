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
    """Fetches and stores the latest garage data."""

    def __init__(self, hass, garages):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
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
            if "record" in rec and isinstance(rec["record"], dict):
                f = rec["record"].get("fields", {})
            elif "fields" in rec:
                f = rec["fields"]
            else:
                f = rec

            # pick the garage identifier
            name = f.get("naam") or f.get("name")
            if name not in self.garages:
                continue

            # available spots: Dutch or English key
            available = (
                f.get("vrije_plaatsen")
                or f.get("availablecapacity")
                or f.get("available_capacity")
                or f.get("freeparking")
            )
            # total capacity: Dutch or English
            capacity = (
                f.get("totaal_aantal_plaatsen")
                or f.get("totalcapacity")
            )
            # address: try adres/address, else description
            address = (
                f.get("adres")
                or f.get("address")
                or f.get("description")
                or ""
            )
            # operator info
            operator = (
                f.get("beheerder")
                or f.get("operatorinformation")
                or f.get("operator")
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
        data = self.coordinator.data.get(self.garage_id, {})
        return data.get("available")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.garage_id, {})
        return {
            "capacity": data.get("capacity"),
            "address": data.get("address"),
            "operator": data.get("operator"),
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
