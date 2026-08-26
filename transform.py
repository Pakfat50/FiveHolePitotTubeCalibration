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

        # ロール角phiは傾きベクトル(u, v)の方向である。
        # 原点ではPythonのatan2(0, 0)=0を利用し、(z, a)=(0, 0)を決定論的に返す。
        phi = math.degrees(math.atan2(v, u))

        candidates = self._generate_equivalent_solutions(theta, phi)
        return self._select_solution(candidates, previous, limits)

    # 対応要求: REQ-TRANS-002
    def _generate_equivalent_solutions(self, theta: float, phi: float) -> list[tuple[float, float]]:
        """同一の流れ姿勢を表す機構角度の候補解を生成する。

        引数:
            theta: 基本ピッチ解 [deg]。
            phi: 基本ロール解 [deg]。

        戻り値:
            等価な``(z, a)``候補解。

        対応要求:
            REQ-TRANS-002
        """
        # tan(-theta)=-tan(theta)であり、同時にrollを180 deg反転すると
        # cos/sinの符号も反転するため、結果のu,vは元の基本解と同一になる。
        # +180と-180は同一姿勢の異なる角度表現なので両方を候補に残し、
        # 後段で可動範囲・連続性に最も適したものを選択する。
        return [
            (theta, phi),
            (-theta, phi + 180.0),
            (-theta, phi - 180.0),
        ]

    # 対応要求: REQ-TRANS-003, REQ-TRANS-004
    def _select_solution(self, candidates: list[tuple[float, float]], previous: tuple[float, float] | None, limits: AxisLimits) -> tuple[float, float]:
        """可動範囲、連続性、移動量、|roll|の優先順位で候補を選択する。

        引数:
            candidates: 等価な角度候補。
            previous: 前回選択した指令。先頭点ではNone。
            limits: 許容Z/A範囲。

        戻り値:
            選択した``(z, a)``候補。

        対応要求:
            REQ-TRANS-003, REQ-TRANS-004
        """
        if not candidates:
            raise ValueError("角度候補がありません。")

        expanded: list[tuple[float, float, int]] = []
        for order, (z, a) in enumerate(candidates):
            # rollは360 deg周期なので、可動範囲内に入り得る代表的な等価角も評価する。
            # 前点がある場合は、まず前点に最も近いunwrap値を候補へ追加する。
            a_values = [a + 360.0 * k for k in range(-2, 3)]
            if previous is not None:
                a_values.append(self._unwrap_angle(a, previous[1]))

            seen: set[float] = set()
            for candidate_a in a_values:
                # 浮動小数の同一値重複を避けるため丸め値をキーにする。
                key = round(candidate_a, 12)
                if key in seen:
                    continue
                seen.add(key)
                expanded.append((z, candidate_a, order))

        def score(item: tuple[float, float, int]) -> tuple[float, ...]:
            z, a, order = item
            in_range = limits.z.minimum <= z <= limits.z.maximum and limits.a.minimum <= a <= limits.a.maximum

            # 優先順位1: Z/Aが可動範囲内の候補を最優先する。
            range_rank = 0.0 if in_range else 1.0

            if previous is None:
                # 先頭点では連続性・移動量を評価できないため、仕様の最終優先順位である
                # |roll|を小さくする。完全同点では元の候補順を維持して決定論的にする。
                return (range_rank, abs(a), float(order))

            # 優先順位2/3: unwrap済みの候補について、前点からの角度変化を最小化する。
            # Z/A総移動量をL1距離で評価することで、両軸の不要な移動を抑える。
            dz = abs(z - previous[0])
            da = abs(a - previous[1])
            total_motion = dz + da

            # 優先順位4: 総移動量まで同一の場合は|roll|が小さい候補を選ぶ。
            return (range_rank, total_motion, abs(a), float(order))

        selected = min(expanded, key=score)
        return selected[0], selected[1]

    # 対応要求: REQ-TRANS-004
    def _unwrap_angle(self, angle: float, previous: float | None) -> float:
        """前回ロール角に最も近い等価角へunwrapする。

        引数:
            angle: 現在のロール角 [deg]。
            previous: 前回ロール角 [deg]。先頭点ではNone。

        戻り値:
            不要な±360 degジャンプを避けた等価角。

        対応要求:
            REQ-TRANS-004
        """
        if previous is None:
            return angle

        # angle + 360*k のうちpreviousとの差が最小となる整数kを選ぶ。
        # roundだけでは厳密な0.5で偶数丸めになるため、近傍3候補を直接比較して
        # 境界条件でも「前点に最も近い」という物理的な意味を優先する。
        center = int(round((previous - angle) / 360.0))
        equivalents = [angle + 360.0 * k for k in (center - 1, center, center + 1)]
        return min(equivalents, key=lambda value: abs(value - previous))
