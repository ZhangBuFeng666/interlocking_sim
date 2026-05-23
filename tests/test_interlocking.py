import unittest

from interlocking_sim.interlocking import InterlockingController
from interlocking_sim.model import SignalAspect, SwitchPosition, TrackState, build_station


class InterlockingTests(unittest.TestCase):
    def setUp(self):
        self.state = build_station()
        self.ctrl = InterlockingController(self.state)

    def test_route_x_to_3g_locks_independent_switches(self):
        self.assertTrue(self.ctrl.request_route("X至3G接车"))
        self.assertTrue(self.state.routes["X至3G接车"].locked)
        self.assertTrue(self.state.switches["1"].locked)
        self.assertTrue(self.state.switches["4"].locked)
        self.assertEqual(self.state.signals["X"].aspect, SignalAspect.GREEN)
        self.assertEqual(self.state.tracks["JXG"].state, TrackState.CLEAR)
        for _ in range(4):
            self.ctrl.tick()
        self.assertEqual(self.state.tracks["JXG"].state, TrackState.OCCUPIED)

    def test_all_required_routes_exist(self):
        expected = {
            "X至3G接车", "X至IIG接车", "X至1G接车", "3G至S发车", "IIG至S发车",
            "1G至S发车", "X至S通过", "D1至1G调车", "D2至IIG调车", "安全线调车",
        }
        self.assertEqual(expected, set(self.state.routes))

    def test_conflicting_route_is_rejected(self):
        self.assertTrue(self.ctrl.request_route("X至IIG接车"))
        self.assertFalse(self.ctrl.request_route("X至S通过"))
        self.assertIn("敌对", self.state.messages[-1])

    def test_switch_single_operation_single_lock_and_block(self):
        self.assertTrue(self.ctrl.move_switch("5", SwitchPosition.REVERSE))
        self.ctrl.tick()
        self.ctrl.tick()
        self.assertEqual(self.state.switches["5"].position, SwitchPosition.REVERSE)
        self.ctrl.set_switch_lock("5", True)
        self.assertFalse(self.ctrl.move_switch("5", SwitchPosition.NORMAL))
        self.ctrl.set_switch_lock("5", False)
        self.ctrl.set_switch_block("5", True)
        self.assertFalse(self.ctrl.request_route("安全线调车"))

    def test_signal_broken_blocks_route(self):
        self.ctrl.set_signal_broken("X", True)
        self.assertFalse(self.ctrl.request_route("X至3G接车"))
        self.assertEqual(self.state.signals["X"].aspect, SignalAspect.BROKEN)
        self.assertIn("断丝", self.state.messages[-1])

    def test_track_occupied_blocks_route(self):
        self.ctrl.set_track_occupied("3G-M", True)
        self.assertFalse(self.ctrl.request_route("X至3G接车"))
        self.assertIn("3G-M占压", self.state.messages[-1])

    def test_manual_unlock_countdown(self):
        self.assertTrue(self.ctrl.request_route("X至1G接车"))
        for _ in range(4):
            self.ctrl.tick()
        self.assertFalse(self.ctrl.cancel_route("X至1G接车"))
        self.assertTrue(self.ctrl.cancel_route("X至1G接车", manual=True))
        for _ in range(5):
            self.ctrl.tick()
        self.assertFalse(self.state.routes["X至1G接车"].locked)
        self.assertFalse(self.state.switches["3"].locked)

    def test_normal_cancel_before_train_enters(self):
        self.assertTrue(self.ctrl.request_route("X至IIG接车"))
        self.assertTrue(self.ctrl.cancel_route("X至IIG接车"))
        self.assertEqual(self.state.routes["X至IIG接车"].cancel_countdown, 2)
        for _ in range(2):
            self.ctrl.tick()
        self.assertFalse(self.state.routes["X至IIG接车"].locked)
        self.assertTrue(all(t.state == TrackState.CLEAR for t in self.state.tracks.values()))

    def test_auto_unlock_refuses_occupied_then_releases_clear_route(self):
        self.assertTrue(self.ctrl.request_route("D2至IIG调车", create_train=False))
        self.ctrl.set_track_occupied("IIG-M", True)
        self.assertFalse(self.ctrl.auto_unlock())
        self.ctrl.set_track_occupied("IIG-M", False)
        self.assertTrue(self.ctrl.auto_unlock())
        self.assertFalse(self.state.routes["D2至IIG调车"].locked)

    def test_train_simulation_releases_route(self):
        self.assertTrue(self.ctrl.request_route("D1至1G调车"))
        for _ in range(11):
            self.ctrl.tick()
        self.assertFalse(self.state.routes["D1至1G调车"].locked)
        self.assertTrue(all(t.state == TrackState.CLEAR for t in self.state.tracks.values()))

    def test_routes_use_fine_grained_track_segments(self):
        self.assertIn("3G-L", self.state.routes["X至3G接车"].tracks)
        self.assertIn("3G-M", self.state.routes["X至3G接车"].tracks)
        self.assertIn("3G-R", self.state.routes["X至3G接车"].tracks)
        self.assertGreater(len(self.state.routes["X至S通过"].tracks), 8)


if __name__ == "__main__":
    unittest.main()
