import logging
import requests

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, API_URL

_LOGGER = logging.getLogger(__name__)

def fetch_garages():
    """Fetch list of garages from Ghent Open Data API, handling both v1 and v2 responses."""
    resp = requests.get(API_URL, params={"limit": 100})
    resp.raise_for_status()
    data = resp.json()
    # v1 uses "records", v2 uses "results"
    records = data.get("records") or data.get("results") or []
    options = {}
    for rec in records:
        # extract the fields dict
        if "record" in rec and isinstance(rec["record"], dict):
            f = rec["record"].get("fields", {})
        elif "fields" in rec:
            f = rec["fields"]
        else:
            f = rec

        # try Dutch first, then English
        gid = f.get("naam") or f.get("name")
        # address: prefer adres/address, else fall back to description
        addr = f.get("adres") or f.get("address") or f.get("description", "")
        if gid:
            options[gid] = f"{gid} ({addr})"
    return options

class GentParkingFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the configuration flow for Gent Parking integration."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            options = await self.hass.async_add_executor_job(fetch_garages)
            schema = vol.Schema({
                vol.Required("selected_garages", default=[]): cv.multi_select(options)
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        return self.async_create_entry(
            title="Gent Parking",
            data=user_input
        )

    async def async_step_import(self, user_input):
        """Support importing from YAML (if you ever add that)."""
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry):
        """Provide an options flow to add/remove garages later."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for existing Gent Parking config entries."""
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is None:
            options = await self.hass.async_add_executor_job(fetch_garages)
            schema = vol.Schema({
                vol.Required(
                    "selected_garages",
                    default=self.entry.data.get("selected_garages", []),
                ): cv.multi_select(options)
            })
            return self.async_show_form(step_id="init", data_schema=schema)

        return self.async_create_entry(title="", data=user_input)
