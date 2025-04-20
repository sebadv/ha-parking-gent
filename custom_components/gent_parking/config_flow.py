import logging
import requests

import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, API_URL

_LOGGER = logging.getLogger(__name__)

def fetch_garages():
    """Fetch list of garages from Ghent Open Data API, handling both v1 and v2 responses."""
    resp = requests.get(API_URL, params={"limit": 100})
    resp.raise_for_status()
    data = resp.json()
    records = data.get("records") or data.get("results") or []
    options = {}
    for rec in records:
        # v1: rec["record"]["fields"], v2: rec["fields"] or rec directly
        if "record" in rec and isinstance(rec["record"], dict):
            f = rec["record"].get("fields", {})
        elif "fields" in rec:
            f = rec["fields"]
        else:
            f = rec
        gid = f.get("naam")
        addr = f.get("adres", "")
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
                vol.Required("selected_garages", default=[]): vol.MultiSelect(options)
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        return self.async_create_entry(
            title="Gent Parking",
            data=user_input
        )

    async def async_step_import(self, user_input):
        return await self.async_step_user(user_input)

    async def async_get_options_flow(self, entry):
        return OptionsFlowHandler(entry)

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
                ): vol.MultiSelect(options)
            })
            return self.async_show_form(step_id="init", data_schema=schema)

        return self.async_create_entry(title="", data=user_input)
