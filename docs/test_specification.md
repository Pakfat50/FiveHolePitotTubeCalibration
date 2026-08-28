# 5孔ピトー管較正Gコード生成GUI テスト仕様書

## 1. 目的

本書は、`docs/pitot_calibration_gui_spec.md` および `docs/architecture_design.md` に基づき、Phase 2として実施するテスト設計を定義する。

本Phaseではテストコードを実装せず、以下を定義する。

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

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-001 | REQ-VALID-001, REQ-VALID-002 | 正常な設定値の検証 | 全項目が有効 | `is_valid=True`、ERRORなし |
| TEST-UNIT-002 | REQ-INPUT-001, REQ-VALID-002 | AoA最小値=最大値 | `aoa_min == aoa_max` | AoA範囲エラー |
| TEST-UNIT-003 | REQ-INPUT-001, REQ-VALID-002 | AoA最小値>最大値 | `aoa_min > aoa_max` | AoA範囲エラー |
| TEST-UNIT-004 | REQ-INPUT-001, REQ-VALID-002 | AoS最小値=最大値 | `aos_min == aos_max` | AoS範囲エラー |
| TEST-UNIT-005 | REQ-INPUT-001, REQ-VALID-002 | AoS最小値>最大値 | `aos_min > aos_max` | AoS範囲エラー |
| TEST-UNIT-006 | REQ-INPUT-002, REQ-VALID-002 | AoA点数の下限正常 | `aoa_points=2` | 点数エラーなし |
| TEST-UNIT-007 | REQ-INPUT-002, REQ-VALID-002 | AoA点数不足 | `aoa_points=1` | 点数エラー |
| TEST-UNIT-008 | REQ-INPUT-002, REQ-VALID-002 | AoS点数不足 | `aos_points=1` | 点数エラー |
| TEST-UNIT-009 | REQ-INPUT-004, REQ-VALID-002 | Feed rate不正 | `feed_rate < 1` または非有限値 | Feed rateエラー |
| TEST-UNIT-010 | REQ-INPUT-004, REQ-VALID-002 | 保持時間不正 | `hold_time_s < 0.1` または非有限値 | 保持時間エラー |
| TEST-UNIT-011 | REQ-INPUT-003, REQ-VALID-002 | 距離が非有限値 | LxまたはLyがNaN/Inf | 距離エラー |
| TEST-UNIT-012 | REQ-INPUT-005, REQ-VALID-002 | X軸最小=最大 | X range min=max | X可動範囲エラー |
| TEST-UNIT-013 | REQ-INPUT-005, REQ-VALID-002 | Y軸最小>最大 | Y range min>max | Y可動範囲エラー |
| TEST-UNIT-014 | REQ-INPUT-005, REQ-VALID-002 | Z軸最小>=最大 | Z range不正 | Z可動範囲エラー |
| TEST-UNIT-015 | REQ-INPUT-005, REQ-VALID-002 | A軸最小>=最大 | A range不正 | A可動範囲エラー |
| TEST-UNIT-016 | REQ-VALID-001 | 複数エラー同時検出 | AoA範囲、点数、Feed等を同時不正 | 複数の`ValidationIssue`を返す |
| TEST-UNIT-111 | REQ-INPUT-003, REQ-VALID-002 | Lx下限違反 | `Lx=0` | 距離エラー |
| TEST-UNIT-112 | REQ-INPUT-003, REQ-VALID-002 | Ly負値 | `Ly<0` | 距離エラー |
| TEST-UNIT-113 | REQ-INPUT-004, REQ-VALID-002 | 保持時間下限正常 | `hold_time_s=0.1` | 保持時間エラーなし |
| TEST-UNIT-114 | REQ-INPUT-004, REQ-VALID-002 | 保持時間下限未満 | `0 <= hold_time_s < 0.1` | 保持時間エラー |
| TEST-UNIT-115 | REQ-INPUT-004, REQ-VALID-002 | Feed rate下限正常 | `feed_rate=1` | Feed rateエラーなし |
| TEST-UNIT-116 | REQ-INPUT-004, REQ-VALID-002 | Feed rate下限未満 | `feed_rate<1` | Feed rateエラー |

