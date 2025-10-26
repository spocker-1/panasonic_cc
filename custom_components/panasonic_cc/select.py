from typing import Callable, Any
from dataclasses import dataclass
import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.select import SelectEntity, SelectEntityDescription

from .const import DOMAIN, DATA_COORDINATORS, AQUAREA_COORDINATORS, SELECT_HORIZONTAL_SWING, SELECT_VERTICAL_SWING
from aio_panasonic_comfort_cloud import PanasonicDevice, ChangeRequestBuilder, constants

from .coordinator import PanasonicDeviceCoordinator, AquareaDeviceCoordinator
from .base import PanasonicDataEntity, AquareaDataEntity
from aioaquarea import Device as AquareaDevice, SpecialStatus, PowerfulTime

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class PanasonicSelectEntityDescription(SelectEntityDescription):
    """Description of a select entity."""
    set_option: Callable[[ChangeRequestBuilder, str], ChangeRequestBuilder]
    get_current_option: Callable[[PanasonicDevice], str]
    is_available: Callable[[PanasonicDevice], bool]
    get_options: Callable[[PanasonicDevice], list[str]] = None

@dataclass(frozen=True, kw_only=True)
class AquareaSelectEntityDescription(SelectEntityDescription):
    """Description of an Aquarea select entity."""
    get_current_option: Callable[[AquareaDevice], str]
    set_option: Callable[[AquareaDevice, str], Any]  # Returns awaitable
    is_available: Callable[[AquareaDevice], bool]


HORIZONTAL_SWING_DESCRIPTION = PanasonicSelectEntityDescription(
    key=SELECT_HORIZONTAL_SWING, 
    translation_key=SELECT_HORIZONTAL_SWING,
    icon="mdi:swap-horizontal",
    name="Horizontal Swing Mode",
    options= [opt.name for opt in constants.AirSwingLR if opt != constants.AirSwingLR.Unavailable],
    set_option = lambda builder, new_value : builder.set_horizontal_swing(new_value),
    get_current_option = lambda device : device.parameters.horizontal_swing_mode.name,
    is_available = lambda device : device.has_horizontal_swing
)
VERTICAL_SWING_DESCRIPTION = PanasonicSelectEntityDescription(
    key=SELECT_VERTICAL_SWING, 
    translation_key=SELECT_VERTICAL_SWING,
    icon="mdi:swap-vertical",
    name="Vertical Swing Mode",
    get_options= lambda device: [opt.name for opt in constants.AirSwingUD if opt != constants.AirSwingUD.Swing or device.features.auto_swing_ud],
    set_option = lambda builder, new_value : builder.set_vertical_swing(new_value),
    get_current_option = lambda device : device.parameters.vertical_swing_mode.name,
    is_available = lambda device : True
)

# Aquarea Select entities
AQUAREA_SPECIAL_STATUS_DESCRIPTION = AquareaSelectEntityDescription(
    key="special_status",
    translation_key="special_status",
    name="Special Status",
    icon="mdi:thermostat",
    options=["NORMAL", "ECO", "COMFORT"],
    get_current_option=lambda device: device.special_status.name if device.special_status else "NORMAL",
    set_option=lambda device, value: device.set_special_status(SpecialStatus[value] if value != "NORMAL" else None),
    is_available=lambda device: device.support_special_status
)

AQUAREA_POWERFUL_TIME_DESCRIPTION = AquareaSelectEntityDescription(
    key="powerful_time",
    translation_key="powerful_time",
    name="Powerful Mode",
    icon="mdi:timer",
    options=["OFF", "30MIN", "60MIN", "90MIN"],
    get_current_option=lambda device: device.powerful_time.name,
    set_option=lambda device, value: device.set_powerful_time(PowerfulTime[value]),
    is_available=lambda device: True
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    entities = []
    data_coordinators: list[PanasonicDeviceCoordinator] = hass.data[DOMAIN][DATA_COORDINATORS]
    aquarea_coordinators: list[AquareaDeviceCoordinator] = hass.data[DOMAIN][AQUAREA_COORDINATORS]
    
    for coordinator in data_coordinators:
        entities.append(PanasonicSelectEntity(coordinator, HORIZONTAL_SWING_DESCRIPTION))
        entities.append(PanasonicSelectEntity(coordinator, VERTICAL_SWING_DESCRIPTION))
    
    # Add Aquarea entities
    for coordinator in aquarea_coordinators:
        entities.append(AquareaSelectEntity(coordinator, AQUAREA_SPECIAL_STATUS_DESCRIPTION))
        entities.append(AquareaSelectEntity(coordinator, AQUAREA_POWERFUL_TIME_DESCRIPTION))
        
    async_add_entities(entities)

class PanasonicSelectEntityBase(SelectEntity):
    """Base class for all select entities."""
    entity_description: PanasonicSelectEntityDescription

class PanasonicSelectEntity(PanasonicDataEntity, PanasonicSelectEntityBase):

    def __init__(self, coordinator: PanasonicDeviceCoordinator, description: PanasonicSelectEntityDescription):
        self.entity_description = description
        if description.get_options is not None:
            self._attr_options = description.get_options(coordinator.device)
        super().__init__(coordinator, description.key)
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.entity_description.is_available(self.coordinator.device)

    async def async_select_option(self, option: str) -> None:
        builder = self.coordinator.get_change_request_builder()
        self.entity_description.set_option(builder, option)
        await self.coordinator.async_apply_changes(builder)
        self._attr_current_option = option
        self.async_write_ha_state()

    def _async_update_attrs(self) -> None:
        self.current_option = self.entity_description.get_current_option(self.coordinator.device)


class AquareaSelectEntity(AquareaDataEntity, SelectEntity):
    """Representation of an Aquarea select entity."""

    entity_description: AquareaSelectEntityDescription

    def __init__(self, coordinator: AquareaDeviceCoordinator, description: AquareaSelectEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.entity_description.is_available(self.coordinator.device)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.set_option(self.coordinator.device, option)
        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    def _async_update_attrs(self) -> None:
        """Update the current option."""
        self._attr_current_option = self.entity_description.get_current_option(self.coordinator.device)

