# 5孔ピトー管較正Gコード生成GUI 仕様書

## 1. 目的

4軸GRBL制御装置を用いて、5孔ピトー管の較正点へ移動するGコードを生成するWindows 11向けGUIソフトウェアを提供する。

対象コントローラはArduino Mega 2560 + RAMPS 1.4/1.6 + grbl-Mega-5Xとし、GRBL軸は以下のとおり対応させる。

| GRBL軸 | 機械動作 |
|---|---|
| X | ピトー管支持部の水平並進 |
| Y | ピトー管支持部の上下並進 |
| Z | 実ピッチ軸（Z軸周りの回転） |
| A | 実ロール軸（ピトー管軸周りの回転） |

## 2. 用語・座標系

- X軸：ピトー管の機首方向
- Y軸：機体上下方向。上方向を正とする
- Z軸：機体左右方向。上方から見て右方向を正とする
- AoA：ピトー管軸と気流の上下方向の角度。上向きを正とする
- AoS：ピトー管軸と気流の左右方向の角度。上方から見て右向きを正とする
- 実ピッチ角：GRBL Z軸の指令角
- 実ロール角：GRBL A軸の指令角

全軸の基準位置は0とする。XYの原点は可動範囲中央かつ風洞中心、ZAの原点はAoA=AoS=0 degとなる姿勢とする。

## 3. EARS要求

### 3.1 入力

#### REQ-INPUT-001（較正範囲）

ソフトウェアは、ユーザーがAoAおよびAoSの最小値・最大値をdeg単位で入力できなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:models.CalibrationSettings]]、[[API:gui.MainWindow._build_widgets]]、[[API:gui.MainWindow._collect_raw_input]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-002]]、[[TESTSPEC:TEST-UNIT-003]]、[[TESTSPEC:TEST-UNIT-004]]、[[TESTSPEC:TEST-UNIT-005]]

#### REQ-INPUT-002（較正点数）

ソフトウェアは、AoAおよびAoSの較正点数を入力できなければならない。点数は両端を含むものとする。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:models.CalibrationSettings]]、[[API:gui.MainWindow._build_widgets]]、[[API:gui.MainWindow._collect_raw_input]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-006]]、[[TESTSPEC:TEST-UNIT-007]]、[[TESTSPEC:TEST-UNIT-008]]

#### REQ-INPUT-003（距離）

ソフトウェアは、ピッチ回転中心からピトー管先端までの基準姿勢におけるX方向距離およびY方向距離をmm単位で入力できなければならない。

LxおよびLyは、いずれも0.0 mm以上の有限な実数でなければならない。0.0 mmは許容する。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:models.CalibrationSettings]]、[[API:gui.MainWindow._build_widgets]]、[[API:gui.MainWindow._collect_raw_input]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-011]]、[[TESTSPEC:TEST-UNIT-111]]、[[TESTSPEC:TEST-UNIT-112]]

#### REQ-INPUT-004（移動条件）

ソフトウェアは、以下を入力できなければならない。

- 較正点保持時間 [s]
- 合成送り速度 Feed rate F [unit/min]

較正点保持時間は **0.1 s以上** でなければならない。

Feed rateは **1 unit/min以上** でなければならない。

送り速度はGRBLのG94における送り速度として扱い、X/Y/Z/A各軸の個別速度は入力しない。

加速度、steps/mm、steps/degは入力対象外とし、GRBL側で設定する。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:models.CalibrationSettings]]、[[API:gui.MainWindow._build_widgets]]、[[API:gui.MainWindow._collect_raw_input]]、[[API:gcode.GCodeGenerator._format_point]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-009]]、[[TESTSPEC:TEST-UNIT-010]]、[[TESTSPEC:TEST-UNIT-113]]、[[TESTSPEC:TEST-UNIT-114]]、[[TESTSPEC:TEST-UNIT-115]]、[[TESTSPEC:TEST-UNIT-116]]、[[TESTSPEC:TEST-UNIT-070]]、[[TESTSPEC:TEST-UNIT-071]]

#### REQ-INPUT-005（実軸可動範囲）

ソフトウェアは、X、Y、Z、A各軸の最小値・最大値を入力できなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:models.AxisLimits]]、[[API:models.AxisRange]]、[[API:gui.MainWindow._build_widgets]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-012]]、[[TESTSPEC:TEST-UNIT-013]]、[[TESTSPEC:TEST-UNIT-014]]、[[TESTSPEC:TEST-UNIT-015]]

#### REQ-INPUT-006（初期化Gコード） { #req-input-006 }

