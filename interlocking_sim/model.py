from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SwitchPosition(str, Enum):
    NORMAL = "定位"
    REVERSE = "反位"
    MOVING = "转换中"


class SignalAspect(str, Enum):
    RED = "关闭"
    GREEN = "开放"
    BROKEN = "断丝"


class TrackState(str, Enum):
    CLEAR = "出清"
    OCCUPIED = "占压"


@dataclass
class Switch:
    name: str
    related_tracks: List[str]
    position: SwitchPosition = SwitchPosition.NORMAL
    target: SwitchPosition = SwitchPosition.NORMAL
    locked: bool = False
    single_locked: bool = False
    blocked: bool = False
    move_ticks: int = 0


@dataclass
class Signal:
    name: str
    aspect: SignalAspect = SignalAspect.RED
    broken: bool = False


@dataclass
class TrackCircuit:
    name: str
    state: TrackState = TrackState.CLEAR


@dataclass
class Train:
    name: str
    route_name: str
    segments: List[str]
    index: int = 0
    dwell_ticks: int = 0
    active: bool = True

    @property
    def current_track(self) -> Optional[str]:
        if not self.active or self.index >= len(self.segments):
            return None
        return self.segments[self.index]


@dataclass
class Route:
    name: str
    kind: str
    signal: str
    tracks: List[str]
    switches: Dict[str, SwitchPosition]
    conflicting_routes: List[str]
    locked: bool = False
    cancel_countdown: int = 0
    train: Optional[Train] = None


@dataclass
class StationState:
    switches: Dict[str, Switch]
    signals: Dict[str, Signal]
    tracks: Dict[str, TrackCircuit]
    routes: Dict[str, Route]
    trains: Dict[str, Train] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)
    tick_no: int = 0
    current_route: Optional[str] = None

    def note(self, message: str) -> None:
        self.messages.append(message)
        self.messages[:] = self.messages[-10:]


def build_station() -> StationState:
    tracks = {name: TrackCircuit(name) for name in [
        "JXG", "IIAG-A", "IIAG-B",
        "3G-L", "3G-M", "3G-R",
        "IIG-L", "IIG-M", "IIG-R",
        "1G-L", "1G-M", "1G-R", "1G-RT",
        "右咽喉", "IIBG-A", "IIBG-B", "JSG",
        "安全线-A", "安全线-B",
    ]}
    switches = {
        "1": Switch("1", related_tracks=["IIAG-B", "3G-L", "IIG-L"]),
        "3": Switch("3", related_tracks=["IIAG-B", "IIG-L", "1G-L"]),
        "5": Switch("5", related_tracks=["1G-M", "安全线-A", "安全线-B"]),
        "4": Switch("4", related_tracks=["3G-R", "IIG-R", "右咽喉"]),
        "2": Switch("2", related_tracks=["1G-RT", "右咽喉", "IIBG-A"]),
    }
    signals = {name: Signal(name) for name in [
        "X", "D1", "S3", "SII", "S1", "X3", "XII", "X1", "D2", "S", "PZA"
    ]}
    routes = {
        "X至3G接车": Route("X至3G接车", "列车", "X", ["JXG", "IIAG-A", "IIAG-B", "3G-L", "3G-M", "3G-R"], {"1": SwitchPosition.REVERSE, "4": SwitchPosition.REVERSE}, []),
        "X至IIG接车": Route("X至IIG接车", "列车", "X", ["JXG", "IIAG-A", "IIAG-B", "IIG-L", "IIG-M", "IIG-R"], {"1": SwitchPosition.NORMAL, "3": SwitchPosition.NORMAL, "4": SwitchPosition.NORMAL}, []),
        "X至1G接车": Route("X至1G接车", "列车", "X", ["JXG", "IIAG-A", "IIAG-B", "1G-L", "1G-M", "1G-R", "1G-RT"], {"3": SwitchPosition.REVERSE, "2": SwitchPosition.REVERSE}, []),
        "3G至S发车": Route("3G至S发车", "列车", "S3", ["3G-M", "3G-R", "右咽喉", "IIBG-A", "IIBG-B", "JSG"], {"4": SwitchPosition.REVERSE}, []),
        "IIG至S发车": Route("IIG至S发车", "列车", "SII", ["IIG-M", "IIG-R", "右咽喉", "IIBG-A", "IIBG-B", "JSG"], {"4": SwitchPosition.NORMAL, "2": SwitchPosition.NORMAL}, []),
        "1G至S发车": Route("1G至S发车", "列车", "S1", ["1G-M", "1G-R", "1G-RT", "IIBG-A", "IIBG-B", "JSG"], {"2": SwitchPosition.REVERSE}, []),
        "X至S通过": Route("X至S通过", "列车", "X", ["JXG", "IIAG-A", "IIAG-B", "IIG-L", "IIG-M", "IIG-R", "右咽喉", "IIBG-A", "IIBG-B", "JSG"], {"1": SwitchPosition.NORMAL, "3": SwitchPosition.NORMAL, "4": SwitchPosition.NORMAL, "2": SwitchPosition.NORMAL}, []),
        "D1至1G调车": Route("D1至1G调车", "调车", "D1", ["IIAG-B", "1G-L", "1G-M"], {"3": SwitchPosition.REVERSE}, []),
        "D2至IIG调车": Route("D2至IIG调车", "调车", "D2", ["IIBG-A", "右咽喉", "IIG-R", "IIG-M"], {"4": SwitchPosition.NORMAL}, []),
        "安全线调车": Route("安全线调车", "调车", "PZA", ["安全线-A", "安全线-B", "1G-M"], {"5": SwitchPosition.REVERSE}, []),
    }
    route_names = list(routes)
    for route in routes.values():
        route.conflicting_routes = [name for name in route_names if name != route.name and _routes_conflict(route, routes[name])]
    return StationState(switches=switches, signals=signals, tracks=tracks, routes=routes)


def _routes_conflict(left: Route, right: Route) -> bool:
    if set(left.tracks) & set(right.tracks):
        return True
    if set(left.switches) & set(right.switches):
        return True
    if left.signal == right.signal:
        return True
    return False
