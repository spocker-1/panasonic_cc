from typing import Callable, Any
from dataclasses import dataclass
import logging

from homeassistant.const import UnitOfTemperature, EntityCategory, PERCENTAGE
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
    SensorEntityDescription
)

from aio_panasonic_comfort_cloud import PanasonicDevice, PanasonicDeviceEnergy, PanasonicDeviceZone, constants
from aioaquarea import Device as AquareaDevice

from .const import (
    DOMAIN,
    DATA_COORDINATORS,
    ENERGY_COORDINATORS,
    AQUAREA_COORDINATORS
    )
from .base import PanasonicDataEntity, PanasonicEnergyEntity, AquareaDataEntity
from .coordinator import PanasonicDeviceCoordinator, PanasonicDeviceEnergyCoordinator, AquareaDeviceCoordinator

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class PanasonicSensorEntityDescription(SensorEntityDescription):
    """Describes Panasonic sensor entity."""
    get_state: Callable[[PanasonicDevice], Any] | None = None
    is_available: Callable[[PanasonicDevice], bool] | None = None

@dataclass(frozen=True, kw_only=True)
class PanasonicEnergySensorEntityDescription(SensorEntityDescription):
    """Describes Panasonic sensor entity."""
    get_state: Callable[[PanasonicDeviceEnergy], Any]| None = None

@dataclass(frozen=True, kw_only=True)
class AquareaSensorEntityDescription(SensorEntityDescription):
    """Describes Aquarea sensor entity."""
    get_state: Callable[[AquareaDevice], Any] | None = None
    is_available: Callable[[AquareaDevice], bool]| None = None

INSIDE_TEMPERATURE_DESCRIPTION = PanasonicSensorEntityDescription(
    key="inside_temperature",
    translation_key="inside_temperature",
    name="Inside Temperature",
    icon="mdi:thermometer",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    get_state=lambda device: device.parameters.inside_temperature,
    is_available=lambda device: device.parameters.inside_temperature is not None,
)
OUTSIDE_TEMPERATURE_DESCRIPTION = PanasonicSensorEntityDescription(
    key="outside_temperature",
    translation_key="outside_temperature",
    name="Outside Temperature",
    icon="mdi:thermometer",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    get_state=lambda device: device.parameters.outside_temperature,
    is_available=lambda device: device.parameters.outside_temperature is not None,
)
LAST_UPDATE_TIME_DESCRIPTION = PanasonicSensorEntityDescription(
    key="last_update",
    translation_key="last_update",
    name="Last Updated",
    icon="mdi:clock-outline",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
    state_class=None,
    native_unit_of_measurement=None,
    get_state=lambda device: device.last_update,
    is_available=lambda device: True,
    entity_registry_enabled_default=False,
)
DATA_AGE_DESCRIPTION = PanasonicSensorEntityDescription(
    key="data_age",
    translation_key="data_age",
    name="Cached Data Age",
    icon="mdi:clock-outline",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
    state_class=None,
    native_unit_of_measurement=None,
    get_state=lambda device: device.timestamp,
    is_available=lambda device: device.info.status_data_mode == constants.StatusDataMode.CACHED,
    entity_registry_enabled_default=False,
)
DATA_MODE_DESCRIPTION = PanasonicSensorEntityDescription(
    key="status_data_mode",
    translation_key="status_data_mode",
    name="Data Mode",
    options=[opt.name for opt in constants.StatusDataMode],
    device_class=SensorDeviceClass.ENUM,
    entity_category=EntityCategory.DIAGNOSTIC,
    state_class=None,
    native_unit_of_measurement=None,
    get_state=lambda device: device.info.status_data_mode.name,
    is_available=lambda device: True,
    entity_registry_enabled_default=True,
)
DAILY_ENERGY_DESCRIPTION = PanasonicEnergySensorEntityDescription(
    key="daily_energy_sensor",
    translation_key="daily_energy_sensor",
    name="Daily Energy",
    icon="mdi:flash",
    device_class=SensorDeviceClass.ENERGY,
    state_class=SensorStateClass.TOTAL_INCREASING,
    native_unit_of_measurement="kWh",
    get_state=lambda energy: energy.consumption
)
DAILY_HEATING_ENERGY_DESCRIPTION = PanasonicEnergySensorEntityDescription(
    key="daily_heating_energy",
    translation_key="daily_heating_energy",
    name="Daily Heating Energy",
    icon="mdi:flash",
    device_class=SensorDeviceClass.ENERGY,
    state_class=SensorStateClass.TOTAL_INCREASING,
    native_unit_of_measurement="kWh",
    get_state=lambda energy: energy.heating_consumption
)
DAILY_COOLING_ENERGY_DESCRIPTION = PanasonicEnergySensorEntityDescription(
    key="daily_cooling_energy",
    translation_key="daily_cooling_energy",
    name="Daily Cooling Energy",
    icon="mdi:flash",
    device_class=SensorDeviceClass.ENERGY,
    state_class=SensorStateClass.TOTAL_INCREASING,
    native_unit_of_measurement="kWh",
    get_state=lambda energy: energy.cooling_consumption
)
POWER_DESCRIPTION = PanasonicEnergySensorEntityDescription(
    key="current_power",
    translation_key="current_power",
    name="Current Extrapolated Power",
    icon="mdi:flash",
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="W",
    get_state=lambda energy: energy.current_power
)
COOLING_POWER_DESCRIPTION = PanasonicEnergySensorEntityDescription(
    key="cooling_power",
    translation_key="cooling_power",
    name="Cooling Extrapolated Power",
    icon="mdi:flash",
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="W",
    get_state=lambda energy: energy.cooling_power
)
HEATING_POWER_DESCRIPTION = PanasonicEnergySensorEntityDescription(
    key="heating_power",
    translation_key="heating_power",
    name="Heating Extrapolated Power",
    icon="mdi:flash",
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="W",
    get_state=lambda energy: energy.heating_power
)

