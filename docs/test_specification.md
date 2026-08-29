# 5孔ピトー管較正Gコード生成GUI テスト仕様書

## 1. 目的

本書は、`docs/pitot_calibration_gui_spec.md` および `docs/architecture_design.md` に基づくテスト設計と、実装済みテストのトレーサビリティを定義する。

本書では以下を管理する。

- 単体テスト仕様
- 要求仕様ID ↔ 単体テストID トレーサビリティ
- モジュール/メソッド ↔ 単体テストID 対応
- 各ユースケースに対応するユースケーステスト（組み合わせテスト）仕様
- ユースケースID ↔ ユースケーステストID トレーサビリティ

既存の要求IDおよびユースケースIDは変更しない。

---

## 2. テストID規則

### 2.1 単体テスト

単体テストIDは `TEST-UNIT-NNN` とする。

各単体テストは1件以上の `REQ-...` 要求IDへトレースする。

### 2.2 ユースケーステスト

ユースケーステストIDは `TEST-UC-XX-NN` とする。

- `XX`：対象ユースケース番号
- `NN`：ユースケース内のテスト連番

ユースケーステストは要求IDではなく、アーキテクチャで定義した `UC-01` ～ `UC-06` へトレースする。

---

## 3. 共通テスト方針

1. 単体テストフレームワークはPython標準ライブラリ `unittest` を使用する。
2. 数値計算結果の比較は要求仕様に従い、理論値に対する**絶対誤差0.001以内**を合格基準とする。角度はdeg、位置はmmを単位とする。
3. Core層はGUIを起動せずに試験する。
4. ファイルI/Oは `tempfile` を用いて一時ファイル・一時ディレクトリ上で試験する。
5. GUI層の単体テストでは計算ロジックを再試験せず、イベント伝播、入力欄の背景色による強調、既存固定メッセージ領域への理由表示、状態表示、ボタン有効/無効、非モーダル通知を中心に確認する。
6. シミュレーションでは実時間10秒を毎回待つ試験は避け、フレーム位置計算や描画呼出しを分離して検証する。ユースケーステストでは必要に応じ再生時間設定を短縮可能なテスト用構成とする。
7. Gコード数値は小数点以下6桁で出力する。Gコード生成テストでは文字列全体一致または行単位一致を使用し、G番号のゼロ埋め、X/Y/Z/A/F/Pの6桁表記、保持時間、コメント有無、終了時復帰命令なしを確認する。
8. 入力中の一時的な不正値は例外やモーダルダイアログを発生させないことを確認する。
9. X/Y可動範囲超過は警告、Z/A可動範囲超過は生成禁止エラーとして明確に区別する。
10. `CalibrationPlan` が較正点マップ、シミュレーション、Gコード生成の共通データ源であることを組み合わせテストで確認する。
11. 設定ファイルはCSV形式とし、スキーマバージョン番号は持たない。
12. CSV設定読込では、必須値欠損、空欄、数値変換不能、構造不正、ファイルI/O失敗等が発生しても未処理例外でアプリケーションを終了させない。
13. CSV設定読込に失敗した場合は、読み込み途中の値を部分適用せず、読込前の設定および `CalibrationPlan` を維持し、ユーザーへ非モーダルにエラーを通知する。

---

# 4. 単体テスト仕様

## 4.1 `validation.py` — `InputValidator.validate`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-001"></a>TEST-UNIT-001 | REQ-VALID-001, REQ-VALID-002 | 正常な設定値の検証 | 全項目が有効 | `is_valid=True`、ERRORなし | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_valid_settings]] |
| <a id="test-unit-002"></a>TEST-UNIT-002 | REQ-INPUT-001, REQ-VALID-002 | AoA最小値=最大値 | `aoa_min == aoa_max` | AoA範囲エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_aoa_min_equal_max]] |
| <a id="test-unit-003"></a>TEST-UNIT-003 | REQ-INPUT-001, REQ-VALID-002 | AoA最小値>最大値 | `aoa_min > aoa_max` | AoA範囲エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_aoa_min_greater_than_max]] |
| <a id="test-unit-004"></a>TEST-UNIT-004 | REQ-INPUT-001, REQ-VALID-002 | AoS最小値=最大値 | `aos_min == aos_max` | AoS範囲エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_aos_min_equal_max]] |
| <a id="test-unit-005"></a>TEST-UNIT-005 | REQ-INPUT-001, REQ-VALID-002 | AoS最小値>最大値 | `aos_min > aos_max` | AoS範囲エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_aos_min_greater_than_max]] |
| <a id="test-unit-006"></a>TEST-UNIT-006 | REQ-INPUT-002, REQ-VALID-002 | AoA点数の下限正常 | `aoa_points=2` | 点数エラーなし | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_aoa_points_minimum_valid]] |
| <a id="test-unit-007"></a>TEST-UNIT-007 | REQ-INPUT-002, REQ-VALID-002 | AoA点数不足 | `aoa_points=1` | 点数エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_aoa_points_too_small]] |
| <a id="test-unit-008"></a>TEST-UNIT-008 | REQ-INPUT-002, REQ-VALID-002 | AoS点数不足 | `aos_points=1` | 点数エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_aos_points_too_small]] |
| <a id="test-unit-009"></a>TEST-UNIT-009 | REQ-INPUT-004, REQ-VALID-002 | Feed rate不正 | `feed_rate < 1` または非有限値 | Feed rateエラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_feed_rate_invalid]] |
| <a id="test-unit-010"></a>TEST-UNIT-010 | REQ-INPUT-004, REQ-VALID-002 | 保持時間不正 | `hold_time_s < 0.1` または非有限値 | 保持時間エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_hold_time_invalid]] |
| <a id="test-unit-011"></a>TEST-UNIT-011 | REQ-INPUT-003, REQ-VALID-002 | 距離が非有限値 | LxまたはLyがNaN/Inf | 距離エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_distance_non_finite]] |
| <a id="test-unit-012"></a>TEST-UNIT-012 | REQ-INPUT-005, REQ-VALID-002 | X軸最小=最大 | X range min=max | X可動範囲エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_x_range_equal]] |
| <a id="test-unit-013"></a>TEST-UNIT-013 | REQ-INPUT-005, REQ-VALID-002 | Y軸最小>最大 | Y range min>max | Y可動範囲エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_y_range_reversed]] |
| <a id="test-unit-014"></a>TEST-UNIT-014 | REQ-INPUT-005, REQ-VALID-002 | Z軸最小>=最大 | Z range不正 | Z可動範囲エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_z_range_invalid]] |
| <a id="test-unit-015"></a>TEST-UNIT-015 | REQ-INPUT-005, REQ-VALID-002 | A軸最小>=最大 | A range不正 | A可動範囲エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_a_range_invalid]] |
| <a id="test-unit-016"></a>TEST-UNIT-016 | REQ-VALID-001 | 複数エラー同時検出 | AoA範囲、点数、Feed等を同時不正 | 複数の`ValidationIssue`を返す | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_multiple_errors_are_reported]] |
| <a id="test-unit-111"></a>TEST-UNIT-111 | REQ-INPUT-003, REQ-VALID-002 | Lx下限違反 | `Lx=0` | 距離エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_lx_zero_is_invalid]] |
| <a id="test-unit-112"></a>TEST-UNIT-112 | REQ-INPUT-003, REQ-VALID-002 | Ly負値 | `Ly<0` | 距離エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_ly_negative_is_invalid]] |
| <a id="test-unit-113"></a>TEST-UNIT-113 | REQ-INPUT-004, REQ-VALID-002 | 保持時間下限正常 | `hold_time_s=0.1` | 保持時間エラーなし | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_hold_time_minimum_is_valid]] |
| <a id="test-unit-114"></a>TEST-UNIT-114 | REQ-INPUT-004, REQ-VALID-002 | 保持時間下限未満 | `0 <= hold_time_s < 0.1` | 保持時間エラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_hold_time_below_minimum_is_invalid]] |
| <a id="test-unit-115"></a>TEST-UNIT-115 | REQ-INPUT-004, REQ-VALID-002 | Feed rate下限正常 | `feed_rate=1` | Feed rateエラーなし | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_feed_rate_minimum_is_valid]] |
| <a id="test-unit-116"></a>TEST-UNIT-116 | REQ-INPUT-004, REQ-VALID-002 | Feed rate下限未満 | `feed_rate<1` | Feed rateエラー | [[TESTCODE_SHORT:tests.test_validation.TestInputValidator.test_feed_rate_below_minimum_is_invalid]] |

