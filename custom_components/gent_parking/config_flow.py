import logging
import requests

import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, API_URL

_LOGGER = logging.getLogger(__name__)

def fetch_garages():
    resp = requests.get(API_URL, params={"limit": 100})
    resp.raise_for_status()
    records = resp.json()["records"]
    options = {}
    for rec in records:
        fields = rec["record"]["fields"]
        gid = fields["naam"]  # unique name
        options[gid] = f"{fields['naam']} ({fields['adres']})"
    return options

class GentParkingFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            # dynamic options
            options = await self.hass.async_add_executor_job(fetch_garages)
            schema = vol.Schema({
                vol.Required("selected_garages", default=[]): vol.MultiSelect(options)
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        # create entry
        return self.async_create_entry(
            title="Gent Parking",
            data=user_input
        )

    async def async_step_import(self, user_input):
        return await self.async_step_user(user_input)

    async def async_get_options_flow(self, entry):
        return OptionsFlowHandler(entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
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