## 4.2 `scan.py` — `ScanPlanner.generate_points`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-017 | REQ-SCAN-001 | 2×2最小グリッド | AoA/AoS各2点 | 4点、全端点を含む |
| TEST-UNIT-018 | REQ-SCAN-001 | 等間隔生成 | AoA=-10..10, 5点 | -10,-5,0,5,10 |
| TEST-UNIT-019 | REQ-SCAN-001 | AoS等間隔生成 | AoS=-20..20, 5点 | -20,-10,0,10,20 |
| TEST-UNIT-020 | REQ-SCAN-002 | 基本走査順序 | serpentine=False | AoA外側、AoS内側で単調走査 |
| TEST-UNIT-021 | REQ-SCAN-003 | 蛇行2行 | serpentine=True | 2行目のAoS順序が反転 |
| TEST-UNIT-022 | REQ-SCAN-003 | 蛇行3行 | serpentine=True | 奇数/偶数行でAoS方向が交互 |
| TEST-UNIT-023 | REQ-SCAN-001 | 点数総数 | `N_aoa`, `N_aos` | `N_aoa*N_aos`点 |
| TEST-UNIT-024 | REQ-SCAN-001, REQ-SCAN-002 | CalibrationPoint index連番 | 任意有効設定 | indexが走査順に一意かつ連番 |

## 4.3 `transform.py` — `AngleTransformer`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-025 | REQ-TRANS-001, REQ-TRANS-002 | 原点変換 | AoA=0, AoS=0 | Z=0, A=0を決定論的に返す |
| TEST-UNIT-026 | REQ-TRANS-002 | AoA正、AoS=0 | AoA=10°, AoS=0 | Z=10°, A=0°に絶対誤差0.001 deg以内で一致 |
| TEST-UNIT-027 | REQ-TRANS-002 | AoA負、AoS=0 | AoA=-10°, AoS=0 | 指定変換式に対応する等価Z/Aを絶対誤差0.001 deg以内で返す |
| TEST-UNIT-028 | REQ-TRANS-002 | AoA=0、AoS正 | AoA=0, AoS=10° | 基本式に絶対誤差0.001 deg以内で一致 |
| TEST-UNIT-029 | REQ-TRANS-002 | AoA/AoS両方正 | 代表値 | tan式、atan2式の期待値に絶対誤差0.001 deg以内で一致 |
| TEST-UNIT-030 | REQ-TRANS-002 | 象限II | u<0, v>0となる条件 | atan2の象限が正しい |
| TEST-UNIT-031 | REQ-TRANS-002 | 象限III | u<0, v<0となる条件 | atan2の象限が正しい |
| TEST-UNIT-032 | REQ-TRANS-002 | 象限IV | u>0, v<0となる条件 | atan2の象限が正しい |
| TEST-UNIT-033 | REQ-TRANS-004 | +360 unwrap | 前回A近傍にA+360の等価角 | 前回に近い角度へunwrap |
| TEST-UNIT-034 | REQ-TRANS-004 | -360 unwrap | 前回A近傍にA-360の等価角 | 前回に近い角度へunwrap |
| TEST-UNIT-035 | REQ-TRANS-004 | ±180境界をまたぐ連続性 | previous≈179°, current≈-179° | 不要な358°ジャンプを避ける |
| TEST-UNIT-036 | REQ-TRANS-003 | 可動範囲内候補優先 | 範囲内候補と範囲外候補 | 範囲内候補を選択 |
| TEST-UNIT-037 | REQ-TRANS-003 | 前点への連続性優先 | 複数の範囲内候補 | 連続な候補を優先 |
| TEST-UNIT-038 | REQ-TRANS-003 | 総移動量で選択 | 連続性同等候補 | Z/A総移動量の小さい候補 |
| TEST-UNIT-039 | REQ-TRANS-003 | |A|で最終選択 | 上位条件同等 | |A|の小さい候補 |
| TEST-UNIT-040 | REQ-TRANS-002, REQ-TRANS-003 | 等価解候補生成 | 代表基本解 | 同一姿勢を表す設計上の候補集合を生成 |

