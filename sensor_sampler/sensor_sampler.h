/*
 * sensor_sampler.h
 *
 * Author     : dcflachs
 */
#ifndef __SENSOR_SAMPLER_H__
#define __SENSOR_SAMPLER_H__

#include "suli2.h"
#include "rpc_server.h"

class SensorSampler
{
public:
    SensorSampler();

    void _sample_function(void);

    bool allow_sleep;
private:
    TIMER_T *timer;
    resource_t *p_current_resource;
};

static void SensorSampler_register(void);

#endif