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

    bool read_allow_sleep(bool *allow);

    bool write_allow_sleep(bool allow);

    DEFINE_EVENT(sample_grove_name, SULI_EDT_STRING);
    DEFINE_EVENT(sample_value_name, SULI_EDT_STRING);

    DEFINE_EVENT(sample_bool_value, SULI_EDT_BOOL);
    DEFINE_EVENT(sample_uint8_value, SULI_EDT_UINT8);
    DEFINE_EVENT(sample_int8_value, SULI_EDT_INT8);
    DEFINE_EVENT(sample_uint16_value, SULI_EDT_UINT16);
    DEFINE_EVENT(sample_int16_value, SULI_EDT_INT16);
    DEFINE_EVENT(sample_uint32_value, SULI_EDT_UINT32);
    DEFINE_EVENT(sample_int32_value, SULI_EDT_INT32);
    DEFINE_EVENT(sample_int_value, SULI_EDT_INT);
    DEFINE_EVENT(sample_float_value, SULI_EDT_FLOAT);
    DEFINE_EVENT(sample_string_value, SULI_EDT_STRING);

    void _sample_function(void);

private:
    bool allow_sleep;
    TIMER_T *timer;
    resource_t *p_current_resource;
};

static void SensorSampler_register_rpc_server_resources(void);

#endif