## 4.4 `positioning.py` — `PositionCompensator.calculate_xy`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-041 | REQ-POS-001 | θ=0 | 任意の有効Lx/Ly | X=0, Y=0 |
| TEST-UNIT-042 | REQ-POS-001 | θ正の代表値 | 既知Lx/Ly/θ | 仕様式に絶対誤差0.001 mm以内で一致 |
| TEST-UNIT-043 | REQ-POS-001 | θ負の代表値 | 既知Lx/Ly/θ | 仕様式に絶対誤差0.001 mm以内で一致 |
| TEST-UNIT-044 | REQ-POS-001 | 小さい正のLy | Lx>0, Ly>0 | 解析解と絶対誤差0.001 mm以内で一致 |
| TEST-UNIT-045 | REQ-POS-001 | 小さい正のLx | Lx>0, Ly>0 | 解析解と絶対誤差0.001 mm以内で一致 |
| TEST-UNIT-046 | REQ-POS-002 | A角非依存 | 同一θ/Lx/Ly、異なるA | X/Yが変わらない |

## 4.5 `limits.py` — `LimitEvaluator`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-047 | REQ-LIMIT-001, REQ-VALID-003 | 全軸範囲内 | commandすべて範囲内 | 飽和なし、rotation errorなし |
| TEST-UNIT-048 | REQ-LIMIT-001 | X最大超過 | X>max | X=maxに飽和、x_saturated=True |
| TEST-UNIT-049 | REQ-LIMIT-001 | X最小超過 | X<min | X=minに飽和 |
| TEST-UNIT-050 | REQ-LIMIT-001 | Y最大超過 | Y>max | Y=maxに飽和 |
| TEST-UNIT-051 | REQ-LIMIT-001 | Y最小超過 | Y<min | Y=minに飽和 |
| TEST-UNIT-052 | REQ-LIMIT-002 | X偏差計算 | X idealが上限超過 | x_deviation=ideal-clampedの絶対偏差 |
| TEST-UNIT-053 | REQ-LIMIT-002 | Y偏差計算 | Y idealが下限超過 | y_deviationが正しく計算 |
| TEST-UNIT-054 | REQ-LIMIT-003, REQ-VALID-003 | Z最大超過 | Z>max | Zを変更せずrotational_error=True |
| TEST-UNIT-055 | REQ-LIMIT-003, REQ-VALID-003 | Z最小超過 | Z<min | Zを変更せずエラー |
| TEST-UNIT-056 | REQ-LIMIT-003, REQ-VALID-003 | A最大超過 | A>max | Aを変更せずエラー |
| TEST-UNIT-057 | REQ-LIMIT-003, REQ-VALID-003 | A最小超過 | A<min | Aを変更せずエラー |
| TEST-UNIT-058 | REQ-LIMIT-001, REQ-LIMIT-003 | X/Y超過とZ/A正常 | X/Yのみ超過 | 生成禁止エラーにはしない |
| TEST-UNIT-059 | REQ-LIMIT-003 | X/Y超過とZ/A超過同時 | 両種超過 | XYは飽和、ZAは非飽和、生成禁止 |

## 4.6 `calibration_service.py` — `CalibrationService.build_plan`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-060 | REQ-SCAN-001, REQ-TRANS-002, REQ-POS-001 | 正常計画生成 | 小規模有効グリッド | 全点の`PointEvaluation`生成 |
| TEST-UNIT-061 | REQ-LIMIT-002 | 最大X/Y偏差集約 | 複数点で異なる偏差 | max_x_deviation/max_y_deviationが各最大値 |
| TEST-UNIT-062 | REQ-LIMIT-003 | Z/Aエラー集約 | 1点のみZA範囲外 | `has_generation_error=True` |
| TEST-UNIT-063 | REQ-LIMIT-001, REQ-LIMIT-002 | XY警告のみ | 1点以上XY飽和、ZA正常 | plan生成、generation error=False |
| TEST-UNIT-064 | REQ-SCAN-002, REQ-SCAN-003, REQ-TRANS-004 | 前点情報の走査順伝播 | 蛇行走査 | 走査順にpreviousが渡され連続解選択に反映 |
| TEST-UNIT-065 | REQ-POS-001, REQ-LIMIT-001 | ideal/actual保持 | XY飽和あり | ideal_commandは飽和前、commandは飽和後 |