## 4.2 `scan.py` — `ScanPlanner.generate_points`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-017"></a>TEST-UNIT-017 | REQ-SCAN-001 | 2×2最小グリッド | AoA/AoS各2点 | 4点、全端点を含む | [[TESTCODE_SHORT:tests.test_scan.TestScanPlanner.test_minimum_grid_has_four_endpoints]] |
| <a id="test-unit-018"></a>TEST-UNIT-018 | REQ-SCAN-001 | 等間隔生成 | AoA=-10..10, 5点 | -10,-5,0,5,10 | [[TESTCODE_SHORT:tests.test_scan.TestScanPlanner.test_aoa_equal_spacing]] |
| <a id="test-unit-019"></a>TEST-UNIT-019 | REQ-SCAN-001 | AoS等間隔生成 | AoS=-20..20, 5点 | -20,-10,0,10,20 | [[TESTCODE_SHORT:tests.test_scan.TestScanPlanner.test_aos_equal_spacing]] |
| <a id="test-unit-020"></a>TEST-UNIT-020 | REQ-SCAN-002 | 基本走査順序 | serpentine=False | AoA外側、AoS内側で単調走査 | [[TESTCODE_SHORT:tests.test_scan.TestScanPlanner.test_basic_scan_aoa_outer_aos_inner]] |
| <a id="test-unit-021"></a>TEST-UNIT-021 | REQ-SCAN-003 | 蛇行2行 | serpentine=True | 2行目のAoS順序が反転 | [[TESTCODE_SHORT:tests.test_scan.TestScanPlanner.test_serpentine_second_row_reversed]] |
| <a id="test-unit-022"></a>TEST-UNIT-022 | REQ-SCAN-003 | 蛇行3行 | serpentine=True | 奇数/偶数行でAoS方向が交互 | [[TESTCODE_SHORT:tests.test_scan.TestScanPlanner.test_serpentine_three_rows_alternate]] |
| <a id="test-unit-023"></a>TEST-UNIT-023 | REQ-SCAN-001 | 点数総数 | `N_aoa`, `N_aos` | `N_aoa*N_aos`点 | [[TESTCODE_SHORT:tests.test_scan.TestScanPlanner.test_total_point_count]] |
| <a id="test-unit-024"></a>TEST-UNIT-024 | REQ-SCAN-001, REQ-SCAN-002 | CalibrationPoint index連番 | 任意有効設定 | indexが走査順に一意かつ連番 | [[TESTCODE_SHORT:tests.test_scan.TestScanPlanner.test_indices_are_unique_and_sequential]] |

## 4.3 `transform.py` — `AngleTransformer`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-025"></a>TEST-UNIT-025 | REQ-TRANS-001, REQ-TRANS-002 | 原点変換 | AoA=0, AoS=0 | Z=0, A=0を決定論的に返す | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_origin_transform]] |
| <a id="test-unit-026"></a>TEST-UNIT-026 | REQ-TRANS-002 | AoA正、AoS=0 | AoA=10°, AoS=0 | Z=10°, A=0°に絶対誤差0.001 deg以内で一致 | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_positive_aoa_zero_aos]] |
| <a id="test-unit-027"></a>TEST-UNIT-027 | REQ-TRANS-002 | AoA負、AoS=0 | AoA=-10°, AoS=0 | 指定変換式に対応する等価Z/Aを絶対誤差0.001 deg以内で返す | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_negative_aoa_zero_aos_reproduces_input]] |
| <a id="test-unit-028"></a>TEST-UNIT-028 | REQ-TRANS-002 | AoA=0、AoS正 | AoA=0, AoS=10° | 基本式に絶対誤差0.001 deg以内で一致 | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_zero_aoa_positive_aos]] |
| <a id="test-unit-029"></a>TEST-UNIT-029 | REQ-TRANS-002 | AoA/AoS両方正 | 代表値 | tan式、atan2式の期待値に絶対誤差0.001 deg以内で一致 | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_general_solution_matches_formula]] |
| <a id="test-unit-030"></a>TEST-UNIT-030 | REQ-TRANS-002 | 象限II | u<0, v>0となる条件 | atan2の象限が正しい | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_quadrant_ii]] |
| <a id="test-unit-031"></a>TEST-UNIT-031 | REQ-TRANS-002 | 象限III | u<0, v<0となる条件 | atan2の象限が正しい | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_quadrant_iii]] |
| <a id="test-unit-032"></a>TEST-UNIT-032 | REQ-TRANS-002 | 象限IV | u>0, v<0となる条件 | atan2の象限が正しい | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_quadrant_iv]] |
| <a id="test-unit-033"></a>TEST-UNIT-033 | REQ-TRANS-004 | +360 unwrap | 前回A近傍にA+360の等価角 | 前回に近い角度へunwrap | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_unwrap_plus_360]] |
| <a id="test-unit-034"></a>TEST-UNIT-034 | REQ-TRANS-004 | -360 unwrap | 前回A近傍にA-360の等価角 | 前回に近い角度へunwrap | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_unwrap_minus_360]] |
| <a id="test-unit-035"></a>TEST-UNIT-035 | REQ-TRANS-004 | ±180境界をまたぐ連続性 | previous≈179°, current≈-179° | 不要な358°ジャンプを避ける | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_unwrap_avoids_358_degree_jump]] |
| <a id="test-unit-036"></a>TEST-UNIT-036 | REQ-TRANS-003 | 可動範囲内候補優先 | 範囲内候補と範囲外候補 | 範囲内候補を選択 | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_in_range_candidate_has_priority]] |
| <a id="test-unit-037"></a>TEST-UNIT-037 | REQ-TRANS-003 | 前点への連続性優先 | 複数の範囲内候補 | 連続な候補を優先 | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_continuity_has_priority]] |
| <a id="test-unit-038"></a>TEST-UNIT-038 | REQ-TRANS-003 | 総移動量で選択 | 連続性同等候補 | Z/A総移動量の小さい候補 | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_smaller_total_motion_selected]] |
| <a id="test-unit-039"></a>TEST-UNIT-039 | REQ-TRANS-003 | |A|で最終選択 | 上位条件同等 | |A|の小さい候補 | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_smaller_absolute_roll_breaks_tie]] |
| <a id="test-unit-040"></a>TEST-UNIT-040 | REQ-TRANS-002, REQ-TRANS-003 | 等価解候補生成 | 代表基本解 | 同一姿勢を表す設計上の候補集合を生成 | [[TESTCODE_SHORT:tests.test_transform.TestAngleTransformer.test_equivalent_solution_candidates_are_generated]] |

## 4.4 `positioning.py` — `PositionCompensator.calculate_xy`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-041"></a>TEST-UNIT-041 | REQ-POS-001 | θ=0 | 任意の有効Lx/Ly | X=0, Y=0 | [[TESTCODE_SHORT:tests.test_positioning.TestPositionCompensator.test_zero_pitch_requires_no_translation]] |
| <a id="test-unit-042"></a>TEST-UNIT-042 | REQ-POS-001 | θ正の代表値 | 既知Lx/Ly/θ | 仕様式に絶対誤差0.001 mm以内で一致 | [[TESTCODE_SHORT:tests.test_positioning.TestPositionCompensator.test_positive_pitch_matches_formula]] |
| <a id="test-unit-043"></a>TEST-UNIT-043 | REQ-POS-001 | θ負の代表値 | 既知Lx/Ly/θ | 仕様式に絶対誤差0.001 mm以内で一致 | [[TESTCODE_SHORT:tests.test_positioning.TestPositionCompensator.test_negative_pitch_matches_formula]] |
| <a id="test-unit-044"></a>TEST-UNIT-044 | REQ-POS-001 | 小さい正のLy | Lx>0, Ly>0 | 解析解と絶対誤差0.001 mm以内で一致 | [[TESTCODE_SHORT:tests.test_positioning.TestPositionCompensator.test_small_positive_ly]] |
| <a id="test-unit-045"></a>TEST-UNIT-045 | REQ-POS-001 | 小さい正のLx | Lx>0, Ly>0 | 解析解と絶対誤差0.001 mm以内で一致 | [[TESTCODE_SHORT:tests.test_positioning.TestPositionCompensator.test_small_positive_lx]] |
| <a id="test-unit-046"></a>TEST-UNIT-046 | REQ-POS-002 | A角非依存 | 同一θ/Lx/Ly、異なるA | X/Yが変わらない | [[TESTCODE_SHORT:tests.test_positioning.TestPositionCompensator.test_roll_does_not_affect_xy]] |

