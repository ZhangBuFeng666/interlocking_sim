from __future__ import annotations

from .model import SignalAspect, StationState, SwitchPosition, TrackState, Train


class InterlockingController:
    def __init__(self, state: StationState):
        self.state = state

    def request_route(self, route_name: str, create_train: bool = True) -> bool:
        route = self.state.routes[route_name]
        if route.locked:
            self.state.note(f"拒绝{route_name}: 进路已锁闭")
            return False
        sig = self.state.signals[route.signal]
        if sig.broken:
            self.state.note(f"拒绝{route_name}: 信号机{route.signal}断丝，禁止开放")
            return False
        for conflict in route.conflicting_routes:
            if self.state.routes[conflict].locked:
                self.state.note(f"拒绝{route_name}: 与{conflict}敌对")
                return False
        for track_name in route.tracks:
            if self.state.tracks[track_name].state == TrackState.OCCUPIED:
                self.state.note(f"拒绝{route_name}: {track_name}占压")
                return False
        for sw_name, required in route.switches.items():
            sw = self.state.switches[sw_name]
            if sw.blocked:
                self.state.note(f"拒绝{route_name}: 道岔{sw_name}封锁")
                return False
            if sw.single_locked and sw.position != required:
                self.state.note(f"拒绝{route_name}: 道岔{sw_name}单锁且位置不符")
                return False
            if sw.locked:
                self.state.note(f"拒绝{route_name}: 道岔{sw_name}已被进路锁闭")
                return False
        for sw_name, required in route.switches.items():
            sw = self.state.switches[sw_name]
            if sw.position != required:
                sw.target = required
                sw.position = SwitchPosition.MOVING
                sw.move_ticks = 2
                self.state.note(f"道岔{sw_name}向{required.value}转换")
        for sw_name in route.switches:
            self.state.switches[sw_name].locked = True
        route.locked = True
        route.cancel_countdown = 0
        self.state.current_route = route.name
        self._set_signal(route.signal, SignalAspect.GREEN)
        if create_train:
            train = Train(f"T{len(self.state.trains) + 1}", route.name, list(route.tracks), index=-1, dwell_ticks=3)
            route.train = train
            self.state.trains[train.name] = train
        self.state.note(f"{route.kind}进路{route_name}建立，{route.signal}开放")
        return True

    def cancel_route(self, route_name: str | None = None, manual: bool = False) -> bool:
        route = self._select_route(route_name)
        if route is None:
            self.state.note("没有可取消的当前进路")
            return False
        if not route.locked:
            self.state.note(f"进路{route.name}未锁闭")
            return False
        occupied = any(self.state.tracks[t].state == TrackState.OCCUPIED for t in route.tracks)
        if occupied and not manual:
            self.state.note(f"拒绝取消{route.name}: 进路占用，需人工解锁")
            return False
        route.cancel_countdown = 5 if manual else 2
        self._set_signal(route.signal, SignalAspect.RED)
        self.state.note(f"{route.name}开始{'人工' if manual else '正常'}解锁倒计时{route.cancel_countdown}s")
        return True

    def auto_unlock(self) -> bool:
        route = self._select_route(None)
        if route is None:
            self.state.note("没有当前进路可自动解锁")
            return False
        occupied = any(self.state.tracks[t].state == TrackState.OCCUPIED for t in route.tracks)
        if occupied:
            self.state.note(f"拒绝自动解锁{route.name}: 轨道仍占压")
            return False
        self._release_route(route.name)
        return True

    def clear_all_routes(self) -> None:
        for route in self.state.routes.values():
            if route.locked:
                self._release_route(route.name)
        self.state.note("已清除所有进路")

    def move_switch(self, switch_name: str, target: SwitchPosition) -> bool:
        sw = self.state.switches[switch_name]
        if sw.locked:
            self.state.note(f"拒绝单操{switch_name}: 道岔进路锁闭")
            return False
        if sw.single_locked:
            self.state.note(f"拒绝单操{switch_name}: 道岔单锁")
            return False
        if sw.blocked:
            self.state.note(f"拒绝单操{switch_name}: 道岔封锁")
            return False
        if any(self.state.tracks[t].state == TrackState.OCCUPIED for t in sw.related_tracks):
            self.state.note(f"拒绝单操{switch_name}: 岔区占压")
            return False
        if sw.position == target:
            self.state.note(f"道岔{switch_name}已在{target.value}")
            return True
        sw.target = target
        sw.position = SwitchPosition.MOVING
        sw.move_ticks = 2
        self.state.note(f"道岔{switch_name}向{target.value}转换")
        return True

    def set_switch_lock(self, switch_name: str, locked: bool) -> None:
        sw = self.state.switches[switch_name]
        sw.single_locked = locked
        self.state.note(f"道岔{switch_name}{'单锁' if locked else '单解'}")

    def set_switch_block(self, switch_name: str, blocked: bool) -> None:
        sw = self.state.switches[switch_name]
        sw.blocked = blocked
        self.state.note(f"道岔{switch_name}{'封锁' if blocked else '解封'}")

    def set_signal_broken(self, signal_name: str, broken: bool) -> None:
        sig = self.state.signals[signal_name]
        sig.broken = broken
        sig.aspect = SignalAspect.BROKEN if broken else SignalAspect.RED
        self.state.note(f"信号机{signal_name}{'断丝' if broken else '恢复'}")

    def set_track_occupied(self, track_name: str, occupied: bool) -> None:
        self.state.tracks[track_name].state = TrackState.OCCUPIED if occupied else TrackState.CLEAR
        self.state.note(f"轨道{track_name}{'模拟占用' if occupied else '模拟出清'}")

    def emergency_clear_track(self, track_name: str) -> None:
        self.set_track_occupied(track_name, False)

    def simulate_train_enter(self) -> None:
        self.set_track_occupied("JXG", True)

    def simulate_train_clear(self) -> None:
        for track in self.state.tracks.values():
            track.state = TrackState.CLEAR
        for train in self.state.trains.values():
            train.active = False
        self.state.note("模拟列车出清，所有轨道恢复出清")

    def reset(self) -> None:
        for route in self.state.routes.values():
            route.locked = False
            route.cancel_countdown = 0
            route.train = None
        for switch in self.state.switches.values():
            switch.position = SwitchPosition.NORMAL
            switch.target = SwitchPosition.NORMAL
            switch.locked = False
            switch.single_locked = False
            switch.blocked = False
            switch.move_ticks = 0
        for signal in self.state.signals.values():
            signal.aspect = SignalAspect.RED
            signal.broken = False
        for track in self.state.tracks.values():
            track.state = TrackState.CLEAR
        self.state.trains.clear()
        self.state.current_route = None
        self.state.note("系统已重置")

    def tick(self) -> None:
        self.state.tick_no += 1
        self._tick_switches()
        self._tick_routes()
        self._tick_trains()

    def _tick_switches(self) -> None:
        for sw in self.state.switches.values():
            if sw.position == SwitchPosition.MOVING:
                sw.move_ticks -= 1
                if sw.move_ticks <= 0:
                    sw.position = sw.target
                    self.state.note(f"道岔{sw.name}到达{sw.position.value}")

    def _tick_routes(self) -> None:
        for route in self.state.routes.values():
            if route.cancel_countdown > 0:
                route.cancel_countdown -= 1
                if route.cancel_countdown == 0:
                    self._release_route(route.name)

    def _tick_trains(self) -> None:
        for train in list(self.state.trains.values()):
            if not train.active:
                continue
            if train.dwell_ticks > 0:
                train.dwell_ticks -= 1
                continue
            current = train.current_track
            if current:
                self.state.tracks[current].state = TrackState.CLEAR
            train.index += 1
            if train.index == 0:
                self.state.note(f"列车{train.name}进入进路{train.route_name}")
            if train.index >= len(train.segments):
                train.active = False
                self.state.note(f"列车{train.name}驶出进路{train.route_name}")
                self._release_route(train.route_name)
                continue
            self.state.tracks[train.segments[train.index]].state = TrackState.OCCUPIED
            train.dwell_ticks = 1

    def is_track_occupied_group(self, group_name: str) -> bool:
        prefix = f"{group_name}-"
        return any(name == group_name or name.startswith(prefix) for name, track in self.state.tracks.items() if track.state == TrackState.OCCUPIED)

    def _select_route(self, route_name: str | None):
        if route_name:
            return self.state.routes[route_name]
        if self.state.current_route and self.state.routes[self.state.current_route].locked:
            return self.state.routes[self.state.current_route]
        for route in self.state.routes.values():
            if route.locked:
                return route
        return None

    def _release_route(self, route_name: str) -> None:
        route = self.state.routes[route_name]
        route.locked = False
        route.cancel_countdown = 0
        for sw_name in route.switches:
            self.state.switches[sw_name].locked = False
        self._set_signal(route.signal, SignalAspect.RED)
        if route.train:
            route.train.active = False
        route.train = None
        if self.state.current_route == route_name:
            self.state.current_route = None
        self.state.note(f"进路{route_name}解锁，信号关闭")

    def _set_signal(self, signal_name: str, aspect: SignalAspect) -> None:
        sig = self.state.signals[signal_name]
        sig.aspect = SignalAspect.BROKEN if sig.broken else aspect
