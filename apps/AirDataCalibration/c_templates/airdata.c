#include "airdata.h"
#include <math.h>

bool airdata_estimate(const AirDataCalibration *cal, float aoa_pa, float aos_pa,
                      float total_pa, AirDataResult *out)
{
    if (!cal || !out || !isfinite(total_pa) || total_pa <= 0.0f ||
        !isfinite(aoa_pa) || !isfinite(aos_pa)) {
        return false;
    }

    const float a = aoa_pa / total_pa;
    const float s = aos_pa / total_pa;
    const float aa = a * a;
    const float ss = s * s;
    const float basis[10] = {1.0f, a, s, aa, a*s, ss, aa*a, aa*s, a*ss, ss*s};
    float value[3] = {0};
    for (int i = 0; i < 10; ++i) {
        for (int j = 0; j < 3; ++j) {
            value[j] += basis[i] * cal->term[i][j];
        }
    }
    value[2] *= total_pa;
    if (!isfinite(value[0]) || !isfinite(value[1]) || !isfinite(value[2])) {
        return false;
    }
    *out = (AirDataResult){value[0], value[1], value[2]};
    return true;
}