## 4.5 `limits.py` — `LimitEvaluator`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-047"></a>TEST-UNIT-047 | REQ-LIMIT-001, REQ-VALID-003 | 全軸範囲内 | commandすべて範囲内 | 飽和なし、rotation errorなし | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_all_axes_in_range]] |
| <a id="test-unit-048"></a>TEST-UNIT-048 | REQ-LIMIT-001 | X最大超過 | X>max | X=maxに飽和、x_saturated=True | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_x_above_max_saturates]] |
| <a id="test-unit-049"></a>TEST-UNIT-049 | REQ-LIMIT-001 | X最小超過 | X<min | X=minに飽和 | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_x_below_min_saturates]] |
| <a id="test-unit-050"></a>TEST-UNIT-050 | REQ-LIMIT-001 | Y最大超過 | Y>max | Y=maxに飽和 | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_y_above_max_saturates]] |
| <a id="test-unit-051"></a>TEST-UNIT-051 | REQ-LIMIT-001 | Y最小超過 | Y<min | Y=minに飽和 | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_y_below_min_saturates]] |
| <a id="test-unit-052"></a>TEST-UNIT-052 | REQ-LIMIT-002 | X偏差計算 | X idealが上限超過 | x_deviation=ideal-clampedの絶対偏差 | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_x_deviation]] |
| <a id="test-unit-053"></a>TEST-UNIT-053 | REQ-LIMIT-002 | Y偏差計算 | Y idealが下限超過 | y_deviationが正しく計算 | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_y_deviation]] |
| <a id="test-unit-054"></a>TEST-UNIT-054 | REQ-LIMIT-003, REQ-VALID-003 | Z最大超過 | Z>max | Zを変更せずrotational_error=True | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_z_above_max_not_clamped]] |
| <a id="test-unit-055"></a>TEST-UNIT-055 | REQ-LIMIT-003, REQ-VALID-003 | Z最小超過 | Z<min | Zを変更せずエラー | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_z_below_min_not_clamped]] |
| <a id="test-unit-056"></a>TEST-UNIT-056 | REQ-LIMIT-003, REQ-VALID-003 | A最大超過 | A>max | Aを変更せずエラー | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_a_above_max_not_clamped]] |
| <a id="test-unit-057"></a>TEST-UNIT-057 | REQ-LIMIT-003, REQ-VALID-003 | A最小超過 | A<min | Aを変更せずエラー | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_a_below_min_not_clamped]] |
| <a id="test-unit-058"></a>TEST-UNIT-058 | REQ-LIMIT-001, REQ-LIMIT-003 | X/Y超過とZ/A正常 | X/Yのみ超過 | 生成禁止エラーにはしない | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_xy_only_overrange_is_not_generation_error]] |
| <a id="test-unit-059"></a>TEST-UNIT-059 | REQ-LIMIT-003 | X/Y超過とZ/A超過同時 | 両種超過 | XYは飽和、ZAは非飽和、生成禁止 | [[TESTCODE_SHORT:tests.test_limits.TestLimitEvaluator.test_translation_and_rotation_overrange_combined]] |

## 4.6 `calibration_service.py` — `CalibrationService.build_plan`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-060"></a>TEST-UNIT-060 | REQ-SCAN-001, REQ-TRANS-002, REQ-POS-001 | 正常計画生成 | 小規模有効グリッド | 全点の`PointEvaluation`生成 | [[TESTCODE_SHORT:tests.test_calibration_service.TestCalibrationService.test_build_plan_creates_evaluation_for_every_point]] |
| <a id="test-unit-061"></a>TEST-UNIT-061 | REQ-LIMIT-002 | 最大X/Y偏差集約 | 複数点で異なる偏差 | max_x_deviation/max_y_deviationが各最大値 | [[TESTCODE_SHORT:tests.test_calibration_service.TestCalibrationService.test_plan_aggregates_max_xy_deviation]] |
| <a id="test-unit-062"></a>TEST-UNIT-062 | REQ-LIMIT-003 | Z/Aエラー集約 | 1点のみZA範囲外 | `has_generation_error=True` | [[TESTCODE_SHORT:tests.test_calibration_service.TestCalibrationService.test_any_rotational_error_blocks_generation]] |
| <a id="test-unit-063"></a>TEST-UNIT-063 | REQ-LIMIT-001, REQ-LIMIT-002 | XY警告のみ | 1点以上XY飽和、ZA正常 | plan生成、generation error=False | [[TESTCODE_SHORT:tests.test_calibration_service.TestCalibrationService.test_xy_saturation_alone_does_not_block_generation]] |
| <a id="test-unit-064"></a>TEST-UNIT-064 | REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-004 | 前点情報の走査順伝播 | 蛇行走査 | 走査順にpreviousが渡され連続解選択に反映 | [[TESTCODE_SHORT:tests.test_calibration_service.TestCalibrationService.test_serpentine_plan_keeps_scan_order_and_continuity]] |
| <a id="test-unit-065"></a>TEST-UNIT-065 | REQ-POS-001, REQ-LIMIT-001 | ideal/actual保持 | XY飽和あり | ideal_commandは飽和前、commandは飽和後 | [[TESTCODE_SHORT:tests.test_calibration_service.TestCalibrationService.test_ideal_and_actual_commands_are_both_preserved]] |

## 4.7 `gcode.py` — `GCodeGenerator`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-066"></a>TEST-UNIT-066 | REQ-GCODE-002 | ヘッダ基本構成 | init textあり | init text、`$H`,`G21`,`G90`,`G94`を含む | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_header_contains_required_commands]] |
| <a id="test-unit-067"></a>TEST-UNIT-067 | REQ-INPUT-006, REQ-GCODE-002 | 初期化Gコード保持 | 複数行init text | 行順と内容を保持して挿入 | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_initialization_text_preserved_in_order]] |
| <a id="test-unit-068"></a>TEST-UNIT-068 | REQ-GCODE-003 | 同時4軸指令 | 1点 | 1行にX,Y,Z,A,Fを出力 | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_each_move_has_four_axes_and_feed]] |
| <a id="test-unit-069"></a>TEST-UNIT-069 | REQ-GCODE-003 | G番号ゼロ埋め | 1点 | `G01` と `G04` を使用 | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_g_numbers_are_zero_padded]] |
| <a id="test-unit-070"></a>TEST-UNIT-070 | REQ-INPUT-004, REQ-GCODE-003 | Feed rate出力 | feed_rate=任意有効値 | `F`を小数点以下6桁で各移動指令に出力 | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_feed_rate_has_six_decimal_places]] |
| <a id="test-unit-071"></a>TEST-UNIT-071 | REQ-INPUT-004, REQ-GCODE-003 | 保持時間出力 | hold_time=3.0 | `G04 P3.000000`を出力 | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_hold_time_has_six_decimal_places]] |
| <a id="test-unit-072"></a>TEST-UNIT-072 | REQ-INPUT-007, REQ-GCODE-004 | コメントON | output_comments=True | 各点にAoA/AoS/軸値/XY飽和状態コメント | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_comments_enabled]] |
| <a id="test-unit-073"></a>TEST-UNIT-073 | REQ-INPUT-007, REQ-GCODE-004 | コメントOFF | output_comments=False | 点コメントを出力しない | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_comments_disabled]] |
| <a id="test-unit-074"></a>TEST-UNIT-074 | REQ-GCODE-005 | 最終点停止 | 複数点 | 最終点後に原点/ホーム復帰指令を追加しない | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_no_return_home_after_final_point]] |
| <a id="test-unit-075"></a>TEST-UNIT-075 | REQ-LIMIT-001, REQ-GCODE-003 | XY飽和値を出力 | PointEvaluation.commandが飽和済み | idealではなくcommand値を小数点以下6桁で出力 | [[TESTCODE_SHORT:tests.test_gcode.TestGCodeGenerator.test_saturated_actual_command_is_written]] |