AQUAREA_OUTSIDE_TEMPERATURE_DESCRIPTION = AquareaSensorEntityDescription(
    key="outside_temperature",
    translation_key="outside_temperature",
    name="Outside Temperature",
    icon="mdi:thermometer",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    get_state=lambda device: device.temperature_outdoor,
    is_available=lambda device: device.temperature_outdoor is not None,
)

AQUAREA_PUMP_DUTY_DESCRIPTION = AquareaSensorEntityDescription(
    key="pump_duty",
    translation_key="pump_duty",
    name="Pump Duty",
    icon="mdi:speedometer",
    device_class=SensorDeviceClass.POWER_FACTOR,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=PERCENTAGE,
    get_state=lambda device: int(device.pump_duty),
    is_available=lambda device: True
)

AQUAREA_DIRECTION_DESCRIPTION = AquareaSensorEntityDescription(
    key="direction",
    translation_key="direction",
    name="Direction",
    icon="mdi:swap-horizontal",
    get_state=lambda device: device.current_direction.name if device.current_direction else "UNKNOWN",
    is_available=lambda device: True
)

AQUAREA_DEVICE_MODE_STATUS_DESCRIPTION = AquareaSensorEntityDescription(
    key="device_mode_status",
    translation_key="device_mode_status",
    name="Device Mode Status",
    icon="mdi:information",
    entity_category=EntityCategory.DIAGNOSTIC,
    get_state=lambda device: device.device_mode_status.name if device.device_mode_status else "UNKNOWN",
    is_available=lambda device: True
)

AQUAREA_FAULT_STATUS_DESCRIPTION = AquareaSensorEntityDescription(
    key="fault_status",
    translation_key="fault_status",
    name="Fault Status",
    icon="mdi:alert",
    entity_category=EntityCategory.DIAGNOSTIC,
    get_state=lambda device: device.current_error.error_message if device.is_on_error else "OK",
    is_available=lambda device: True
)

def create_zone_temperature_description(zone: PanasonicDeviceZone):
    return PanasonicSensorEntityDescription(
        key = f"zone-{zone.id}-temperature",
        translation_key=f"zone-{zone.id}-temperature",
        name = f"{zone.name} Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        get_state=lambda device: zone.temperature,
        is_available=lambda device: zone.has_temperature
    )