ソフトウェアは、初期化用Gコードをテキストファイルから読み込めなければならない。初期化Gコード入力欄をGUIに設けてもよいが、基本操作はファイル選択とする。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-02]]
- 製品コード: [[API:repositories.InitializationGCodeRepository.load]]、[[API:gui.MainWindow._on_load_initialization]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-067]]、[[TESTSPEC:TEST-UNIT-080]]、[[TESTSPEC:TEST-UNIT-081]]、[[TESTSPEC:TEST-UNIT-106]]

#### REQ-INPUT-007（オプション）

ソフトウェアは、以下のオプションを指定できなければならない。

- 蛇行走査を使用する
- Gコードコメントを出力する

### 3.2 入力値検証

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]、[[ARCH:UC-06]]
- 製品コード: [[API:models.CalibrationSettings]]、[[API:gui.MainWindow._build_widgets]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-072]]、[[TESTSPEC:TEST-UNIT-073]]

#### REQ-VALID-001（入力値のリアルタイム検証）

ソフトウェアは、入力値が変更されるたびに入力値を検証しなければならない。

入力中に不正値が存在する場合、モーダルなエラーダイアログを表示してはならない。ソフトウェアは不正な入力フィールドを個別に特定し、該当する入力フィールドの背景色を通常時と異なる色へ変更して視覚的に強調するとともに、GUI内の既存の固定メッセージ領域にエラー理由を表示しなければならない。入力エラーを示すために入力フィールドの枠色を変更してはならず、入力欄近傍等へ新たなメッセージ領域やアイコンを追加してGUIレイアウトを変更してはならない。

不正値が解消された場合、ソフトウェアは該当する入力フィールドの背景色を通常状態へ戻し、固定メッセージ領域の入力エラー理由表示を自動的に解除しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:controller.CalibrationController.on_settings_changed]]、[[API:gui.MainWindow._on_gui_input_changed]]、[[API:gui.MainWindow._find_numeric_parse_errors]]、[[API:gui.MainWindow._apply_validation_highlights]]、[[API:gui.MainWindow._update_validation_display]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-001]]、[[TESTSPEC:TEST-UNIT-016]]、[[TESTSPEC:TEST-UNIT-084]]、[[TESTSPEC:TEST-UNIT-085]]、[[TESTSPEC:TEST-UNIT-086]]、[[TESTSPEC:TEST-UNIT-101]]、[[TESTSPEC:TEST-UNIT-102]]

#### REQ-VALID-002（入力値整合性）

最小値が最大値以上、点数が2未満、Feed rateが1 unit/min未満、保持時間が0.1 s未満、Lx/Lyが0未満または非有限値である場合、ソフトウェアは該当入力をエラー状態とし、較正点列の更新、シミュレーションおよびGコード生成を実行してはならない。Lx/Ly=0.0 mmは有効値として扱う。

入力途中の一時的な不正状態は許容し、ユーザー操作を妨げるモーダルダイアログは表示しない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]、[[ARCH:UC-04]]、[[ARCH:UC-05]]、[[ARCH:UC-06]]
- 製品コード: [[API:controller.CalibrationController.can_generate]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-001]]、[[TESTSPEC:TEST-UNIT-002]]、[[TESTSPEC:TEST-UNIT-003]]、[[TESTSPEC:TEST-UNIT-004]]、[[TESTSPEC:TEST-UNIT-005]]、[[TESTSPEC:TEST-UNIT-006]]、[[TESTSPEC:TEST-UNIT-007]]、[[TESTSPEC:TEST-UNIT-008]]、[[TESTSPEC:TEST-UNIT-009]]、[[TESTSPEC:TEST-UNIT-010]]、[[TESTSPEC:TEST-UNIT-011]]、[[TESTSPEC:TEST-UNIT-012]]、[[TESTSPEC:TEST-UNIT-013]]、[[TESTSPEC:TEST-UNIT-014]]、[[TESTSPEC:TEST-UNIT-015]]、[[TESTSPEC:TEST-UNIT-111]]、[[TESTSPEC:TEST-UNIT-112]]、[[TESTSPEC:TEST-UNIT-113]]、[[TESTSPEC:TEST-UNIT-114]]、[[TESTSPEC:TEST-UNIT-115]]、[[TESTSPEC:TEST-UNIT-116]]、[[TESTSPEC:TEST-UNIT-085]]

#### REQ-VALID-003（軸可動範囲による生成可否）

計算された軸指令値がREQ-INPUT-005で入力された可動範囲を超える場合、ソフトウェアは軸種別に応じて以下のように処理しなければならない。

