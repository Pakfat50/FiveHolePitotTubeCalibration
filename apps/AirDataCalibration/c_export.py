"""組込み用の共通C実装と、較正ごとに選べる係数ヘッダーを出力する。"""
import hashlib
from pathlib import Path
import re

import numpy as np


def install(path, content):
    """同じ内容は再利用し、既存の別内容は上書きしない。"""
    try:
        stream = path.open('xb')
    except FileExistsError:
        return path.read_bytes() == content
    try:
        with stream:
            stream.write(content)
    except OSError:
        path.unlink(missing_ok=True)
        raise
    return True


def export_c(directory, model, csv_path):
    model = np.asarray(model, dtype='<f8')
    if model.shape != (10, 3) or not np.isfinite(model).all():
        raise ValueError('有限の10項×3列の係数が必要です。')
    with np.errstate(over='ignore', under='ignore'):
        single = model.astype(np.float32)
    if not np.isfinite(single).all() or np.any((model != 0) & (single == 0)):
        raise ValueError('floatの範囲外の係数があります。')

    directory.mkdir(exist_ok=True, parents=True)
    for name in ('airdata.h', 'airdata.c'):
        source = Path(__file__).with_name('c_templates') / name
        if not install(directory / name, source.read_bytes()):
            raise ValueError(f'{name} の内容が共通実装と異なります。既存ファイルを確認してください。')

    digest = hashlib.sha256(model.tobytes()).hexdigest()
    match = re.fullmatch(r'cal_([0-9a-f]{4,64})', Path(csv_path).stem)
    prefix = match[1] if match else digest[:4]
    rows = ''.join('    {'+', '.join(f'{v:.8e}f' for v in row)+'},\n' for row in single)
    for extra in range(0, 65, 2):
        suffix = prefix + digest[:extra]
        guard = f'AIRDATA_CAL_{suffix.upper()}_H'
        header = (f'#ifndef {guard}\n#define {guard}\n#include "airdata.h"\n\n'
                  f'static const AirDataCalibration cal_{suffix} = {{{{\n{rows}}}}};\n\n#endif\n')
        path = directory / f'cal_{suffix}.h'
        if install(path, header.encode('ascii')):
            return path
    raise FileExistsError('係数ヘッダーのファイル名が衝突しました。')