## 4.7 `gcode.py` — `GCodeGenerator`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-066 | REQ-GCODE-002 | ヘッダ基本構成 | init textあり | init text、`$H`,`G21`,`G90`,`G94`を含む |
| TEST-UNIT-067 | REQ-INPUT-006, REQ-GCODE-002 | 初期化Gコード保持 | 複数行init text | 行順と内容を保持して挿入 |
| TEST-UNIT-068 | REQ-GCODE-003 | 同時4軸指令 | 1点 | 1行にX,Y,Z,A,Fを出力 |
| TEST-UNIT-069 | REQ-GCODE-003 | G番号ゼロ埋め | 1点 | `G01` と `G04` を使用 |
| TEST-UNIT-070 | REQ-INPUT-004, REQ-GCODE-003 | Feed rate出力 | feed_rate=任意有効値 | `F`を小数点以下6桁で各移動指令に出力 |
| TEST-UNIT-071 | REQ-INPUT-004, REQ-GCODE-003 | 保持時間出力 | hold_time=3.0 | `G04 P3.000000`を出力 |
| TEST-UNIT-072 | REQ-INPUT-007, REQ-GCODE-004 | コメントON | output_comments=True | 各点にAoA/AoS/軸値/XY飽和状態コメント |
| TEST-UNIT-073 | REQ-INPUT-007, REQ-GCODE-004 | コメントOFF | output_comments=False | 点コメントを出力しない |
| TEST-UNIT-074 | REQ-GCODE-005 | 最終点停止 | 複数点 | 最終点後に原点/ホーム復帰指令を追加しない |
| TEST-UNIT-075 | REQ-LIMIT-001, REQ-GCODE-003 | XY飽和値を出力 | PointEvaluation.commandが飽和済み | idealではなくcommand値を小数点以下6桁で出力 |

## 4.8 `repositories.py`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-076 | REQ-GUI-003 | CSV設定保存→読込往復 | 正常settings | CSV保存前後で同等の設定 |
| TEST-UNIT-077 | REQ-GUI-003 | CSVで全オプション保持 | serpentine/comments各組合せ | 読込後も値保持 |
| TEST-UNIT-078 | REQ-GUI-003 | CSVで軸範囲保持 | X/Y/Z/A各range | 読込後に一致 |
| TEST-UNIT-079 | REQ-GUI-003 | 構造不正CSV読込 | 行列構造が不正なCSV | 未処理例外を発生させず明示的な読込エラーを返す |
| TEST-UNIT-080 | REQ-INPUT-006 | 初期化Gコード読込 | UTF-8複数行 | 内容を文字列として保持 |
| TEST-UNIT-081 | REQ-INPUT-006 | 存在しない初期化ファイル | 無効path | I/Oエラーを上位へ通知 |
| TEST-UNIT-082 | REQ-GCODE-001 | `.nc`保存 | 正常path/text | 指定ファイルに同一内容を保存 |
| TEST-UNIT-083 | REQ-GCODE-001 | Gコード保存失敗 | 書込不可path等 | I/Oエラーを上位へ通知 |
| TEST-UNIT-117 | REQ-GUI-003 | CSV必須キー欠損 | 例：`feed_rate`行が存在しない | 未処理例外なし、読込失敗を返し、`CalibrationSettings`を生成しない |
| TEST-UNIT-118 | REQ-GUI-003 | CSV必須値空欄 | 必須キーはあるがvalueが空欄 | 未処理例外なし、読込失敗を返す |
| TEST-UNIT-119 | REQ-GUI-003 | CSV数値変換不能 | 数値項目に文字列 | 未処理例外なし、読込失敗を返す |
| TEST-UNIT-120 | REQ-GUI-003 | CSVファイルI/O失敗 | 存在しない/読取不可path | 未処理例外なし、上位層が通知可能な読込エラーを返す |

## 4.9 `controller.py` — `CalibrationController`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-084 | REQ-VALID-001, REQ-SCAN-001 | 有効入力変更 | valid settings | validate後にplan再生成 |
| TEST-UNIT-085 | REQ-VALID-001, REQ-VALID-002 | 無効入力変更 | invalid settings | planを再生成しない、生成不可 |
| TEST-UNIT-086 | REQ-VALID-001 | 無効→有効復帰 | 連続2イベント | エラー解除、plan再生成、生成可能化 |
| TEST-UNIT-087 | REQ-VALID-003, REQ-LIMIT-001 | XY警告plan | generation error=False | `can_generate=True` |
| TEST-UNIT-088 | REQ-VALID-003, REQ-LIMIT-003 | ZAエラーplan | generation error=True | `can_generate=False` |
| TEST-UNIT-089 | REQ-GUI-003 | 設定適用 | loadしたsettings | current settings更新後にvalidate/build |