## 4.8 `repositories.py`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-076"></a>TEST-UNIT-076 | REQ-GUI-003 | CSV設定保存→読込往復 | 正常settings | CSV保存前後で同等の設定 | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_settings_csv_round_trip]] |
| <a id="test-unit-077"></a>TEST-UNIT-077 | REQ-GUI-003 | CSVで全オプション保持 | serpentine/comments各組合せ | 読込後も値保持 | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_options_round_trip]] |
| <a id="test-unit-078"></a>TEST-UNIT-078 | REQ-GUI-003 | CSVで軸範囲保持 | X/Y/Z/A各range | 読込後に一致 | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_axis_ranges_round_trip]] |
| <a id="test-unit-079"></a>TEST-UNIT-079 | REQ-GUI-003 | 構造不正CSV読込 | 行列構造が不正なCSV | 未処理例外を発生させず明示的な読込エラーを返す | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_structurally_invalid_csv_returns_explicit_error]] |
| <a id="test-unit-080"></a>TEST-UNIT-080 | REQ-INPUT-006 | 初期化Gコード読込 | UTF-8複数行 | 内容を文字列として保持 | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_initialization_gcode_utf8_multiline]] |
| <a id="test-unit-081"></a>TEST-UNIT-081 | REQ-INPUT-006 | 存在しない初期化ファイル | 無効path | I/Oエラーを上位へ通知 | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_missing_initialization_file_raises_ioerror]] |
| <a id="test-unit-082"></a>TEST-UNIT-082 | REQ-GCODE-001 | `.nc`保存 | 正常path/text | 指定ファイルに同一内容を保存 | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_save_nc_file]] |
| <a id="test-unit-083"></a>TEST-UNIT-083 | REQ-GCODE-001 | Gコード保存失敗 | 書込不可path等 | I/Oエラーを上位へ通知 | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_gcode_save_failure_is_reported]] |
| <a id="test-unit-117"></a>TEST-UNIT-117 | REQ-GUI-003 | CSV必須キー欠損 | 例：`feed_rate`行が存在しない | 未処理例外なし、読込失敗を返し、`CalibrationSettings`を生成しない | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_missing_required_csv_key]] |
| <a id="test-unit-118"></a>TEST-UNIT-118 | REQ-GUI-003 | CSV必須値空欄 | 必須キーはあるがvalueが空欄 | 未処理例外なし、読込失敗を返す | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_blank_required_csv_value]] |
| <a id="test-unit-119"></a>TEST-UNIT-119 | REQ-GUI-003 | CSV数値変換不能 | 数値項目に文字列 | 未処理例外なし、読込失敗を返す | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_non_numeric_csv_value]] |
| <a id="test-unit-120"></a>TEST-UNIT-120 | REQ-GUI-003 | CSVファイルI/O失敗 | 存在しない/読取不可path | 未処理例外なし、上位層が通知可能な読込エラーを返す | [[TESTCODE_SHORT:tests.test_repositories.TestRepositories.test_settings_io_failure_is_wrapped]] |

## 4.9 `controller.py` — `CalibrationController`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-084"></a>TEST-UNIT-084 | REQ-VALID-001, REQ-SCAN-001 | 有効入力変更 | valid settings | validate後にplan再生成 | [[TESTCODE_SHORT:tests.test_controller.TestCalibrationController.test_valid_input_rebuilds_plan]] |
| <a id="test-unit-085"></a>TEST-UNIT-085 | REQ-VALID-001, REQ-VALID-002 | 無効入力変更 | invalid settings | planを再生成しない、生成不可 | [[TESTCODE_SHORT:tests.test_controller.TestCalibrationController.test_invalid_input_does_not_rebuild_plan]] |
| <a id="test-unit-086"></a>TEST-UNIT-086 | REQ-VALID-001 | 無効→有効復帰 | 連続2イベント | エラー解除、plan再生成、生成可能化 | [[TESTCODE_SHORT:tests.test_controller.TestCalibrationController.test_invalid_then_valid_recovers]] |
| <a id="test-unit-087"></a>TEST-UNIT-087 | REQ-VALID-003, REQ-LIMIT-001 | XY警告plan | generation error=False | `can_generate=True` | [[TESTCODE_SHORT:tests.test_controller.TestCalibrationController.test_xy_warning_plan_can_generate]] |
| <a id="test-unit-088"></a>TEST-UNIT-088 | REQ-VALID-003, REQ-LIMIT-003 | ZAエラーplan | generation error=True | `can_generate=False` | [[TESTCODE_SHORT:tests.test_controller.TestCalibrationController.test_rotational_error_plan_cannot_generate]] |
| <a id="test-unit-089"></a>TEST-UNIT-089 | REQ-GUI-003 | 設定適用 | loadしたsettings | current settings更新後にvalidate/build | [[TESTCODE_SHORT:tests.test_controller.TestCalibrationController.test_apply_settings_updates_and_revalidates]] |

## 4.10 `map_view.py` — `CalibrationMapView`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-090"></a>TEST-UNIT-090 | REQ-GUI-002 | 正常点表示 | warning/errorなし | AoS横軸、AoA縦軸で点描画 | [[TESTCODE_SHORT:tests.test_map_view.TestCalibrationMapView.test_axes_are_aos_horizontal_aoa_vertical]] |
| <a id="test-unit-091"></a>TEST-UNIT-091 | REQ-GUI-002, REQ-LIMIT-001 | XY飽和点識別 | x/y_saturated=True | 正常点と視覚的に異なる表現 | [[TESTCODE_SHORT:tests.test_map_view.TestCalibrationMapView.test_saturated_points_use_distinct_visual_group]] |
| <a id="test-unit-092"></a>TEST-UNIT-092 | REQ-GUI-002, REQ-LIMIT-003 | ZAエラー点識別 | rotational_error=True | 生成禁止点として識別可能 | [[TESTCODE_SHORT:tests.test_map_view.TestCalibrationMapView.test_rotational_error_points_use_distinct_visual_group_without_third_color]] |
| <a id="test-unit-124"></a>TEST-UNIT-124 | REQ-GUI-001 | 較正点マップの日本語フォント選択とフォールバック | 日本語対応フォントあり／なしをそれぞれ模擬 | 対応フォントありでは優先候補を選択して日本語文字列を使用し、なしではDejaVu Sansと英語文字列へフォールバックする | [[TESTCODE_SHORT:tests.test_map_view.TestCalibrationMapView.test_japanese_font_selection_and_english_fallback]] |
| <a id="test-unit-125"></a>TEST-UNIT-125 | REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003 | XY飽和とZA範囲外の複合表示 | x_saturatedまたはy_saturated=True、かつrotational_error=True | XY飽和色を維持し、Z/A生成禁止をエラーマーカーと凡例で同時に識別できる | [[TESTCODE_SHORT:tests.test_map_view.TestCalibrationMapView.test_saturated_rotational_error_keeps_saturation_color_and_error_marker_group]] |

