from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Parkeerbezetting Gent from a config entry."""
    # Prefer options (updated via Options Flow), fall back to data (initial selection)
    selected = entry.options.get(
        "selected_garages", entry.data.get("selected_garages", [])
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = selected

    # When options change, reload so sensors get added/removed
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True

async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry):
    """Called when the user updates options — reload the entry."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