async def async_setup_entry(hass, entry, async_add_entities):
    entities = []
    data_coordinators: list[PanasonicDeviceCoordinator] = hass.data[DOMAIN][DATA_COORDINATORS]
    energy_coordinators: list[PanasonicDeviceEnergyCoordinator] = hass.data[DOMAIN][ENERGY_COORDINATORS]
    aquarea_coordinators: list[AquareaDeviceCoordinator] = hass.data[DOMAIN][AQUAREA_COORDINATORS]

    for coordinator in data_coordinators:
        entities.append(PanasonicSensorEntity(coordinator, INSIDE_TEMPERATURE_DESCRIPTION))
        entities.append(PanasonicSensorEntity(coordinator, OUTSIDE_TEMPERATURE_DESCRIPTION))
        entities.append(PanasonicSensorEntity(coordinator, LAST_UPDATE_TIME_DESCRIPTION))
        entities.append(PanasonicSensorEntity(coordinator, DATA_AGE_DESCRIPTION))
        entities.append(PanasonicSensorEntity(coordinator, DATA_MODE_DESCRIPTION))
        if coordinator.device.has_zones:
            for zone in coordinator.device.parameters.zones:
                entities.append(PanasonicSensorEntity(
                    coordinator,
                    create_zone_temperature_description(zone)))

    for coordinator in energy_coordinators:
        entities.append(PanasonicEnergySensorEntity(coordinator, DAILY_ENERGY_DESCRIPTION))
        entities.append(PanasonicEnergySensorEntity(coordinator, DAILY_COOLING_ENERGY_DESCRIPTION))
        entities.append(PanasonicEnergySensorEntity(coordinator, DAILY_HEATING_ENERGY_DESCRIPTION))
        entities.append(PanasonicEnergySensorEntity(coordinator, POWER_DESCRIPTION))
        entities.append(PanasonicEnergySensorEntity(coordinator, COOLING_POWER_DESCRIPTION))
        entities.append(PanasonicEnergySensorEntity(coordinator, HEATING_POWER_DESCRIPTION))

    for coordinator in aquarea_coordinators:
        entities.append(AquareaSensorEntity(coordinator, AQUAREA_OUTSIDE_TEMPERATURE_DESCRIPTION))
        entities.append(AquareaSensorEntity(coordinator, AQUAREA_PUMP_DUTY_DESCRIPTION))
        entities.append(AquareaSensorEntity(coordinator, AQUAREA_DIRECTION_DESCRIPTION))
        entities.append(AquareaSensorEntity(coordinator, AQUAREA_DEVICE_MODE_STATUS_DESCRIPTION))
        entities.append(AquareaSensorEntity(coordinator, AQUAREA_FAULT_STATUS_DESCRIPTION))

    async_add_entities(entities)


class PanasonicSensorEntityBase(SensorEntity):
    """Base class for all sensor entities."""
    entity_description: PanasonicSensorEntityDescription # type: ignore[override]

class PanasonicSensorEntity(PanasonicDataEntity, PanasonicSensorEntityBase):
    
    def __init__(self, coordinator: PanasonicDeviceCoordinator, description: PanasonicSensorEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if self.entity_description.is_available is None:
            return False        
        return self.entity_description.is_available(self.coordinator.device)

    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        if self.entity_description.is_available:
            self._attr_available = self.entity_description.is_available(self.coordinator.device)
        if self.entity_description.get_state:
            self._attr_native_value = self.entity_description.get_state(self.coordinator.device)

class PanasonicEnergySensorEntity(PanasonicEnergyEntity, SensorEntity):
    
    entity_description: PanasonicEnergySensorEntityDescription # type: ignore[override]

    def __init__(self, coordinator: PanasonicDeviceEnergyCoordinator, description: PanasonicEnergySensorEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available
    
    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        value = self.entity_description.get_state(self.coordinator.energy)
        self._attr_available = value is not None
        self._attr_native_value = value

class AquareaSensorEntity(AquareaDataEntity, SensorEntity):
    
    entity_description: AquareaSensorEntityDescription

    def __init__(self, coordinator: AquareaDeviceCoordinator, description: AquareaSensorEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        value = self.entity_description.is_available(self.coordinator.device) if self.entity_description.is_available else None 
        return value if value is not None else False

    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        if self.entity_description.is_available:
            self._attr_available = self.entity_description.is_available(self.coordinator.device)
        if self.entity_description.get_state:
            self._attr_native_value = self.entity_description.get_state(self.coordinator.device)