## 4.11 `simulation.py` — `SimulationController`, `SimulationView`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|---|
| <a id="test-unit-093"></a>TEST-UNIT-093 | REQ-SIM-002 | 開始フレーム | progress=0 | 最初の較正点を返す  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_start_frame_is_first_point]] |
| <a id="test-unit-094"></a>TEST-UNIT-094 | REQ-SIM-002 | 終了フレーム | progress=1 | 最終較正点を返す  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_end_frame_is_last_point]] |
| <a id="test-unit-095"></a>TEST-UNIT-095 | REQ-SIM-002 | 中間フレーム | 0<progress<1 | 走査順に対応した点を返す  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_middle_progress_maps_to_scan_order]] |
| <a id="test-unit-096"></a>TEST-UNIT-096 | REQ-SIM-002 | 保持時間非反映 | 異なるhold_timeで同plan点数 | 約10秒再生構成が保持時間に依存しない  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_playback_duration_is_independent_of_hold_time]] |
| <a id="test-unit-097"></a>TEST-UNIT-097 | REQ-SIM-003 | 横面図初期化 | valid plan | pitch/X/Yを表現する描画要素生成  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_side_view_is_initialized]] |
| <a id="test-unit-098"></a>TEST-UNIT-098 | REQ-SIM-003 | 正面図初期化 | valid plan | rollを表現する描画要素生成  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_front_view_is_initialized]] |
| <a id="test-unit-099"></a>TEST-UNIT-099 | REQ-SIM-004 | 情報表示 | 任意点 | point番号、AoA/AoS、X/Y/Z/A、状態、進捗を更新  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_render_frame_updates_required_information]] |
| <a id="test-unit-122"></a>TEST-UNIT-122 | REQ-SIM-005 | 較正点マップ初期化 | 複数較正点を持つvalid plan | AoS横軸、AoA縦軸で全較正点を表示し、凡例を表示しない  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_calibration_map_displays_all_points_without_legend]] |
| <a id="test-unit-123"></a>TEST-UNIT-123 | REQ-SIM-006 | 現在較正点の強調・同期 | 異なる2点を連続描画 | 現在点だけが通常点と異なる色で表示され、横面図・正面図と同じ点へ同期更新され、文字注記を追加しない  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_current_calibration_point_color_tracks_rendered_point]] |
| <a id="test-unit-126"></a>TEST-UNIT-126 | REQ-SIM-007 | シミュレーション開始状態 | 有効なplanで開始 | 先頭較正点から再生を開始し、再生中状態と一時停止ボタン「Ⅱ」を表示する  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_start_sets_playing_state_at_first_point]] |
| <a id="test-unit-127"></a>TEST-UNIT-127 | REQ-SIM-008 | 一時停止 | 再生中に一時停止操作 | タイマーが停止し、現在較正点を保持し、再生ボタン「▶」を表示する  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_pause_stops_animation_and_keeps_current_point]] |
| <a id="test-unit-128"></a>TEST-UNIT-128 | REQ-SIM-009 | 一時停止からの再生再開 | 中間点で一時停止後に再生 | 現在位置から再生を再開する  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_resume_restarts_from_current_point]] |
| <a id="test-unit-129"></a>TEST-UNIT-129 | REQ-SIM-010 | 一時停止中の較正点シーク | 一時停止中に指定点へ移動 | 指定した較正点を現在点として保持する  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_seek_while_paused_selects_point]] |
| <a id="test-unit-130"></a>TEST-UNIT-130 | REQ-SIM-011 | 再生中シーク時の自動一時停止 | 再生中にシーク操作開始 | 自動一時停止し、操作終了後も再生ボタン「▶」を表示する  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_seek_while_playing_pauses_automatically]] |
| <a id="test-unit-131"></a>TEST-UNIT-131 | REQ-SIM-012 | シーク表示即時反映 | 指定点へシーク | 横面図・正面図・マップ・数値・進捗表示が同一の指定点へ更新される  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_seek_renders_selected_point_immediately]] |
| <a id="test-unit-132"></a>TEST-UNIT-132 | REQ-SIM-013 | 再生完了 | 最終フレーム到達 | 最終較正点で停止し、自動ループせず、再生ボタン「▶」を表示する  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_animation_completion_stays_at_last_point]] |
| <a id="test-unit-133"></a>TEST-UNIT-133 | REQ-SIM-009 | 完了後の再生 | 完了後に再生操作 | 先頭較正点へ戻って再生を開始する  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_resume_after_completion_restarts_at_first_point]] |
| <a id="test-unit-134"></a>TEST-UNIT-134 | REQ-SIM-014, REQ-SIM-015 | シークバー設定 | 複数較正点のplanを初期化 | 既存プログレスバーを表示せず、較正点インデックス単位で操作でき、大きなつまみを持つ  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_view_has_point_based_seek_bar_with_large_handle]] |
| <a id="test-unit-135"></a>TEST-UNIT-135 | REQ-SIM-016 | 再生状態とボタン表示 | 再生中/停止中/完了後 | 再生中は「Ⅱ」、停止中および完了後は「▶」を表示する  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_playback_button_label_follows_state]] |
| <a id="test-unit-136"></a>TEST-UNIT-136 | REQ-SIM-014 | 進捗表示 | 任意の現在点 | 表示が「現在の較正点 / 全較正点」となり、時間表示を使用しない  | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_progress_text_uses_point_count_not_time]] |


## 4.12 `gui.py` — `MainWindow`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-unit-100"></a>TEST-UNIT-100 | REQ-GUI-001, REQ-GUI-004 | 必須GUI要素 | 起動 | 日本語ラベル、4操作ボタンを持つ | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_required_japanese_labels_and_buttons_are_defined]] |
| <a id="test-unit-101"></a>TEST-UNIT-101 | REQ-VALID-001, REQ-GUI-005 | 入力エラー表示 | フィールドを特定できるValidationIssueまたは数値変換不能入力あり | 該当Entryだけがエラー用背景色となり、枠色は変更せず、既存固定メッセージ領域へ理由を表示し、新規メッセージ領域・アイコン・モーダル表示を追加しない | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_validation_error_changes_target_background_and_shows_existing_message]] |
| <a id="test-unit-102"></a>TEST-UNIT-102 | REQ-VALID-001, REQ-GUI-005 | エラー解除 | issueまたは数値変換不能状態を解消 | 該当Entryの背景色が通常状態へ自動復帰し、固定メッセージ領域の入力エラー理由表示も解除される | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_validation_error_background_and_message_clear_after_recovery]] |
| <a id="test-unit-103"></a>TEST-UNIT-103 | REQ-LIMIT-002, REQ-GUI-005 | XY警告表示 | max X/Y deviationあり | X/Yを別々に表示、合成距離なし | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_xy_warning_shows_separate_deviations_without_resultant]] |
| <a id="test-unit-104"></a>TEST-UNIT-104 | REQ-LIMIT-003, REQ-GUI-005 | ZAエラー表示 | generation error=True | 警告と異なるエラー表示、Sim/G-code無効 | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_rotational_error_disables_actions]] |
| <a id="test-unit-105"></a>TEST-UNIT-105 | REQ-GUI-005 | 正常時ボタン有効化 | valid plan | Sim/G-code有効 | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_valid_plan_enables_actions]] |
| <a id="test-unit-106"></a>TEST-UNIT-106 | REQ-INPUT-006 | 初期化Gコード選択 | 読込成功 | 読み込んだテキストを保持 | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_initialization_gcode_load_success]] |
| <a id="test-unit-107"></a>TEST-UNIT-107 | REQ-GUI-003, REQ-GUI-004 | 設定保存イベント | 保存ボタン | Repositoryへ現在設定を渡す | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_save_settings_passes_current_settings_to_repository]] |
| <a id="test-unit-108"></a>TEST-UNIT-108 | REQ-GUI-003, REQ-GUI-004 | 設定読込イベント | 読込成功 | 読込設定をGUIへ反映し再検証 | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_load_settings_applies_and_revalidates]] |
| <a id="test-unit-109"></a>TEST-UNIT-109 | REQ-SIM-001, REQ-GUI-004 | シミュレーションイベント | valid plan | 同一planをSimulationControllerへ渡す | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_simulation_uses_current_plan]] |
| <a id="test-unit-110"></a>TEST-UNIT-110 | REQ-GCODE-001, REQ-GUI-004 | Gコード生成イベント | valid plan | 保存ダイアログ→Generator→Repositoryの順 | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_generate_gcode_sequence]] |
| <a id="test-unit-121"></a>TEST-UNIT-121 | REQ-GUI-003, REQ-GUI-005 | 設定CSV読込失敗時の防御処理 | Repositoryが読込エラーを返す | 未処理例外なし、読込前のGUI設定とplanを維持、部分適用なし、非モーダルにユーザーへエラー通知 | [[TESTCODE_SHORT:tests.test_gui.TestMainWindow.test_failed_csv_load_keeps_existing_state_and_notifies_user]] |

---

# 5. 要求仕様ID ↔ 単体テストID トレーサビリティマトリックス

