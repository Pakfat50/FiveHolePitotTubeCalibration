"""AoA/AoSを実機構のZ/A角へ変換する。"""

import math

from models import AxisLimits


class AngleTransformer:
    """要求された流れ角を実ピッチ／実ロール指令へ変換する。

    機構はピッチ回転後にピトー管軸周りのロール回転を行うものとして扱う。
    等価解は可動範囲と前較正点からの連続性を考慮して選択する。

    対応要求:
        REQ-TRANS-001, REQ-TRANS-002, REQ-TRANS-003, REQ-TRANS-004
    """

    # 対応要求: REQ-TRANS-001, REQ-TRANS-002, REQ-TRANS-003, REQ-TRANS-004
    def transform(self, aoa: float, aos: float, previous: tuple[float, float] | None, limits: AxisLimits) -> tuple[float, float]:
        """1つのAoA/AoS点から実ピッチZと実ロールAを算出する。

        引数:
            aoa: 要求AoA [deg]。
            aos: 要求AoS [deg]。
            previous: 前回選択した``(z, a)``指令。先頭点ではNone。
            limits: 軸可動範囲。

        戻り値:
            等価解の中から可動範囲と連続性を考慮して選択した``(z, a)``角度 [deg]。

        対応要求:
            REQ-TRANS-001, REQ-TRANS-002, REQ-TRANS-003, REQ-TRANS-004
        """
        # AoA/AoSは度で入力されるため、tanを計算する前にラジアンへ変換する。
        # u, vは要求流れ方向をX軸に対する傾きとして表す無次元量である。
        u = math.tan(math.radians(aoa))
        v = math.tan(math.radians(aos))

        # u-v平面での傾きの大きさrからピッチ角thetaを求める。
        r = math.hypot(u, v)
        theta = math.degrees(math.atan(r))

        # AoA=AoS=0ではロール方向は数学的に不定となる。
        # ここで前点からの連続性を適用すると、走査途中の原点がA=±180 deg等の
        # 等価解へ変化し得るため、仕様どおり原点だけは常に(Z,A)=(0,0)とする。
        if r == 0.0:
            return 0.0, 0.0

        # ロール角phiは傾きベクトル(u, v)の方向である。
        phi = math.degrees(math.atan2(v, u))
        candidates = self._generate_equivalent_solutions(theta, phi)

        # AoA=0の行では、走査途中に決定論的原点A=0が現れる可能性がある。
        # 実A範囲内に±180 deg以内の等価解が存在する場合は、その正規化候補の中から
        # 前点に最も近いものを選ぶ。これにより、原点直前でA=-270 deg等を選択して
        # 原点への不要な270 degジャンプを発生させることを防ぐ。
        if u == 0.0:
            canonical = [
                (z, a)
                for z, a in candidates
                if -180.0 <= a <= 180.0
                and limits.z.minimum <= z <= limits.z.maximum
                and limits.a.minimum <= a <= limits.a.maximum
            ]
            if canonical:
                return self._select_without_unwrap(canonical, previous)

        return self._select_solution(candidates, previous, limits)

    # 対応要求: REQ-TRANS-002
    def _generate_equivalent_solutions(self, theta: float, phi: float) -> list[tuple[float, float]]:
        """同一の流れ姿勢を表す機構角度の候補解を生成する。"""
        return [
            (theta, phi),
            (-theta, phi + 180.0),
            (-theta, phi - 180.0),
        ]

    # 対応要求: REQ-TRANS-003, REQ-TRANS-004
    def _select_solution(self, candidates: list[tuple[float, float]], previous: tuple[float, float] | None, limits: AxisLimits) -> tuple[float, float]:
        """可動範囲、連続性、移動量、|roll|の優先順位で候補を選択する。"""
        if not candidates:
            raise ValueError("角度候補がありません。")

        expanded: list[tuple[float, float, int]] = []
        for order, (z, a) in enumerate(candidates):
            a_values = [a + 360.0 * k for k in range(-2, 3)]
            if previous is not None:
                a_values.append(self._unwrap_angle(a, previous[1]))

            seen: set[float] = set()
            for candidate_a in a_values:
                key = round(candidate_a, 12)
                if key in seen:
                    continue
                seen.add(key)
                expanded.append((z, candidate_a, order))

        def score(item: tuple[float, float, int]) -> tuple[float, ...]:
            z, a, order = item
            in_range = limits.z.minimum <= z <= limits.z.maximum and limits.a.minimum <= a <= limits.a.maximum
            range_rank = 0.0 if in_range else 1.0

            if previous is None:
                return (range_rank, float(order), abs(a))

            dz = abs(z - previous[0])
            da = abs(a - previous[1])
            total_motion = dz + da
            return (range_rank, total_motion, abs(a), float(order))

        selected = min(expanded, key=score)
        return selected[0], selected[1]

    def _select_without_unwrap(self, candidates: list[tuple[float, float]], previous: tuple[float, float] | None) -> tuple[float, float]:
        """正規化済み等価解を±360展開せずに選択する。

        対応要求:
            REQ-TRANS-003, REQ-TRANS-004
        """
        if previous is None:
            return min(enumerate(candidates), key=lambda item: (item[0], abs(item[1][1])))[1]
        return min(
            candidates,
            key=lambda item: (
                abs(item[0] - previous[0]) + abs(item[1] - previous[1]),
                abs(item[1]),
            ),
        )

    # 対応要求: REQ-TRANS-004
    def _unwrap_angle(self, angle: float, previous: float | None) -> float:
        """前回ロール角に最も近い等価角へunwrapする。"""
        if previous is None:
            return angle

        center = int(round((previous - angle) / 360.0))
        equivalents = [angle + 360.0 * k for k in (center - 1, center, center + 1)]
        return min(equivalents, key=lambda value: abs(value - previous))