## 4.10 `map_view.py` — `CalibrationMapView`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-090 | REQ-GUI-002 | 正常点表示 | warning/errorなし | AoS横軸、AoA縦軸で点描画 |
| TEST-UNIT-091 | REQ-GUI-002, REQ-LIMIT-001 | XY飽和点識別 | x/y_saturated=True | 正常点と視覚的に異なる表現 |
| TEST-UNIT-092 | REQ-GUI-002, REQ-LIMIT-003 | ZAエラー点識別 | rotational_error=True | 生成禁止点として識別可能 |
| TEST-UNIT-124 | REQ-GUI-001 | 較正点マップの日本語フォント選択とフォールバック | 日本語対応フォントあり／なしをそれぞれ模擬 | 対応フォントありでは優先候補を選択して日本語文字列を使用し、なしではDejaVu Sansと英語文字列へフォールバックする |
| TEST-UNIT-125 | REQ-GUI-002, REQ-LIMIT-001, REQ-LIMIT-003 | XY飽和とZA範囲外の複合表示 | x_saturatedまたはy_saturated=True、かつrotational_error=True | XY飽和色を維持し、Z/A生成禁止をエラーマーカーと凡例で同時に識別できる |

## 4.11 `simulation.py` — `SimulationController`, `SimulationView`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-093 | REQ-SIM-002 | 開始フレーム | progress=0 | 最初の較正点を返す |
| TEST-UNIT-094 | REQ-SIM-002 | 終了フレーム | progress=1 | 最終較正点を返す |
| TEST-UNIT-095 | REQ-SIM-002 | 中間フレーム | 0<progress<1 | 走査順に対応した点を返す |
| TEST-UNIT-096 | REQ-SIM-002 | 保持時間非反映 | 異なるhold_timeで同plan点数 | 約10秒再生構成が保持時間に依存しない |
| TEST-UNIT-097 | REQ-SIM-003 | 横面図初期化 | valid plan | pitch/X/Yを表現する描画要素生成 |
| TEST-UNIT-098 | REQ-SIM-003 | 正面図初期化 | valid plan | rollを表現する描画要素生成 |
| TEST-UNIT-099 | REQ-SIM-004 | 情報表示 | 任意点 | point番号、AoA/AoS、X/Y/Z/A、状態、進捗を更新 |
| TEST-UNIT-122 | REQ-SIM-005 | 較正点マップ初期化 | 複数較正点を持つvalid plan | AoS横軸、AoA縦軸で全較正点を表示し、凡例を表示しない |
| TEST-UNIT-123 | REQ-SIM-006 | 現在較正点の強調・同期 | 異なる2点を連続描画 | 現在点だけが通常点と異なる色で表示され、横面図・正面図と同じ点へ同期更新され、文字注記を追加しない |

## 4.12 `gui.py` — `MainWindow`