- XまたはYの並進軸が可動範囲を超える場合：警告を表示し、可動範囲端に飽和させたうえでシミュレーションおよびGコード生成を許可する。
- ZまたはAの回転軸が可動範囲を超える場合：エラーを表示し、当該軸を飽和させず、シミュレーションおよびGコード生成を禁止する。

### 3.3 座標変換

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]、[[ARCH:UC-04]]、[[ARCH:UC-05]]、[[ARCH:UC-06]]
- 製品コード: [[API:limits.LimitEvaluator.evaluate]]、[[API:controller.CalibrationController.can_generate]]、[[API:gui.MainWindow._update_action_state]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-047]]、[[TESTSPEC:TEST-UNIT-054]]、[[TESTSPEC:TEST-UNIT-055]]、[[TESTSPEC:TEST-UNIT-056]]、[[TESTSPEC:TEST-UNIT-057]]、[[TESTSPEC:TEST-UNIT-087]]、[[TESTSPEC:TEST-UNIT-088]]

#### REQ-TRANS-001（回転モデル）

実機構は、ピッチ回転後にピトー管軸周りのロール回転を行うものとして計算しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:transform.AngleTransformer.transform]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-025]]

#### REQ-TRANS-002（AoA/AoSから実軸角への変換） { #req-trans-002 }

ソフトウェアは、入力されたAoA=α、AoS=βを再現するよう、実ピッチ角θおよび実ロール角φを次式で求めなければならない。

$$
u=\tan(\alpha), \qquad v=\tan(\beta)
$$

$$
r=\sqrt{u^2+v^2}
$$

基本解は、

$$
\theta=\arctan(r)
$$

$$
\phi=\mathrm{atan2}(v,u)
$$

とする。

算出した実ピッチ角および実ロール角は、上記式から得られる理論値に対して **絶対誤差0.001 deg以内** でなければならない。

同一のAoA/AoSを表す別解が存在する場合は候補解を生成し、可動範囲および前較正点からの連続性を考慮して解を選択しなければならない。

AoA=AoS=0 degの場合、実ピッチ角は0 degで一意とし、実ロール角は任意とする。この場合、前較正点が存在すれば前較正点の実ロール角を保持し、前較正点が存在しない初期点ではA軸可動範囲の中央値を用いなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:transform.AngleTransformer.transform]]、[[API:transform.AngleTransformer._generate_equivalent_solutions]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-025]]、[[TESTSPEC:TEST-UNIT-026]]、[[TESTSPEC:TEST-UNIT-027]]、[[TESTSPEC:TEST-UNIT-028]]、[[TESTSPEC:TEST-UNIT-029]]、[[TESTSPEC:TEST-UNIT-030]]、[[TESTSPEC:TEST-UNIT-031]]、[[TESTSPEC:TEST-UNIT-032]]、[[TESTSPEC:TEST-UNIT-040]]、[[TESTSPEC:TEST-UNIT-060]]、[[TESTSPEC:TEST-UNIT-137]]、[[TESTSPEC:TEST-UNIT-138]]

#### REQ-TRANS-003（解の選択）

複数の等価な変換解が存在する場合、ソフトウェアは以下の優先順位で解を選択しなければならない。

1. Z/Aの可動範囲内である
2. 前の較正点に対して角度変化が連続している
3. 前の較正点からのZ/A総移動量が小さい
4. ロール角の絶対値が小さい

AoA=AoS=0 degでは、実ピッチ角を0 degとし、前較正点が存在する場合は前較正点の実ロール角を選択する。前較正点が存在しない場合は、A軸可動範囲の中央値を初期ロール角として選択する。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:transform.AngleTransformer._select_solution]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-036]]、[[TESTSPEC:TEST-UNIT-037]]、[[TESTSPEC:TEST-UNIT-038]]、[[TESTSPEC:TEST-UNIT-039]]、[[TESTSPEC:TEST-UNIT-040]]、[[TESTSPEC:TEST-UNIT-137]]、[[TESTSPEC:TEST-UNIT-138]]

#### REQ-TRANS-004（角度の連続性）

ロール角は、不要な±360 deg相当のジャンプが発生しないよう、前の較正点に近い等価角へunwrapしなければならない。

### 3.4 XY補正

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:transform.AngleTransformer._unwrap_angle]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-033]]、[[TESTSPEC:TEST-UNIT-034]]、[[TESTSPEC:TEST-UNIT-035]]、[[TESTSPEC:TEST-UNIT-064]]、[[TESTSPEC:TEST-UNIT-137]]

#### REQ-POS-001（先端位置補正）

ピッチ回転中心からピトー管先端までの基準姿勢の距離をLx、Lyとし、実ピッチ角をθとする。