| 要求ID | 単体テストID |
|---|---|
| REQ-INPUT-001 | TEST-UNIT-002,003,004,005 |
| REQ-INPUT-002 | TEST-UNIT-006,007,008 |
| REQ-INPUT-003 | TEST-UNIT-011,111,112 |
| REQ-INPUT-004 | TEST-UNIT-009,010,070,071,113,114,115,116 |
| REQ-INPUT-005 | TEST-UNIT-012,013,014,015 |
| REQ-INPUT-006 | TEST-UNIT-067,080,081,106 |
| REQ-INPUT-007 | TEST-UNIT-072,073 |
| REQ-VALID-001 | TEST-UNIT-001,016,084,085,086,101,102 |
| REQ-VALID-002 | TEST-UNIT-001..016,111..116（該当入力検証） |
| REQ-VALID-003 | TEST-UNIT-047,054,055,056,057,087,088 |
| REQ-TRANS-001 | TEST-UNIT-025,026..032 |
| REQ-TRANS-002 | TEST-UNIT-025..032,040,060 |
| REQ-TRANS-003 | TEST-UNIT-036,037,038,039,040 |
| REQ-TRANS-004 | TEST-UNIT-033,034,035,064 |
| REQ-POS-001 | TEST-UNIT-041,042,043,044,045,060,065 |
| REQ-POS-002 | <a id="test-unit-046"></a>TEST-UNIT-046 |
| REQ-LIMIT-001 | TEST-UNIT-047,048,049,050,051,058,059,063,065,075,087,125 |
| REQ-LIMIT-002 | TEST-UNIT-052,053,061,063,103 |
| REQ-LIMIT-003 | TEST-UNIT-054,055,056,057,059,062,088,092,104,125 |
| REQ-SCAN-001 | TEST-UNIT-017,018,019,023,024,060,084 |
| REQ-SCAN-002 | TEST-UNIT-020,024,064 |
| REQ-SCAN-003 | TEST-UNIT-021,022,064 |
| REQ-GCODE-001 | TEST-UNIT-082,083,110 |
| REQ-GCODE-002 | TEST-UNIT-066,067 |
| REQ-GCODE-003 | TEST-UNIT-068,069,070,071,075 |
| REQ-GCODE-004 | TEST-UNIT-072,073 |
| REQ-GCODE-005 | <a id="test-unit-074"></a>TEST-UNIT-074 |
| REQ-SIM-001 | <a id="test-unit-109"></a>TEST-UNIT-109 |
| REQ-SIM-002 | TEST-UNIT-093,094,095,096 |
| REQ-SIM-003 | TEST-UNIT-097,098 |
| REQ-SIM-004 | <a id="test-unit-099"></a>TEST-UNIT-099 |
| REQ-SIM-005 | <a id="test-unit-122"></a>TEST-UNIT-122 |
| REQ-SIM-006 | <a id="test-unit-123"></a>TEST-UNIT-123 |
| REQ-SIM-007 | <a id="test-unit-126"></a>TEST-UNIT-126 |
| REQ-SIM-008 | <a id="test-unit-127"></a>TEST-UNIT-127 |
| REQ-SIM-009 | TEST-UNIT-128,133 |
| REQ-SIM-010 | <a id="test-unit-129"></a>TEST-UNIT-129 |
| REQ-SIM-011 | <a id="test-unit-130"></a>TEST-UNIT-130 |
| REQ-SIM-012 | <a id="test-unit-131"></a>TEST-UNIT-131 |
| REQ-SIM-013 | <a id="test-unit-132"></a>TEST-UNIT-132 |
| REQ-SIM-014 | TEST-UNIT-134,136 |
| REQ-SIM-015 | <a id="test-unit-134"></a>TEST-UNIT-134 |
| REQ-SIM-016 | <a id="test-unit-135"></a>TEST-UNIT-135 |
| REQ-GUI-001 | TEST-UNIT-100,124 |
| REQ-GUI-002 | TEST-UNIT-090,091,092,125 |
| REQ-GUI-003 | TEST-UNIT-076,077,078,079,089,107,108,117,118,119,120,121 |
| REQ-GUI-004 | TEST-UNIT-100,107,108,109,110 |
| REQ-GUI-005 | TEST-UNIT-101,102,103,104,105,121 |

---

# 6. モジュール/メソッド ↔ 単体テストID 対応表

| モジュール/メソッド | テストID |
|---|---|
| `InputValidator.validate` | TEST-UNIT-001..016,111..116 |
| `ScanPlanner.generate_points` | TEST-UNIT-017..024 |
| `AngleTransformer.transform` | TEST-UNIT-025..032,040 |
| `AngleTransformer._unwrap_angle` | TEST-UNIT-033..035 |
| `AngleTransformer._select_solution` | TEST-UNIT-036..039 |
| `AngleTransformer._generate_equivalent_solutions` | <a id="test-unit-040"></a>TEST-UNIT-040 |
| `PositionCompensator.calculate_xy` | TEST-UNIT-041..046 |
| `LimitEvaluator.evaluate` | TEST-UNIT-047..059 |
| `CalibrationService.build_plan` | TEST-UNIT-060..065 |
| `GCodeGenerator._format_header` | TEST-UNIT-066,067 |
| `GCodeGenerator._format_point` | TEST-UNIT-068..073,075 |
| `GCodeGenerator.generate` | TEST-UNIT-066..075 |
| `SettingsRepository.save/load` | TEST-UNIT-076..079,117..120 |
| `InitializationGCodeRepository.load` | TEST-UNIT-080,081 |
| `GCodeRepository.save` | TEST-UNIT-082,083 |
| `CalibrationController.on_settings_changed/apply_settings/can_generate` | TEST-UNIT-084..089 |
| `CalibrationMapView.render` | TEST-UNIT-090..092,125 |
| `CalibrationMapView._configure_matplotlib_font/_text` | <a id="test-unit-124"></a>TEST-UNIT-124 |
| `SimulationController.start/_frame_at` | TEST-UNIT-093..096,126 |
| `SimulationController.pause/resume/seek_to_point/restart_from_beginning/on_animation_complete` | TEST-UNIT-127..133 |
| `SimulationView.initialize/render_frame` | TEST-UNIT-097..099,122,123,131,136 |
| `SimulationView.start_animation/set_playback_state/_on_seek/_on_play_pause/_update_seek_bar/_update_playback_button` | TEST-UNIT-126..136 |
| `MainWindow` | TEST-UNIT-100..110,121 |

---

# 7. ユースケーステスト（組み合わせテスト）仕様

ユースケーステストは、単一クラスの内部ロジックではなく、アーキテクチャのシーケンス図に示された複数モジュールの組み合わせが、ユーザー操作として成立することを確認する。

## 7.1 UC-01 較正条件を入力・更新する

対象経路：