| テストID | 要求ID | テスト内容 | 入力/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UNIT-100 | REQ-GUI-001, REQ-GUI-004 | 必須GUI要素 | 起動 | 日本語ラベル、4操作ボタンを持つ |
| TEST-UNIT-101 | REQ-VALID-001, REQ-GUI-005 | 入力エラー表示 | フィールドを特定できるValidationIssueまたは数値変換不能入力あり | 該当Entryだけがエラー用背景色となり、枠色は変更せず、既存固定メッセージ領域へ理由を表示し、新規メッセージ領域・アイコン・モーダル表示を追加しない |
| TEST-UNIT-102 | REQ-VALID-001, REQ-GUI-005 | エラー解除 | issueまたは数値変換不能状態を解消 | 該当Entryの背景色が通常状態へ自動復帰し、固定メッセージ領域の入力エラー理由表示も解除される |
| TEST-UNIT-103 | REQ-LIMIT-002, REQ-GUI-005 | XY警告表示 | max X/Y deviationあり | X/Yを別々に表示、合成距離なし |
| TEST-UNIT-104 | REQ-LIMIT-003, REQ-GUI-005 | ZAエラー表示 | generation error=True | 警告と異なるエラー表示、Sim/G-code無効 |
| TEST-UNIT-105 | REQ-GUI-005 | 正常時ボタン有効化 | valid plan | Sim/G-code有効 |
| TEST-UNIT-106 | REQ-INPUT-006 | 初期化Gコード選択 | 読込成功 | 読み込んだテキストを保持 |
| TEST-UNIT-107 | REQ-GUI-003, REQ-GUI-004 | 設定保存イベント | 保存ボタン | Repositoryへ現在設定を渡す |
| TEST-UNIT-108 | REQ-GUI-003, REQ-GUI-004 | 設定読込イベント | 読込成功 | 読込設定をGUIへ反映し再検証 |
| TEST-UNIT-109 | REQ-SIM-001, REQ-GUI-004 | シミュレーションイベント | valid plan | 同一planをSimulationControllerへ渡す |
| TEST-UNIT-110 | REQ-GCODE-001, REQ-GUI-004 | Gコード生成イベント | valid plan | 保存ダイアログ→Generator→Repositoryの順 |
| TEST-UNIT-121 | REQ-GUI-003, REQ-GUI-005 | 設定CSV読込失敗時の防御処理 | Repositoryが読込エラーを返す | 未処理例外なし、読込前のGUI設定とplanを維持、部分適用なし、非モーダルにユーザーへエラー通知 |

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
| REQ-POS-002 | TEST-UNIT-046 |
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
| REQ-GCODE-005 | TEST-UNIT-074 |
| REQ-SIM-001 | TEST-UNIT-109 |
| REQ-SIM-002 | TEST-UNIT-093,094,095,096 |
| REQ-SIM-003 | TEST-UNIT-097,098 |
| REQ-SIM-004 | TEST-UNIT-099 |
| REQ-SIM-005 | TEST-UNIT-122 |
| REQ-SIM-006 | TEST-UNIT-123 |
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
| `AngleTransformer._generate_equivalent_solutions` | TEST-UNIT-040 |
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
| `CalibrationMapView._configure_matplotlib_font/_text` | TEST-UNIT-124 |
| `SimulationController.start/_frame_at` | TEST-UNIT-093..096 |
| `SimulationView.initialize/render_frame` | TEST-UNIT-097..099,122,123 |
| `MainWindow` | TEST-UNIT-100..110,121 |

---

# 7. ユースケーステスト（組み合わせテスト）仕様

ユースケーステストは、単一クラスの内部ロジックではなく、アーキテクチャのシーケンス図に示された複数モジュールの組み合わせが、ユーザー操作として成立することを確認する。

## 7.1 UC-01 較正条件を入力・更新する

対象経路：

`MainWindow → CalibrationController → InputValidator → CalibrationService → ScanPlanner → AngleTransformer → PositionCompensator → LimitEvaluator → CalibrationMapView`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UC-01-01 | UC-01 | 正常入力 | 全条件を有効値で入力 | 自動検証→全較正点生成→Map更新、Sim/G-code有効 |
| TEST-UC-01-02 | UC-01 | AoA範囲不正 | min>=maxへ変更 | 該当入力欄を背景色で強調し既存固定メッセージ領域へ理由表示、plan更新停止、Sim/G-code無効、モーダルなし |
| TEST-UC-01-03 | UC-01 | 一時的文字入力不正から復帰 | 数値欄を一旦空欄→正常値入力 | 不正欄だけ背景色で強調され既存固定メッセージ領域へ理由表示・生成不可、復帰後に背景色と理由表示を自動解除して再計算 |
| TEST-UC-01-04 | UC-01 | 点数変更によるリアルタイム再生成 | AoA/AoS点数を変更 | 点数積に応じた点列へ更新 |
| TEST-UC-01-05 | UC-01 | 蛇行OFF→ON | serpentine切替 | 同一較正点集合のまま走査順だけが蛇行に変化 |
| TEST-UC-01-06 | UC-01 | XY上限飽和 | X/Y範囲を狭くして飽和発生 | Mapで警告点識別、X/Y最大偏差表示、Sim/G-codeは有効 |
| TEST-UC-01-07 | UC-01 | ZA範囲超過 | Z/A範囲を狭くする | Mapでエラー点識別、Z/A非飽和、Sim/G-code無効 |
| TEST-UC-01-08 | UC-01 | XY警告とZAエラー同時 | 両方発生する設定 | XY警告情報を保持しつつ生成禁止はZAエラーが優先 |
| TEST-UC-01-09 | UC-01 | AoA/AoS=0を含む格子 | 中央点あり | 中央点Z=0,A=0、不要な角度ジャンプなし |
| TEST-UC-01-10 | UC-01 | ±180近傍の連続性を伴う走査 | ロールunwrapが必要な点列 | 走査点間で不要な±360°ジャンプがない |
| TEST-UC-01-11 | UC-01 | Lx/Ly下限違反 | LxまたはLyを0以下へ変更 | 該当入力欄を背景色で強調し既存固定メッセージ領域へ理由表示、plan更新停止、Sim/G-code無効 |
| TEST-UC-01-12 | UC-01 | 保持時間/Feed下限境界 | hold=0.1, F=1→各下限未満へ変更 | 下限値は有効、下限未満では該当入力欄を背景色で強調し既存固定メッセージ領域へ理由表示、生成不可 |