回転後の先端位置は次式で計算しなければならない。

$$
x_{tip}=L_x\cos\theta-L_y\sin\theta
$$

$$
y_{tip}=L_x\sin\theta+L_y\cos\theta
$$

ピトー管先端を風洞中心に保持するための並進指令値は、

$$
X=L_x-x_{tip}
$$

$$
Y=L_y-y_{tip}
$$

とする。

算出したXおよびY指令値は、上記式から得られる理論値に対して **絶対誤差0.001 mm以内** でなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:positioning.PositionCompensator.calculate_xy]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-041]]、[[TESTSPEC:TEST-UNIT-042]]、[[TESTSPEC:TEST-UNIT-043]]、[[TESTSPEC:TEST-UNIT-044]]、[[TESTSPEC:TEST-UNIT-045]]、[[TESTSPEC:TEST-UNIT-060]]、[[TESTSPEC:TEST-UNIT-065]]

#### REQ-POS-002（ロールによる位置変化）

実ロール軸はピトー管軸上にあるため、ロール回転はピトー管先端位置に影響しないものとして扱う。

### 3.5 可動範囲と飽和

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:positioning.PositionCompensator.calculate_xy]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-046]]

#### REQ-LIMIT-001（並進軸の飽和）

計算されたXまたはY指令値が入力された可動範囲を超えた場合、ソフトウェアは該当するX/Y指令値を最小値または最大値に飽和させなければならない。

X/Yの飽和が発生しても、Z/Aが可動範囲内であればシミュレーションおよびGコード生成を継続できなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:limits.LimitEvaluator.evaluate]]、[[API:limits.LimitEvaluator._saturate_translation]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-047]]、[[TESTSPEC:TEST-UNIT-048]]、[[TESTSPEC:TEST-UNIT-049]]、[[TESTSPEC:TEST-UNIT-050]]、[[TESTSPEC:TEST-UNIT-051]]、[[TESTSPEC:TEST-UNIT-058]]、[[TESTSPEC:TEST-UNIT-063]]、[[TESTSPEC:TEST-UNIT-065]]、[[TESTSPEC:TEST-UNIT-075]]、[[TESTSPEC:TEST-UNIT-087]]、[[TESTSPEC:TEST-UNIT-091]]、[[TESTSPEC:TEST-UNIT-125]]

#### REQ-LIMIT-002（並進軸の飽和警告）

X/Yの飽和が発生した場合、ソフトウェアは非モーダルな警告を表示しなければならない。警告には、理想的なピトー管先端位置からのX方向およびY方向の最大逸脱量をmm単位で表示し、合成距離は表示しない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:limits.LimitEvaluator.evaluate]]、[[API:calibration_service.CalibrationService.build_plan]]、[[API:gui.MainWindow._update_plan_status]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-052]]、[[TESTSPEC:TEST-UNIT-053]]、[[TESTSPEC:TEST-UNIT-061]]、[[TESTSPEC:TEST-UNIT-063]]、[[TESTSPEC:TEST-UNIT-103]]

#### REQ-LIMIT-003（回転軸の範囲超過）

計算されたZまたはA指令値が入力された可動範囲を超えた場合、ソフトウェアは該当指令値を飽和させてはならない。

Z/Aのいずれかが可動範囲を超える較正点が1点でも存在する間、ソフトウェアはエラー状態とし、シミュレーションおよびGコード生成を実行できない状態にしなければならない。

### 3.6 較正点と走査順序

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:limits.LimitEvaluator.evaluate]]、[[API:limits.LimitEvaluator._rotation_in_range]]、[[API:controller.CalibrationController.can_generate]]、[[API:gui.MainWindow._update_plan_status]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-054]]、[[TESTSPEC:TEST-UNIT-055]]、[[TESTSPEC:TEST-UNIT-056]]、[[TESTSPEC:TEST-UNIT-057]]、[[TESTSPEC:TEST-UNIT-058]]、[[TESTSPEC:TEST-UNIT-059]]、[[TESTSPEC:TEST-UNIT-062]]、[[TESTSPEC:TEST-UNIT-088]]、[[TESTSPEC:TEST-UNIT-092]]、[[TESTSPEC:TEST-UNIT-125]]、[[TESTSPEC:TEST-UNIT-104]]

#### REQ-SCAN-001（較正点生成）

ソフトウェアは、AoAおよびAoSの範囲と点数から、両端を含む等間隔の較正点列を生成しなければならない。

