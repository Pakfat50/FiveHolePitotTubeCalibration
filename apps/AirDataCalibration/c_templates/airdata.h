#ifndef AIRDATA_H
#define AIRDATA_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    /* Rows: 1, a, s, a*a, a*s, s*s, a*a*a, a*a*s, a*s*s, s*s*s.
       Columns: alpha [deg], beta [deg], q_ref / total. */
    float term[10][3];
} AirDataCalibration;

typedef struct {
    float alpha_deg;
    float beta_deg;
    float q_ref_pa;
} AirDataResult;

/* All three inputs are differential pressures in Pa. On failure, out is unchanged. */
bool airdata_estimate(const AirDataCalibration *cal, float aoa_pa, float aos_pa,
                      float total_pa, AirDataResult *out);

#ifdef __cplusplus
}
#endif
#endif