## 7.2 UC-02 初期化Gコードを読み込む

対象経路：

`MainWindow → InitializationGCodeRepository`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UC-02-01 | UC-02 | 正常読込 | UTF-8テキストファイル選択 | 内容を保持し後続Gコード生成に使用可能 |
| TEST-UC-02-02 | UC-02 | 複数行読込 | コメント/GRBLコマンドを含む | 行順を保持 |
| TEST-UC-02-03 | UC-02 | 読込キャンセル | ファイルダイアログをキャンセル | 現在内容を破壊せず何も実行しない |
| TEST-UC-02-04 | UC-02 | 読込失敗 | 削除済み/アクセス不可ファイル | アプリ継続、非モーダルに失敗通知 |

## 7.3 UC-03 設定を保存する

対象経路：

`MainWindow → CalibrationController → SettingsRepository`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UC-03-01 | UC-03 | 正常保存 | 現在の有効設定を保存 | 全入力条件とオプションをCSVへ保存 |
| TEST-UC-03-02 | UC-03 | オプション組合せ保存 | serpentine/comments各状態 | CSV保存内容へ正しく反映 |
| TEST-UC-03-03 | UC-03 | 保存キャンセル | 保存ダイアログ取消 | ファイルを作成せず状態維持 |
| TEST-UC-03-04 | UC-03 | 保存失敗 | 書込不可場所 | アプリ継続、非モーダルに失敗通知 |

## 7.4 UC-04 設定を読み込む

対象経路：

`MainWindow → SettingsRepository → CalibrationController → InputValidator → CalibrationService`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UC-04-01 | UC-04 | 正常設定読込 | 保存済み正常CSV | GUIへ全値反映→自動検証→plan再生成 |
| TEST-UC-04-02 | UC-04 | 蛇行設定復元 | serpentine=TrueのCSV | 読込後の点列順序が蛇行 |
| TEST-UC-04-03 | UC-04 | 読込後XY警告 | XY範囲が狭いCSV設定 | 警告表示、Sim/G-code有効 |
| TEST-UC-04-04 | UC-04 | 読込後ZAエラー | ZA範囲が狭いCSV設定 | エラー表示、Sim/G-code無効 |
| TEST-UC-04-05 | UC-04 | 構造不正CSV | 行列構造が不正 | アプリ継続、現設定/plan維持、部分適用なし、非モーダルに失敗通知 |
| TEST-UC-04-06 | UC-04 | 読込キャンセル | ダイアログ取消 | 現在設定とplanを維持 |
| TEST-UC-04-07 | UC-04 | 必須値欠損CSV | 必須キー1件以上なし | アプリ継続、現設定/plan維持、部分適用なし、欠損を示す読込失敗通知 |
| TEST-UC-04-08 | UC-04 | 必須値空欄CSV | 必須valueが空欄 | アプリ継続、現設定/plan維持、部分適用なし、読込失敗通知 |
| TEST-UC-04-09 | UC-04 | 数値変換不能CSV | 数値項目に文字列 | アプリ継続、現設定/plan維持、部分適用なし、読込失敗通知 |
| TEST-UC-04-10 | UC-04 | 読込I/O失敗 | 削除済み/アクセス不可CSV | アプリ継続、現設定/plan維持、非モーダルに失敗通知 |
| TEST-UC-04-11 | UC-04 | 読込途中で後半項目が不正 | 前半は正常、後半の必須項目が不正 | 前半だけをGUIへ反映せず、全設定を読込前状態のまま維持 |

## 7.5 UC-05 シミュレーションする

対象経路：