入力値が有効な場合、AoA/AoSの範囲または点数が変更されるたびに、較正点列および変換後の実軸指令値をリアルタイムで自動再生成しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]、[[ARCH:UC-04]]
- 製品コード: [[API:scan.ScanPlanner.generate_points]]、[[API:controller.CalibrationController.on_settings_changed]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-017]]、[[TESTSPEC:TEST-UNIT-018]]、[[TESTSPEC:TEST-UNIT-019]]、[[TESTSPEC:TEST-UNIT-023]]、[[TESTSPEC:TEST-UNIT-024]]、[[TESTSPEC:TEST-UNIT-060]]、[[TESTSPEC:TEST-UNIT-084]]

#### REQ-SCAN-002（基本走査）

較正点は、ピッチ方向の移動回数を少なくするため、AoAを外側ループ、AoSを内側ループとして生成しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]、[[ARCH:UC-04]]
- 製品コード: [[API:scan.ScanPlanner.generate_points]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-020]]、[[TESTSPEC:TEST-UNIT-024]]、[[TESTSPEC:TEST-UNIT-064]]

#### REQ-SCAN-003（蛇行走査）

「蛇行走査を使用」が有効な場合、AoSの走査方向をAoA行ごとに反転しなければならない。

### 3.7 Gコード生成

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]、[[ARCH:UC-04]]
- 製品コード: [[API:scan.ScanPlanner.generate_points]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-021]]、[[TESTSPEC:TEST-UNIT-022]]、[[TESTSPEC:TEST-UNIT-064]]

#### REQ-GCODE-001（ファイル形式）

Gコードは`.nc`形式で保存できなければならない。保存先とファイル名はWindowsのファイル保存ダイアログで指定する。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-06]]
- 製品コード: [[API:repositories.GCodeRepository.save]]、[[API:gui.MainWindow._on_generate_gcode]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-082]]、[[TESTSPEC:TEST-UNIT-083]]、[[TESTSPEC:TEST-UNIT-110]]

#### REQ-GCODE-002（ヘッダ）

生成Gコードには、少なくとも以下を含めなければならない。

```gcode
; User initialization G-code
<読み込んだ初期化Gコード>

; Homing
$H

G21
G90
G94
```

原点復帰Gコード用の個別入力欄は設けない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-06]]
- 製品コード: [[API:gcode.GCodeGenerator._format_header]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-066]]、[[TESTSPEC:TEST-UNIT-067]]

#### REQ-GCODE-003（較正点指令）

各較正点では、X、Y、Z、Aを1行の同時指令として出力し、REQ-INPUT-004で入力された合成送り速度を`F`ワードとして指定しなければならない。GコードのG番号は2桁ゼロ埋め表記とし、少なくとも移動指令は`G01`、保持指令は`G04`として出力しなければならない。

Gコードへ出力する浮動小数点値は、小数点以下6桁で表記しなければならない。

```gcode
G01 X... Y... Z... A... F...
G04 P3.000000
```

保持時間の単位は秒とする。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-06]]
- 製品コード: [[API:gcode.GCodeGenerator._format_point]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-068]]、[[TESTSPEC:TEST-UNIT-069]]、[[TESTSPEC:TEST-UNIT-070]]、[[TESTSPEC:TEST-UNIT-071]]、[[TESTSPEC:TEST-UNIT-075]]

#### REQ-GCODE-004（コメント）

コメント出力が有効な場合、各較正点にAoA、AoS、実軸指令値、およびX/Y飽和状態をコメントとして出力する。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-06]]
- 製品コード: [[API:gcode.GCodeGenerator._format_point]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-072]]、[[TESTSPEC:TEST-UNIT-073]]

#### REQ-GCODE-005（終了位置）

Gコードの終了時は、最終較正点に留まるものとし、原点復帰や初期位置への復帰は行わない。

### 3.8 シミュレーション

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-06]]
- 製品コード: [[API:gcode.GCodeGenerator.generate]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-074]]

#### REQ-SIM-001（任意実行）

シミュレーションは任意実行とし、シミュレーションを実行していなくても、入力値およびZ/A可動範囲の検証に合格していればGコードを生成できなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:gui.MainWindow._on_simulate]]、[[API:controller.CalibrationController.can_generate]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-109]]

#### REQ-SIM-002（再生時間）

シミュレーションは、較正点保持時間を再現せず、全体を約10秒で再生する。実際のGコードの保持時間はシミュレーション時間に反映しない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationController.start]]、[[API:simulation.SimulationController._frame_at]]、[[API:simulation.SimulationView.start_animation]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-093]]、[[TESTSPEC:TEST-UNIT-094]]、[[TESTSPEC:TEST-UNIT-095]]、[[TESTSPEC:TEST-UNIT-096]]

