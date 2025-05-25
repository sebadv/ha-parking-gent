import logging
import requests

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, DEFAULT_NAME, API_URL

_LOGGER = logging.getLogger(__name__)


def fetch_garages():
    """Fetch list of garages, handling both v1 and v2 responses."""
    resp = requests.get(API_URL, params={"limit": 100})
    resp.raise_for_status()
    data = resp.json()
    records = data.get("records") or data.get("results") or []
    options = {}
    for rec in records:
        # Handle v2 API response structure
        if "record" in rec and isinstance(rec["record"], dict):
            fields = rec["record"].get("fields", {})
        else:
            fields = rec.get("fields", rec)
        
        # Get name and address, trying both Dutch and English field names
        name = fields.get("naam") or fields.get("name")
        address = fields.get("adres") or fields.get("address") or fields.get("location", "")
        
        if name:
            # Clean up the address and ensure it's not empty
            if isinstance(address, str) and address.strip():
                display_name = f"{name} ({address.strip()})"
            else:
                display_name = name
            options[name] = display_name
    
    return options


class GentParkingFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the configuration flow for Parking Occupancy Ghent."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            # Even here, ensure the integration name is stored correctly
            self.hass.config_entries.async_update_entry(
                self.context.get("entry"), title=DEFAULT_NAME
            ) if self.context.get("entry") else None

            options = await self.hass.async_add_executor_job(fetch_garages)
            schema = vol.Schema({
                vol.Required("selected_garages", default=[]): cv.multi_select(options)
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        return self.async_create_entry(
            title=DEFAULT_NAME,
            data=user_input
        )

    async def async_step_import(self, user_input):
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for existing Parking Occupancy Ghent entries."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        # *** Force‑rename the entry title before showing the form ***
        self.hass.config_entries.async_update_entry(
            self.entry,
            title=DEFAULT_NAME
        )

        if user_input is None:
            options = await self.hass.async_add_executor_job(fetch_garages)
            schema = vol.Schema({
                vol.Required(
                    "selected_garages",
                    default=self.entry.options.get(
                        "selected_garages",
                        self.entry.data.get("selected_garages", []),
                    )
                ): cv.multi_select(options)
            })
            return self.async_show_form(step_id="init", data_schema=schema)

        return self.async_create_entry(title=DEFAULT_NAME, data=user_input)
