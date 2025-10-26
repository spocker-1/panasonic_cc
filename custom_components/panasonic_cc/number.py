import logging
from typing import Callable
from dataclasses import dataclass

from homeassistant.const import PERCENTAGE, UnitOfTemperature

_LOGGER = logging.getLogger(__name__)
from homeassistant.core import HomeAssistant
from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)

from aio_panasonic_comfort_cloud import PanasonicDevice, PanasonicDeviceZone, ChangeRequestBuilder
from aioaquarea import Device as AquareaDevice
from aioaquarea import ExtendedOperationMode

from . import DOMAIN
from .const import DATA_COORDINATORS, AQUAREA_COORDINATORS
from .coordinator import PanasonicDeviceCoordinator, AquareaDeviceCoordinator
from .base import PanasonicDataEntity, AquareaDataEntity

@dataclass(frozen=True, kw_only=True)
class PanasonicNumberEntityDescription(NumberEntityDescription):
    """Describes Panasonic Number entity."""
    get_value: Callable[[PanasonicDevice], int]
    set_value: Callable[[ChangeRequestBuilder, int], ChangeRequestBuilder]

@dataclass(frozen=True, kw_only=True)
class AquareaNumberEntityDescription(NumberEntityDescription):
    """Describes Aquarea Number entity."""
    zone_id: int

def create_zone_damper_description(zone: PanasonicDeviceZone):
    return PanasonicNumberEntityDescription(
        key = f"zone-{zone.id}-damper",
        translation_key=f"zone-{zone.id}-damper",
        name = f"{zone.name} Damper Position",
        icon="mdi:valve",
        native_unit_of_measurement=PERCENTAGE,
        native_max_value=100,
        native_min_value=0,
        native_step=10,
        mode=NumberMode.SLIDER,
        get_value=lambda device: zone.level,
        set_value=lambda builder, value: builder.set_zone_damper(zone.id, value),
    )

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    devices = []
    data_coordinators: list[PanasonicDeviceCoordinator] = hass.data[DOMAIN][DATA_COORDINATORS]
    for data_coordinator in data_coordinators:
        if data_coordinator.device.has_zones:
            for zone in data_coordinator.device.parameters.zones:
                devices.append(PanasonicNumberEntity(
                    data_coordinator,
                    create_zone_damper_description(zone)))

    # Aquarea Number entities for temperature targets
    aquarea_coordinators: list[AquareaDeviceCoordinator] = hass.data[DOMAIN][AQUAREA_COORDINATORS]
    for coordinator in aquarea_coordinators:
        for zone_id in coordinator.device.zones:
            zone = coordinator.device.zones.get(zone_id)
            # Add heat target temperature
            devices.append(AquareaNumberEntity(
                coordinator,
                AquareaNumberEntityDescription(
                    zone_id=zone_id,
                    key=f"zone-{zone_id}-heat-target",
                    translation_key=f"zone-{zone_id}-heat-target",
                    name=f"{zone.name} Heat Target",
                    icon="mdi:thermometer",
                    device_class=NumberDeviceClass.TEMPERATURE,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    native_max_value=zone.heat_max if zone.heat_max is not None else 30,
                    native_min_value=zone.heat_min if zone.heat_min is not None else 10,
                    native_step=1,
                    mode=NumberMode.BOX,
                )
            ))
            # Add cool target temperature if supported
            if zone.cool_max and zone.cool_min:
                devices.append(AquareaNumberEntity(
                    coordinator,
                    AquareaNumberEntityDescription(
                        zone_id=zone_id,
                        key=f"zone-{zone_id}-cool-target",
                        translation_key=f"zone-{zone_id}-cool-target",
                        name=f"{zone.name} Cool Target",
                        icon="mdi:thermometer",
                        device_class=NumberDeviceClass.TEMPERATURE,
                        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        native_max_value=zone.cool_max if zone.cool_max is not None else 30,
                        native_min_value=zone.cool_min if zone.cool_min is not None else 16,
                        native_step=1,
                        mode=NumberMode.BOX,
                    )
                ))

    async_add_entities(devices)

class PanasonicNumberEntity(PanasonicDataEntity, NumberEntity):
    """Representation of a Panasonic Number."""

    entity_description: PanasonicNumberEntityDescription

    def __init__(self, coordinator: PanasonicDeviceCoordinator, description: PanasonicNumberEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, description.key)
    

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        value = int(value)
        builder = self.coordinator.get_change_request_builder()
        self.entity_description.set_value(builder, value)
        await self.coordinator.async_apply_changes(builder)
        self._attr_native_value = value
        self.async_write_ha_state()

    def _async_update_attrs(self) -> None:
        self._attr_native_value = self.entity_description.get_value(self.coordinator.device)


class AquareaNumberEntity(AquareaDataEntity, NumberEntity):
    """Aquarea Number entity for setting target temperatures."""

    entity_description: AquareaNumberEntityDescription

    def __init__(self, coordinator: AquareaDeviceCoordinator, description: AquareaNumberEntityDescription):
        """Initialize the number entity."""
        self.entity_description = description
        super().__init__(coordinator, description.key)

    async def async_set_native_value(self, value: float) -> None:
        """Set new target temperature value."""
        zone_id = self.entity_description.zone_id
        temperature = int(value)
        
        # Determine if we're setting heat or cool based on key
        if "heat-target" in self.entity_description.key:
            # Temporarily switch mode to HEAT if needed
            original_mode = self.coordinator.device.mode
            if original_mode not in (ExtendedOperationMode.HEAT, ExtendedOperationMode.AUTO_HEAT):
                _LOGGER.debug(f"Switching to HEAT mode to set heat target for zone {zone_id}")
            await self.coordinator.device.set_temperature(temperature, zone_id)
        elif "cool-target" in self.entity_description.key:
            # Temporarily switch mode to COOL if needed
            original_mode = self.coordinator.device.mode
            if original_mode not in (ExtendedOperationMode.COOL, ExtendedOperationMode.AUTO_COOL):
                _LOGGER.debug(f"Switching to COOL mode to set cool target for zone {zone_id}")
            await self.coordinator.device.set_temperature(temperature, zone_id)
        
        self._attr_native_value = temperature
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    def _async_update_attrs(self) -> None:
        """Update the current value."""
        zone = self.coordinator.device.zones.get(self.entity_description.zone_id)
        if zone:
            # When heatSet/coolSet is not available from API, display current temperature as reference
            if "heat-target" in self.entity_description.key:
                # Try to get target temperature first, fallback to current temperature
                temp = zone.heat_target_temperature
                if temp is None:
                    # API doesn't return setpoint, use current temperature as reference
                    temp = zone.temperature
                self._attr_native_value = temp
            elif "cool-target" in self.entity_description.key:
                temp = zone.cool_target_temperature
                if temp is None:
                    temp = zone.temperature
                self._attr_native_value = temp