#### REQ-SIM-003（表示）

シミュレーション画面は、以下の2画面を同時に表示する。

- 横面図：ピッチ角、X、Yを確認する図。ピッチ回転中心から基準姿勢におけるY方向距離Lyだけ延び、その端からピトー管軸方向へX方向距離Lxだけ延びるL字形状として模式表示し、このL字形状全体を実ピッチ角Zに応じて回転表示しなければならない。ピトー管軸方向はLx側線分の先端に矢印で示す。Lx、Ly、ピッチ回転中心、先端等の説明文字、およびLx/Lyを示す寸法矢印は表示しない。
- 正面図：ピトー管軸周りのロール角を確認する図。ロール方向は、正面図の中心から外周へ向かう半径矢印で表示しなければならない。反対側まで延びる直径線、角度を示す円弧、および方向を説明する文字注記は表示しない。

過度に詳細な3Dモデルは使用せず、抽象化した装置表示とする。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationView.initialize]]、[[API:simulation.SimulationView._calculate_side_limits]]、[[API:simulation.SimulationView._configure_side_axes]]、[[API:simulation.SimulationView._configure_front_axes]]、[[API:simulation.SimulationView.render_frame]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-097]]、[[TESTSPEC:TEST-UNIT-098]]

#### REQ-SIM-004（状態表示）

シミュレーション画面には、現在の較正点番号、AoA、AoS、X、Y、Z、A、可動範囲状態、再生進捗を表示する。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationView.render_frame]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-099]]

#### REQ-SIM-005（較正点マップ表示）

シミュレーション画面は、シミュレーション対象となる全較正点を、AoAを縦軸、AoSを横軸とした2次元較正点マップとして表示しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationView.initialize]]、[[API:simulation.SimulationView._calculate_calibration_limits]]、[[API:simulation.SimulationView._configure_calibration_axes]]、[[API:simulation.SimulationView._draw_calibration_map]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-122]]

#### REQ-SIM-006（現在較正点の強調表示）

シミュレーション実行中、ソフトウェアは現在の横面図および正面図が示す較正点と同じ較正点を、較正点マップ上でその他の較正点と異なる色により強調表示しなければならない。

較正点が切り替わった場合、強調表示する点も同じタイミングで更新しなければならない。

現在較正点を示すための凡例および「現在較正中」等の文字注記は表示しない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationView.render_frame]]、[[API:simulation.SimulationView._update_current_calibration_point]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-123]]

#### REQ-SIM-007（再生開始）

シミュレーション開始時、シミュレーションは先頭の較正点から再生を開始しなければならない。

開始時の状態は再生中とし、操作ボタンには一時停止ボタンを表示しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationController.start]]、[[API:simulation.SimulationView.start_animation]]、[[API:simulation.SimulationView.set_playback_state]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-126]]

#### REQ-SIM-008（一時停止）

再生中に一時停止ボタンを押した場合、シミュレーションは現在の較正点を保持したまま停止しなければならない。

一時停止中は、操作ボタンに再生ボタンを表示しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationController.pause]]、[[API:simulation.SimulationView._on_play_pause]]、[[API:simulation.SimulationView.set_playback_state]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-127]]

#### REQ-SIM-009（再生再開）

一時停止中に再生ボタンを押した場合、現在位置から再生を再開しなければならない。

ただし、最終較正点で停止している場合は、先頭の較正点へ移動して再生を開始しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationController.resume]]、[[API:simulation.SimulationController.restart_from_beginning]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-128]]、[[TESTSPEC:TEST-UNIT-133]]

#### REQ-SIM-010（シーク）

シークバーをドラッグすることにより、任意の較正点へ移動できなければならない。

シーク位置は連続した時間位置ではなく、較正点単位で決定しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationView._on_seek]]、[[API:simulation.SimulationController.seek_to_point]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-129]]

#### REQ-SIM-011（シーク時の自動一時停止）

再生中にシークバーの操作を開始した場合、シミュレーションは自動的に一時停止しなければならない。

シーク操作中および操作終了後は、選択された較正点を表示し、再生ボタンを表示しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationController.pause]]、[[API:simulation.SimulationView._on_seek]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-130]]

#### REQ-SIM-012（シーク位置の即時反映）

一時停止中またはシーク操作中にシーク位置が変更された場合、以下の表示を選択された較正点へ即座に更新しなければならない。

- 横面図
- 正面図
- 較正点マップ上の現在点強調
- 現在較正点番号
- AoA、AoS、X、Y、Z、A
- 可動範囲状態
- 「現在の較正点 / 全較正点」の進捗表示

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationController.seek_to_point]]、[[API:simulation.SimulationView.render_frame]]、[[API:simulation.SimulationView._update_seek_slider]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-131]]