`MainWindow → CalibrationController → SimulationController → SimulationView`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UC-05-01 | UC-05 | 正常シミュレーション | warning/errorなしplan | 約10秒相当で全点を走査し最終点表示 |
| TEST-UC-05-02 | UC-05 | XY警告付きplan | XY飽和あり、ZA正常 | 飽和後commandを使いシミュレーション実行可能 |
| TEST-UC-05-03 | UC-05 | ZAエラー時 | generation error=True | GUIから実行できない |
| TEST-UC-05-04 | UC-05 | 保持時間変更 | hold_timeを大きく変更 | シミュレーション総時間は実保持時間に比例しない |
| TEST-UC-05-05 | UC-05 | 表示情報整合 | 任意中間点 | point番号/AoA/AoS/X/Y/Z/A/状態/進捗がplanと一致 |
| TEST-UC-05-06 | UC-05 | 2ビュー同期 | 任意点列 | 横面図と正面図が同一CalibrationPlan・同一点を表示 |
| TEST-UC-05-07 | UC-05 | 較正点マップ表示 | 複数点の正常plan | シミュレーション画面に全較正点がAoA/AoS位置で表示され、凡例がない |
| TEST-UC-05-08 | UC-05 | 3ビュー現在点同期 | 走査中に複数点を切替 | 横面図・正面図・較正点マップ強調が常に同一較正点を示し、強調点だけ色が異なり文字注記がない |

## 7.6 UC-06 Gコードを生成する

対象経路：

`MainWindow → CalibrationController → GCodeGenerator → GCodeRepository`

| テストID | トレースUC | シナリオ | 操作/条件 | 期待結果 |
|---|---|---|---|---|
| TEST-UC-06-01 | UC-06 | 正常Gコード生成 | valid plan、init textあり | `.nc`へ正しいヘッダと全点を保存 |
| TEST-UC-06-02 | UC-06 | コメントON | output_comments=True | 各点コメント付き |
| TEST-UC-06-03 | UC-06 | コメントOFF | output_comments=False | 点コメントなし |
| TEST-UC-06-04 | UC-06 | XY飽和付き生成 | XY warningのみ | 生成可能、飽和後X/Yを出力、コメントONなら飽和状態記載 |
| TEST-UC-06-05 | UC-06 | ZAエラー時 | generation error=True | 生成ボタン無効、ファイル生成なし |
| TEST-UC-06-06 | UC-06 | Feed/hold反映 | 任意Fとhold | 各`G01`にF、各点後に`G04 P...`、数値は小数点以下6桁 |
| TEST-UC-06-07 | UC-06 | 初期化Gコード反映 | UC-02で読込済みtext | ヘッダ先頭部へ内容反映 |
| TEST-UC-06-08 | UC-06 | 最終点停止 | 複数点 | 最終点後にホーム/原点復帰を追加しない |
| TEST-UC-06-09 | UC-06 | 保存キャンセル | 保存ダイアログ取消 | ファイル生成なし、plan維持 |
| TEST-UC-06-10 | UC-06 | 保存失敗 | 書込不可path | アプリ継続、失敗通知 |
| TEST-UC-06-11 | UC-06 | GUI/シミュレーション/Gコード整合 | 同一plan | Gコードの各X/Y/Z/Aが表示・Simulationで使うcommandと一致 |
| TEST-UC-06-12 | UC-06 | 6桁数値フォーマット | 小数部を持つX/Y/Z/A/F/P | 対象浮動小数点値がすべて小数点以下6桁で出力 |

---

# 8. ユースケースID ↔ ユースケーステストID トレーサビリティマトリックス

| ユースケースID | ユースケース名 | テストID |
|---|---|---|
| UC-01 | 較正条件を入力・更新する | TEST-UC-01-01 ～ TEST-UC-01-12 |
| UC-02 | 初期化Gコードを読み込む | TEST-UC-02-01 ～ TEST-UC-02-04 |
| UC-03 | 設定を保存する | TEST-UC-03-01 ～ TEST-UC-03-04 |
| UC-04 | 設定を読み込む | TEST-UC-04-01 ～ TEST-UC-04-11 |
| UC-05 | シミュレーションする | TEST-UC-05-01 ～ TEST-UC-05-08 |
| UC-06 | Gコードを生成する | TEST-UC-06-01 ～ TEST-UC-06-12 |

---

# 9. テスト実装時のファイル構成案

Phase 3でテストコードを実装する場合、以下を基本構成とする。

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

# 10. Phase 3への入力条件

Phase 3「テスト実装」へ進む前に、本テスト仕様についてユーザーレビューを受ける。

テスト条件はすべて要求仕様へ反映済みであり、本書では要求仕様を試験の唯一の基準とする。

Phase 3では、本書に定義されたテストIDを変更せずにテストコードへ実装する。