`MainWindow → CalibrationController → InputValidator → CalibrationService → ScanPlanner → AngleTransformer → PositionCompensator → LimitEvaluator → CalibrationMapView`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-uc-01-01"></a>TEST-UC-01-01 | UC-01 | 正常入力 | 全条件を有効値で入力 | 自動検証→全較正点生成→Map更新、Sim/G-code有効 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_valid_input_recalculates_plan]] |
| <a id="test-uc-01-02"></a>TEST-UC-01-02 | UC-01 | AoA範囲不正 | min>=maxへ変更 | 該当入力欄を背景色で強調し既存固定メッセージ領域へ理由表示、plan更新停止、Sim/G-code無効、モーダルなし | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_invalid_aoa_range_blocks_generation]] |
| <a id="test-uc-01-03"></a>TEST-UC-01-03 | UC-01 | 一時的文字入力不正から復帰 | 数値欄を一旦空欄→正常値入力 | 不正欄だけ背景色で強調され既存固定メッセージ領域へ理由表示・生成不可、復帰後に背景色と理由表示を自動解除して再計算 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_temporary_invalid_then_valid_recovers]] |
| <a id="test-uc-01-04"></a>TEST-UC-01-04 | UC-01 | 点数変更によるリアルタイム再生成 | AoA/AoS点数を変更 | 点数積に応じた点列へ更新 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_point_count_change_rebuilds_grid]] |
| <a id="test-uc-01-05"></a>TEST-UC-01-05 | UC-01 | 蛇行OFF→ON | serpentine切替 | 同一較正点集合のまま走査順だけが蛇行に変化 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_serpentine_changes_order_not_set]] |
| <a id="test-uc-01-06"></a>TEST-UC-01-06 | UC-01 | XY上限飽和 | X/Y範囲を狭くして飽和発生 | Mapで警告点識別、X/Y最大偏差表示、Sim/G-codeは有効 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_xy_saturation_warns_but_allows_actions]] |
| <a id="test-uc-01-07"></a>TEST-UC-01-07 | UC-01 | ZA範囲超過 | Z/A範囲を狭くする | Mapでエラー点識別、Z/A非飽和、Sim/G-code無効 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_za_overrange_blocks_actions]] |
| <a id="test-uc-01-08"></a>TEST-UC-01-08 | UC-01 | XY警告とZAエラー同時 | 両方発生する設定 | XY警告情報を保持しつつ生成禁止はZAエラーが優先 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_xy_warning_and_za_error_coexist]] |
| <a id="test-uc-01-09"></a>TEST-UC-01-09 | UC-01 | AoA/AoS=0を含む格子 | 中央点あり | 中央点Z=0,A=0、不要な角度ジャンプなし | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_grid_origin_is_deterministic]] |
| <a id="test-uc-01-10"></a>TEST-UC-01-10 | UC-01 | ±180近傍の連続性を伴う走査 | ロールunwrapが必要な点列 | 走査点間で不要な±360°ジャンプがない | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_roll_has_no_unnecessary_360_jump]] |
| <a id="test-uc-01-11"></a>TEST-UC-01-11 | UC-01 | Lx/Ly下限違反 | LxまたはLyを0以下へ変更 | 該当入力欄を背景色で強調し既存固定メッセージ領域へ理由表示、plan更新停止、Sim/G-code無効 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_nonpositive_offsets_block_plan]] |
| <a id="test-uc-01-12"></a>TEST-UC-01-12 | UC-01 | 保持時間/Feed下限境界 | hold=0.1, F=1→各下限未満へ変更 | 下限値は有効、下限未満では該当入力欄を背景色で強調し既存固定メッセージ領域へ理由表示、生成不可 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc01_hold_and_feed_boundaries]] |

## 7.2 UC-02 初期化Gコードを読み込む

対象経路：

`MainWindow → InitializationGCodeRepository`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-uc-02-01"></a>TEST-UC-02-01 | UC-02 | 正常読込 | UTF-8テキストファイル選択 | 内容を保持し後続Gコード生成に使用可能 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc02_load_initialization_text]] |
| <a id="test-uc-02-02"></a>TEST-UC-02-02 | UC-02 | 複数行読込 | コメント/GRBLコマンドを含む | 行順を保持 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc02_multiline_order_preserved]] |
| <a id="test-uc-02-03"></a>TEST-UC-02-03 | UC-02 | 読込キャンセル | ファイルダイアログをキャンセル | 現在内容を破壊せず何も実行しない | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc02_cancel_keeps_current_initialization]] |
| <a id="test-uc-02-04"></a>TEST-UC-02-04 | UC-02 | 読込失敗 | 削除済み/アクセス不可ファイル | アプリ継続、非モーダルに失敗通知 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc02_load_failure_does_not_terminate_process]] |

## 7.3 UC-03 設定を保存する

対象経路：

`MainWindow → CalibrationController → SettingsRepository`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-uc-03-01"></a>TEST-UC-03-01 | UC-03 | 正常保存 | 現在の有効設定を保存 | 全入力条件とオプションをCSVへ保存 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc03_save_all_settings_to_csv]] |
| <a id="test-uc-03-02"></a>TEST-UC-03-02 | UC-03 | オプション組合せ保存 | serpentine/comments各状態 | CSV保存内容へ正しく反映 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc03_save_option_combinations]] |
| <a id="test-uc-03-03"></a>TEST-UC-03-03 | UC-03 | 保存キャンセル | 保存ダイアログ取消 | ファイルを作成せず状態維持 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc03_cancel_creates_no_file]] |
| <a id="test-uc-03-04"></a>TEST-UC-03-04 | UC-03 | 保存失敗 | 書込不可場所 | アプリ継続、非モーダルに失敗通知 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc03_save_failure_is_recoverable]] |

## 7.4 UC-04 設定を読み込む

対象経路：

`MainWindow → SettingsRepository → CalibrationController → InputValidator → CalibrationService`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-uc-04-01"></a>TEST-UC-04-01 | UC-04 | 正常設定読込 | 保存済み正常CSV | GUIへ全値反映→自動検証→plan再生成 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_load_valid_csv_and_rebuild_plan]] |
| <a id="test-uc-04-02"></a>TEST-UC-04-02 | UC-04 | 蛇行設定復元 | serpentine=TrueのCSV | 読込後の点列順序が蛇行 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_restore_serpentine]] |
| <a id="test-uc-04-03"></a>TEST-UC-04-03 | UC-04 | 読込後XY警告 | XY範囲が狭いCSV設定 | 警告表示、Sim/G-code有効 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_loaded_xy_warning_allows_generation]] |
| <a id="test-uc-04-04"></a>TEST-UC-04-04 | UC-04 | 読込後ZAエラー | ZA範囲が狭いCSV設定 | エラー表示、Sim/G-code無効 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_loaded_za_error_blocks_generation]] |
| <a id="test-uc-04-05"></a>TEST-UC-04-05 | UC-04 | 構造不正CSV | 行列構造が不正 | アプリ継続、現設定/plan維持、部分適用なし、非モーダルに失敗通知 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_structurally_invalid_csv_is_rejected]] |
| <a id="test-uc-04-06"></a>TEST-UC-04-06 | UC-04 | 読込キャンセル | ダイアログ取消 | 現在設定とplanを維持 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_cancel_keeps_settings_and_plan]] |
| <a id="test-uc-04-07"></a>TEST-UC-04-07 | UC-04 | 必須値欠損CSV | 必須キー1件以上なし | アプリ継続、現設定/plan維持、部分適用なし、欠損を示す読込失敗通知 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_missing_required_value_is_rejected]] |
| <a id="test-uc-04-08"></a>TEST-UC-04-08 | UC-04 | 必須値空欄CSV | 必須valueが空欄 | アプリ継続、現設定/plan維持、部分適用なし、読込失敗通知 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_blank_required_value_is_rejected]] |
| <a id="test-uc-04-09"></a>TEST-UC-04-09 | UC-04 | 数値変換不能CSV | 数値項目に文字列 | アプリ継続、現設定/plan維持、部分適用なし、読込失敗通知 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_non_numeric_value_is_rejected]] |
| <a id="test-uc-04-10"></a>TEST-UC-04-10 | UC-04 | 読込I/O失敗 | 削除済み/アクセス不可CSV | アプリ継続、現設定/plan維持、非モーダルに失敗通知 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_io_failure_is_rejected]] |
| <a id="test-uc-04-11"></a>TEST-UC-04-11 | UC-04 | 読込途中で後半項目が不正 | 前半は正常、後半の必須項目が不正 | 前半だけをGUIへ反映せず、全設定を読込前状態のまま維持 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc04_late_error_does_not_partially_apply]] |

## 7.5 UC-05 シミュレーションする

対象経路：