#### REQ-SIM-013（再生完了）

最終較正点の表示が完了した場合、シミュレーションは自動的に停止し、最終較正点を表示した状態で待機しなければならない。

再生完了後に自動的に先頭へ戻って再生してはならない。

再生完了後は再生ボタンを表示しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationController.on_animation_complete]]、[[API:simulation.SimulationView.show_final_state]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-132]]

#### REQ-SIM-014（既存プログレスバーの置換）

既存のプログレスバーはシークバーへ置き換えなければならない。

既存プログレスバーとシークバーを同時に表示してはならない。

シークバーは、現在の較正点および全較正点に対する進捗を表すものとする。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationView.initialize]]、[[API:simulation.SimulationView._update_seek_slider]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-134]]、[[TESTSPEC:TEST-UNIT-136]]

#### REQ-SIM-015（シークバー操作性）

シークバーは、ドラッグ操作しやすい十分な大きさのつまみを持たなければならない。

シークバーは、マウスによるつまみのドラッグに加えて、トラック上のクリックでも該当位置へ移動できることが望ましい。

シークバーは、較正点単位で操作できなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationView.initialize]]、[[API:simulation.SimulationView._on_seek]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-134]]

#### REQ-SIM-016（操作ボタン表示）

シミュレーション画面には、シークバーの横に再生状態操作ボタンを1個配置しなければならない。

ボタン表示は状態に応じて以下のとおり切り替える。

| 状態 | ボタン表示 | 押下時の動作 |
|---|---|---|
| 再生中 | 一時停止「Ⅱ」 | 現在位置で一時停止 |
| 一時停止中 | 再生「▶」 | 現在位置から再生再開 |
| 最終位置で停止中 | 再生「▶」 | 先頭へ移動して再生開始 |

専用の巻き戻しボタンおよび時間単位のスキップボタンは設けない。

### 3.9 GUI

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-05]]
- 製品コード: [[API:simulation.SimulationView.set_playback_state]]、[[API:simulation.SimulationView._on_play_pause]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-135]]

#### REQ-GUI-001（言語）

GUIの表示言語は日本語とする。ただし、軸名、単位、AoA、AoS、Gコードなどの技術用語は英字表記を併記してよい。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]、[[ARCH:UC-02]]、[[ARCH:UC-03]]、[[ARCH:UC-04]]、[[ARCH:UC-05]]、[[ARCH:UC-06]]
- 製品コード: [[API:gui.MainWindow._build_widgets]]、[[API:map_view.CalibrationMapView._configure_matplotlib_font]]、[[API:simulation.SimulationView._configure_matplotlib_font]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-124]]、[[TESTSPEC:TEST-UNIT-100]]

#### REQ-GUI-002（較正点マップ）

GUIは、AoAを縦軸、AoSを横軸とした2次元較正点マップを表示しなければならない。

X/Y飽和点は通常点と異なる表示とし、Z/A可動範囲超過点は生成禁止エラーであることが識別できる表示としなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]
- 製品コード: [[API:map_view.CalibrationMapView.render]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-090]]、[[TESTSPEC:TEST-UNIT-091]]、[[TESTSPEC:TEST-UNIT-092]]、[[TESTSPEC:TEST-UNIT-125]]

#### REQ-GUI-003（設定ファイル）

ユーザーは、入力条件およびオプションをCSV形式の設定ファイルへ保存し、後から読み込めなければならない。

設定CSVにはスキーマバージョン番号を設けない。

設定CSVの読み込み時に、必須項目欠損、空欄、構造不正、数値変換不能、ファイルI/Oエラー等によって必要な値を取得できない場合、ソフトウェアは未処理例外によって終了してはならない。

設定CSVの読み込みに失敗した場合、読み込み途中の値を部分的に適用してはならず、読み込み前の設定および較正計画を維持しなければならない。

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-03]]、[[ARCH:UC-04]]
- 製品コード: [[API:gui.MainWindow._on_save_settings]]、[[API:gui.MainWindow._on_load_settings]]、[[API:repositories.SettingsRepository.save/load]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-076]]、[[TESTSPEC:TEST-UNIT-077]]、[[TESTSPEC:TEST-UNIT-078]]、[[TESTSPEC:TEST-UNIT-079]]、[[TESTSPEC:TEST-UNIT-117]]、[[TESTSPEC:TEST-UNIT-118]]、[[TESTSPEC:TEST-UNIT-119]]、[[TESTSPEC:TEST-UNIT-120]]、[[TESTSPEC:TEST-UNIT-089]]、[[TESTSPEC:TEST-UNIT-107]]、[[TESTSPEC:TEST-UNIT-108]]、[[TESTSPEC:TEST-UNIT-121]]

