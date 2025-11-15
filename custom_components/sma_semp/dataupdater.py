"""DataUpdater"""

import logging
import typing
from dataclasses import dataclass
from datetime import datetime, timedelta
from logging import Logger

from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import parse_yaml
from homeassistant.exceptions import HomeAssistantError
from pysmaplus.semp.const import callbackAction
from pysmaplus.semp.device import sempTimeframe, sempDevice

from .const import MY_KEY, SempDeviceInfo
from .helper import switchOnOff

_LOGGER = logging.getLogger(__name__)


@dataclass
class timeframeStatus:
    """Structur for timeframeStatus"""

    active: bool = False
    currentTimeframe: str = ""
    activeCounter: int = 0
    currentTime: datetime | None = None


async def getCalender(hass: HomeAssistant, calendarname: str):
    """Return the entries from the calendar entitiy"""
    a = await hass.services.async_call(
        "calendar",
        "get_events",
        service_data={
            "entity_id": calendarname,
            "duration": "24:00",
        },
        blocking=True,
        return_response=True,
    )
    return a


class sempCoordinator(DataUpdateCoordinator):
    """Coordinator helper to handle Elmax API polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        name: str,
        update_interval: timedelta,
        # sempCoordinator(hass, _LOGGER, "smasemp", interval)
    ) -> None:
        """Instantiate the object."""
        self.hass = hass
        self.timezone = dt_util.get_default_time_zone()
        # self._client = elmax_api_client
        # self._panel_entry = panel
        # self._state_by_endpoint = None
        super().__init__(
            hass=hass, logger=logger, name=name, update_interval=update_interval
        )

    def _getStatus(self, device, cfg) -> tuple[str, int]:
        """Get the Status for this device"""
        status = "unknown"
        value = 0
        if device is None:
            return status, value
        # Status based on power usage
        sensor = self.hass.states.get(cfg.source)
        if sensor is None or sensor.state == "unavailable":
            value = 0
            status = "offline"
        elif sensor.state == "unknown":
            value = 0
            status = "offline"
        else:
            value = int(float(sensor.state))
            if sensor.attributes.get(ATTR_UNIT_OF_MEASUREMENT, "") == "kW":
                value = int(float(sensor.state) * 1000)
            status = "on"
            if value < 10:
                status = "off"

        # Based on onoffswitch
        if cfg.onoffswitch is not None:
            sensor = self.hass.states.get(cfg.onoffswitch)
            if sensor is None:
                # TODO Startup
                _LOGGER.error(f"Sensor {cfg.onoffswitch} return None!")
            else:
                if sensor.state == "unavailable":
                    status = "offline"
                else:
                    if sensor.state in ["on", "off"]:
                        status = sensor.state
                    else:
                        _LOGGER.warning("Unknown Status: " + sensor.state)
        return status, value

    async def _async_update_data(self):
        data = self.hass.data[MY_KEY]
        now = datetime.now(tz=self.timezone)
        sempstatus = data.sempserver.getStatus()

        for dev in data.sendata.values():
            dev = typing.cast(SempDeviceInfo, dev)
            await self._handleDevice(dev, sempstatus, now)

    async def _handleDevice(self, dev: SempDeviceInfo, sempstatus: str, now: datetime):
        """ """
        cfg = dev.configdata
        (
            timeframes,
            withInTimeFrame,
            controllable,
            interruptable,
        ) = await self._getTimeFrameInformation(dev, now, cfg)
        dev.timeframes = timeframes
        status, powerUsage = self._getStatus(dev.device, cfg)
        timeframestatus = None

        if dev.sensors_status:
            last_data = dev.sensors_status.extra_state_attributes
            timeframestatus = typing.cast(
                timeframeStatus, last_data.get("currentTimeframe", timeframeStatus())
            )

        if timeframestatus is None:
            timeframestatus = timeframeStatus()

        if dev.sensors_status and controllable:
            # in timeframe	sametimeframe	device
            # true	        true	        on	        addiere Zeit
            # true	        true	        of	        0
            # true	        false       	on      	reset Zeit
            # true	        false       	of      	reset Zeit
            # false	        true	        on	        nicht möglich
            # false	        true	        of	        nicht möglich
            # false	        false       	on      	reset Zeit
            # false	        false       	of      	reset Zeit

            sameTimeFrame = False
            timeframeId = ""
            if withInTimeFrame is not None:
                timeframeId = (
                    str(withInTimeFrame.start) + "/" + str(withInTimeFrame.stop)
                )
                sameTimeFrame = timeframeId == timeframestatus.currentTimeframe
            if not sameTimeFrame:
                # Outside of timeframe, reset counter
                if timeframestatus is not None:
                    timeframestatus.activeCounter = 0
                if status == "on":
                    await switchOnOff(self.hass, dev.configdata.onoffswitch, False)
                    dev.history.append(
                        {
                            "time": datetime.now().isoformat()[0:19],
                            "event": "turn off (end of timeframe)",
                        }
                    )
            else:
                if status == "on":
                    timeframestatus.activeCounter += 5  # TODO
                elif status == "off":
                    pass
                else:
                    _LOGGER.warning(f"Unknown status {status}")
                if timeframestatus.activeCounter > 0:
                    withInTimeFrame.minRunningTime = max(
                        0,
                        withInTimeFrame.minRunningTime - timeframestatus.activeCounter,
                    )
                    withInTimeFrame.maxRunningTime = max(
                        0,
                        withInTimeFrame.maxRunningTime - timeframestatus.activeCounter,
                    )
                    if status == "on" and withInTimeFrame.maxRunningTime == 0:
                            await switchOnOff(self.hass, dev.configdata.onoffswitch, False)
                            dev.history.append(
                                {
                                    "time": datetime.now().isoformat()[0:19],
                                    "event": "turn off (end of maxRunningTime)",
                                }
                            )
            timeframestatus.currentTimeframe = timeframeId
            timeframestatus.currentTime = now
            _LOGGER.debug(
                f"Device: {cfg.name} Status: {status} sameTimeFrame {sameTimeFrame} withInTimeFrame {withInTimeFrame} Counter {timeframestatus.activeCounter}"
            )

        if dev.device:
            #            _LOGGER.error(f"Status {status}")
            dev.device.setPowerStatus(powerUsage, status)
            dev.device.setTimeframes(dev.timeframes)
            dev.device.setInterruptable(interruptable)

        if dev.sensors_status:
            # dev.timeframes
            # status
            # sempstatus
            # timeframestatus
            # withintimeframe

            aattr: dict[str, typing.Any] = {}
            aattr["timeframes"] = []
            for tf in dev.timeframes:
                aattr["timeframes"].append(
                    {
                        "start": tf.start,
                        "stop": tf.stop,
                        "minRunningTime": tf.minRunningTime,
                        "maxRunningTime": tf.maxRunningTime,
                    }
                )
                # aattr["timeframes"].append(asdict(tf))

            errorStatus = []
            if status in ["unknown", "offline"]:
                errorStatus.append("Entity: " + status)

            if sempstatus in ["Connection lost", "Not Connected"]:
                errorStatus.append("SEMP: " + sempstatus)

            if len(errorStatus) == 0:
                if controllable:
                    minRunning = timeframestatus.activeCounter // 60
                    if status == "on":
                        val = f"Running ({minRunning} min)"
                    else:
                        if withInTimeFrame is not None:
                            val = f"Waiting for next slot in this timeframe ({minRunning} min)"
                        else:
                            val = "Waiting for next timeframe"
                else:
                    val = "Reporting"
            else:
                val = ",".join(errorStatus)

            aattr["currentTimeframe"] = timeframestatus
            aattr["sempstatus"] = sempstatus
            aattr["entitystatus"] = status
            if len(dev.history) > 20:
                dev.history = dev.history[-20:]

            aattr["history"] = dev.history
            aattr["name"] = dev.configdata.name
            dev.sensors_status.set_value(val, aattr)

    def getValuesFromDescription(self, e):
        """Get additional Values from the Description Field of the Calendar Entry"""
        values = {}
        if "description" in e and (desc := e["description"]) != "":
            try:
                values = parse_yaml(desc)
#                _LOGGER.error(values)
            except HomeAssistantError as exc:
                print("ERROR", exc)
        return values

    async def _getTimeFrameInformation(
        self, dev, now, cfg
    ) -> tuple[list[sempTimeframe], sempTimeframe | None, bool, bool]:
        timeframes: list[sempTimeframe] = []
        interruptable = False
        withInTimeFrame = None
        controllable = False
        if (
            cfg.controllable
            and dev.switch_controllable is not None
            and dev.switch_controllable.is_on
        ):
            controllable = True
            name = cfg.name.lower()
            tf = await getCalender(self.hass, cfg.calendar)
            for c in tf.values():
                for e in c["events"]:
                    if e["summary"].lower() != name:
                        continue
                    values = self.getValuesFromDescription(e)
                    mintr = (
                        timedelta(**cfg.minrunningtime)
                        if "MinRunningTime" not in values
                        else timedelta(seconds=values["MinRunningTime"])
                    )
                    maxtr = (
                        timedelta(**cfg.maxrunningtime)
                        if "MaxRunningTime" not in values
                        else timedelta(seconds=values["MaxRunningTime"])
                    )
                    s = datetime.fromisoformat(e["start"])
                    e = datetime.fromisoformat(e["end"])
                    
                    # Ensure timezone consistency for comparison
                    if s.tzinfo is None:
                        s = s.replace(tzinfo=now.tzinfo)
                    if e.tzinfo is None:
                        e = e.replace(tzinfo=now.tzinfo)
                    
                    t = sempTimeframe(s, e, mintr, maxtr)
                    timeframes.append(t)
                    if s <= now <= e:
                        withInTimeFrame = t
            interruptable = (
                cfg.interruptable
                and dev.switch_interruptable is not None
                and dev.switch_interruptable.is_on
            )

        return timeframes, withInTimeFrame, controllable, interruptable

    async def sempcallback(self, d: callbackAction) -> None:
        """Callback from the pysma-plus-Library"""
        data = self.hass.data[MY_KEY]
        if d.shortdeviceid not in data.sendata:
            _LOGGER.warning(f"Unknnown device {d.deviceid} {d.shortdeviceid}")
            return

        sendata = data.sendata[d.shortdeviceid]
        if sendata.configdata.onoffswitch is None:
            _LOGGER.warning(
                f"No onoff switch for device {d.deviceid} {d.shortdeviceid}"
            )
            return

        if (
            sendata.switch_controllable is not None
            and not sendata.switch_controllable.is_on
        ):
            _LOGGER.warning(
                f"Controllable is off for devices {d.deviceid} {d.shortdeviceid}"
            )
            return
        status = "on" if d.requestedStatus else "off"

        now = datetime.now(tz=self.timezone)

        withInTimeFrame = False
        for tf in sendata.timeframes:
            if tf.start < now < tf.stop:
                withInTimeFrame = True

        if not withInTimeFrame and status == "off":
            sendata.history.append(
                {
                    "time": datetime.now().isoformat()[0:19],
                    "event": "reject turn " + status + " (outside timeframe)",
                }
            )
            return
        sendata.history.append(
            {"time": datetime.now().isoformat()[0:19], "event": "turn " + status}
        )

        await self.hass.services.async_call(
            "homeassistant",
            "turn_" + status,
            service_data={
                "entity_id": sendata.configdata.onoffswitch,
                #                "duration": "24:00",
            },
            blocking=True,
        )
