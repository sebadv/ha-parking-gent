from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DEFAULT_NAME

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Parkeerbezetting Gent from a config entry."""
    # Retrieve selected garages, preferring updated options
    selected = entry.options.get(
        "selected_garages", entry.data.get("selected_garages", [])
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = selected

    # Listen for option updates: rename entry and reload
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    # Forward setup to sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True

async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Called when the user updates options — rename & reload the entry."""
    # Update the stored title to match DEFAULT_NAME
    hass.config_entries.async_update_entry(entry, title=DEFAULT_NAME)
    # Reload the config entry to apply new options
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