#### REQ-GUI-004（操作ボタン）

GUIには少なくとも以下の操作ボタンを設ける。

- シミュレーション
- Gコード生成
- 設定保存
- 設定読込

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-02]]、[[ARCH:UC-03]]、[[ARCH:UC-04]]、[[ARCH:UC-05]]、[[ARCH:UC-06]]
- 製品コード: [[API:gui.MainWindow._build_widgets]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-100]]、[[TESTSPEC:TEST-UNIT-107]]、[[TESTSPEC:TEST-UNIT-108]]、[[TESTSPEC:TEST-UNIT-109]]、[[TESTSPEC:TEST-UNIT-110]]

#### REQ-GUI-005（エラー・警告表示）

入力値エラーおよび軸可動範囲エラー・警告は、通常操作中にモーダルダイアログとして表示してはならない。

入力値エラーは該当フィールドの背景色のみを通常時と異なる色へ変更して示し、エラー理由をGUI内の既存の固定メッセージ領域に表示しなければならない。入力値エラーを示すために入力フィールドの枠色を変更してはならず、入力欄近傍等へ新たなメッセージ領域やアイコンを追加してGUIレイアウトを変更してはならない。X/Y範囲超過は警告、Z/A範囲超過は生成禁止エラーとして視覚的に区別しなければならない。

設定CSVの読み込み失敗を含むユーザー起点のファイル読込エラーは、アプリケーションを継続したまま、GUI上でユーザーにエラー内容を通知しなければならない。

生成禁止エラーが存在する間、シミュレーションおよびGコード生成ボタンは無効化しなければならない。

## 4. Gコード生成処理の基本フロー

1. GUI入力値の変更を検出する
2. 入力値をリアルタイム検証する
3. 入力値が有効ならAoA/AoSの較正点列を自動生成する
4. AoA/AoSからZ/Aを計算する
5. XY補正値を計算する
6. X/Y可動範囲を確認し、必要に応じて飽和させて警告を更新する
7. Z/A可動範囲を確認し、超過があれば生成禁止エラーを更新する
8. AoA/AoSマップおよびSummary表示を更新する
9. 生成禁止エラーがなければシミュレーションおよびGコード生成を有効化する
10. シミュレーションボタン押下時は約10秒のアニメーションを実行する
11. シミュレーション画面では、再生・一時停止・較正点単位のシークを操作できる
12. Gコード生成ボタン押下時は`.nc`保存ダイアログを表示する

## 5. レビュー対象の確認事項

- AoA/AoSから実ピッチ角・実ロール角への座標変換式と絶対誤差0.001 deg以内の精度
- XY補正式と絶対誤差0.001 mm以内の精度
- X/Y範囲超過時の飽和・警告と、Z/A範囲超過時の生成禁止
- 入力変更時のリアルタイム較正点生成、背景色による入力エラー強調、および固定メッセージ領域への理由表示
- Lx/Ly >= 0、保持時間0.1 s以上、Feed rate 1 unit/min以上
- 蛇行走査
- `$H`を固定でGコードへ出力すること
- 合成送り速度を`F`ワードとして出力すること
- Gコード浮動小数点値を小数点以下6桁で出力すること
- 保持時間を`G04 P<秒>`で出力すること
- G番号を2桁ゼロ埋め表記とすること
- CSV設定保存/読込と、読込失敗時の防御処理・部分適用禁止・ユーザー通知

**関連成果物**

- アーキテクチャ設計: [[ARCH:UC-01]]、[[ARCH:UC-02]]、[[ARCH:UC-03]]、[[ARCH:UC-04]]、[[ARCH:UC-05]]、[[ARCH:UC-06]]
- 製品コード: [[API:gui.MainWindow._on_gui_input_changed]]、[[API:gui.MainWindow._apply_validation_highlights]]、[[API:gui.MainWindow._update_validation_display]]、[[API:gui.MainWindow._update_plan_status]]、[[API:gui.MainWindow._update_action_state]]、[[API:controller.CalibrationController.can_generate]]
- テスト仕様: [[TESTSPEC:TEST-UNIT-101]]、[[TESTSPEC:TEST-UNIT-102]]、[[TESTSPEC:TEST-UNIT-103]]、[[TESTSPEC:TEST-UNIT-104]]、[[TESTSPEC:TEST-UNIT-105]]、[[TESTSPEC:TEST-UNIT-121]]
