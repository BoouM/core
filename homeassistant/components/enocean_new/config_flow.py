"""Config flow for EnOcean integration."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import usb
from homeassistant.components.hassio import is_hassio
from homeassistant.const import CONF_NAME, CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_USE_ADDON, DEFAULT_URL, DOMAIN

ON_MANUAL_SCHEMA = vol.Schema({vol.Required(CONF_URL, default=DEFAULT_URL): str})
ON_SUPERVISOR_SCHEMA = vol.Schema({vol.Optional(CONF_USE_ADDON, default=True): bool})
TITLE = "EnOcean"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EnOcean."""

    VERSION = 1
    MINOR_VERSION = 0

    def __init__(self) -> None:
        """Set up flow instance."""
        super().__init__()
        self.use_addon = False
        self._title: str | None = None
        self._usb_discovery = False

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a manual configuration."""
        if user_input is None:
            return self.async_show_form(step_id="manual", data_schema=ON_MANUAL_SCHEMA)
        errors: dict[str, str] = {}
        if errors is {}:
            return self._async_create_entry_from_flow()

        return self.async_show_form(
            step_id="manual",
            data_schema=ON_MANUAL_SCHEMA(user_input),
            errors=errors,
        )

    async def async_step_on_supervisor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle logic when on Supervisor host."""
        if user_input is None:
            return self.async_show_form(
                step_id="on_supervisor", data_schema=ON_SUPERVISOR_SCHEMA
            )
        if not user_input[CONF_USE_ADDON]:
            return await self.async_step_manual()

        self.use_addon = True
        return await self.async_step_manual()

    async def async_step_usb(self, discovery_info: usb.UsbServiceInfo) -> FlowResult:
        """Handle USB Discovery."""
        if not is_hassio(self.hass):
            return self.async_abort(reason="discovery_requires_supervisor")
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        if self._async_in_progress():
            return self.async_abort(reason="already_in_progress")

        await self.async_set_unique_id("123-456-789")
        return await self.async_step_usb_confirm()

    async def async_step_usb_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle USB Discovery confirmation."""
        if user_input is None:
            return self.async_show_form(
                step_id="usb_confirm",
                description_placeholders={CONF_NAME: self._title},
            )

        self._usb_discovery = True

        return await self.async_step_on_supervisor({CONF_USE_ADDON: True})

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if is_hassio(self.hass):
            return await self.async_step_on_supervisor()

        return await self.async_step_manual()

    @callback
    def _async_create_entry_from_flow(self) -> FlowResult:
        """Return a config entry for the flow."""
        return self.async_create_entry(title=TITLE, data={})