`MainWindow → CalibrationController → SimulationController → SimulationView`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-uc-05-01"></a>TEST-UC-05-01 | UC-05 | 正常シミュレーション | warning/errorなしplan | 約10秒相当で全点を走査し最終点表示 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc05_normal_simulation_uses_full_plan]] |
| <a id="test-uc-05-02"></a>TEST-UC-05-02 | UC-05 | XY警告付きplan | XY飽和あり、ZA正常 | 飽和後commandを使いシミュレーション実行可能 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc05_xy_warning_plan_is_simulatable]] |
| <a id="test-uc-05-03"></a>TEST-UC-05-03 | UC-05 | ZAエラー時 | generation error=True | GUIから実行できない | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc05_za_error_is_not_simulatable_from_gui_state]] |
| <a id="test-uc-05-04"></a>TEST-UC-05-04 | UC-05 | 保持時間変更 | hold_timeを大きく変更 | シミュレーション総時間は実保持時間に比例しない | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc05_duration_does_not_depend_on_hold_time]] |
| <a id="test-uc-05-05"></a>TEST-UC-05-05 | UC-05 | 表示情報整合 | 任意中間点 | point番号/AoA/AoS/X/Y/Z/A/状態/進捗がplanと一致 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc05_display_information_matches_plan]] |
| <a id="test-uc-05-06"></a>TEST-UC-05-06 | UC-05 | 2ビュー同期 | 任意点列 | 横面図と正面図が同一CalibrationPlan・同一点を表示 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc05_two_views_share_same_current_point]] |
| <a id="test-uc-05-07"></a>TEST-UC-05-07 | UC-05 | 較正点マップ表示 | 複数点の正常plan | シミュレーション画面に全較正点がAoA/AoS位置で表示され、凡例がない | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc05_simulation_displays_all_calibration_points_without_legend]] |
| <a id="test-uc-05-08"></a>TEST-UC-05-08 | UC-05 | 3ビュー現在点同期 | 走査中に複数点を切替 | 横面図・正面図・較正点マップ強調が常に同一較正点を示し、強調点だけ色が異なり文字注記がない | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc05_three_views_share_same_current_point]] |
| <a id="test-uc-05-09"></a>TEST-UC-05-09 | UC-05 | 一時停止と再生再開 | 再生中に一時停止し、再生ボタンを押す | 現在較正点を保持して一時停止し、同じ位置から再生を再開する | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_pause_stops_animation_and_keeps_current_point]] [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_resume_restarts_from_current_point]] |
| <a id="test-uc-05-10"></a>TEST-UC-05-10 | UC-05 | 一時停止中のシーク | 一時停止中にシークバーを任意点へドラッグ | 指定点が即時表示され、再生状態は一時停止のまま | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_seek_while_paused_selects_point]] |
| <a id="test-uc-05-11"></a>TEST-UC-05-11 | UC-05 | 再生中のシーク | 再生中にシークバーをドラッグ開始 | 自動一時停止し、指定点表示後は再生ボタンを表示する | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_seek_while_playing_pauses_automatically]] |
| <a id="test-uc-05-12"></a>TEST-UC-05-12 | UC-05 | 再生完了と待機 | 最終点まで再生 | 自動ループせず最終点で停止し、再生ボタンを表示する | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_animation_completion_stays_at_last_point]] |
| <a id="test-uc-05-13"></a>TEST-UC-05-13 | UC-05 | 完了後の再生 | 最終点で再生ボタンを押す | 先頭点へ戻って再生する | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_resume_after_completion_restarts_at_first_point]] |
| <a id="test-uc-05-14"></a>TEST-UC-05-14 | UC-05 | 較正点単位のシーク | シークバーを複数位置へ操作 | 時間位置ではなく、各較正点を選択して表示する | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_view_has_point_based_seek_bar_with_large_handle]] |
| <a id="test-uc-05-15"></a>TEST-UC-05-15 | UC-05 | 3表示と進捗の即時同期 | 任意点へシーク | 横面図・正面図・マップ・数値表示・「現在点/全点」が同一点を示す | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_seek_renders_selected_point_immediately]] |
| <a id="test-uc-05-16"></a>TEST-UC-05-16 | UC-05 | シークバー操作性 | 実GUIでつまみをドラッグ | つまみを容易に操作でき、既存プログレスバーは表示されない | [[TESTCODE_SHORT:tests.test_simulation.TestSimulation.test_view_has_point_based_seek_bar_with_large_handle]] |

## 7.6 UC-06 Gコードを生成する

対象経路：

`MainWindow → CalibrationController → GCodeGenerator → GCodeRepository`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 | 対象テスト |
|---|---|---|---|
| <a id="test-uc-06-01"></a>TEST-UC-06-01 | UC-06 | 正常Gコード生成 | valid plan、init textあり | `.nc`へ正しいヘッダと全点を保存 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_generate_valid_nc]] |
| <a id="test-uc-06-02"></a>TEST-UC-06-02 | UC-06 | コメントON | output_comments=True | 各点コメント付き | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_comments_on]] |
| <a id="test-uc-06-03"></a>TEST-UC-06-03 | UC-06 | コメントOFF | output_comments=False | 点コメントなし | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_comments_off]] |
| <a id="test-uc-06-04"></a>TEST-UC-06-04 | UC-06 | XY飽和付き生成 | XY warningのみ | 生成可能、飽和後X/Yを出力、コメントONなら飽和状態記載 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_xy_saturated_values_are_written]] |
| <a id="test-uc-06-05"></a>TEST-UC-06-05 | UC-06 | ZAエラー時 | generation error=True | 生成ボタン無効、ファイル生成なし | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_za_error_blocks_generation_action]] |
| <a id="test-uc-06-06"></a>TEST-UC-06-06 | UC-06 | Feed/hold反映 | 任意Fとhold | 各`G01`にF、各点後に`G04 P...`、数値は小数点以下6桁 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_feed_and_hold_are_written]] |
| <a id="test-uc-06-07"></a>TEST-UC-06-07 | UC-06 | 初期化Gコード反映 | UC-02で読込済みtext | ヘッダ先頭部へ内容反映 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_loaded_initialization_is_in_header]] |
| <a id="test-uc-06-08"></a>TEST-UC-06-08 | UC-06 | 最終点停止 | 複数点 | 最終点後にホーム/原点復帰を追加しない | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_final_point_has_no_return_home]] |
| <a id="test-uc-06-09"></a>TEST-UC-06-09 | UC-06 | 保存キャンセル | 保存ダイアログ取消 | ファイル生成なし、plan維持 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_cancel_creates_no_file]] |
| <a id="test-uc-06-10"></a>TEST-UC-06-10 | UC-06 | 保存失敗 | 書込不可path | アプリ継続、失敗通知 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_save_failure_is_recoverable]] |
| <a id="test-uc-06-11"></a>TEST-UC-06-11 | UC-06 | GUI/シミュレーション/Gコード整合 | 同一plan | Gコードの各X/Y/Z/Aが表示・Simulationで使うcommandと一致 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_display_simulation_and_gcode_use_same_commands]] |
| <a id="test-uc-06-12"></a>TEST-UC-06-12 | UC-06 | 6桁数値フォーマット | 小数部を持つX/Y/Z/A/F/P | 対象浮動小数点値がすべて小数点以下6桁で出力 | [[TESTCODE_SHORT:tests.test_use_cases.TestUseCases.test_uc06_all_float_words_have_six_decimals]] |

---

# 8. ユースケースID ↔ ユースケーステストID トレーサビリティマトリックス

| ユースケースID | ユースケース名 | テストID |
|---|---|---|
| UC-01 | 較正条件を入力・更新する | TEST-UC-01-01 ～ TEST-UC-01-12 |
| UC-02 | 初期化Gコードを読み込む | TEST-UC-02-01 ～ TEST-UC-02-04 |
| UC-03 | 設定を保存する | TEST-UC-03-01 ～ TEST-UC-03-04 |
| UC-04 | 設定を読み込む | TEST-UC-04-01 ～ TEST-UC-04-11 |
| UC-05 | シミュレーションする | TEST-UC-05-01 ～ TEST-UC-05-16 |
| UC-06 | Gコードを生成する | TEST-UC-06-01 ～ TEST-UC-06-12 |

---

# 9. テスト実装ファイル構成

現在のテストコードは、以下を基本構成として実装する。

```text
tests/
  test_validation.py
  test_scan.py
  test_transform.py
  test_positioning.py
  test_limits.py
  test_calibration_service.py
  test_gcode.py
  test_repositories.py
  test_controller.py
  test_map_view.py
  test_simulation.py
  test_gui.py
  test_use_cases.py
```

各テストメソッド直上またはdocstringにテストIDを必ず記載する。

例：

```python
# TEST-UNIT-025
# Requirements: REQ-TRANS-001, REQ-TRANS-002
def test_origin_transform(self):
    ...

# TEST-UC-01-01
# UseCase: UC-01
def test_uc01_valid_input_recalculates_plan(self):
    ...
```

---

# 10. テスト仕様の運用

本書は実装済みテストと対応関係を維持する現行仕様書として管理する。

- 新しいテスト観点を追加する場合は、テストコードより先に本書へテストID・要求ID・期待結果を追加する。
- 既存テストIDは再利用・不用意な再採番を行わない。
- 要求、アーキテクチャ、テストコードの変更時は、要求ID ↔ TEST IDおよびモジュール/メソッド ↔ TEST IDの両マトリックスを同時に確認する。
- テスト条件の判定基準は `docs/pitot_calibration_gui_spec.md` の要求仕様を基準とする。
