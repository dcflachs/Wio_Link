/*
 * sensor_sampler.h
 *
 * Author     : dcflachs
 */
#ifndef __SENSOR_SAMPLER_H__
#define __SENSOR_SAMPLER_H__

#include "suli2.h"

typedef bool (*sampler_func_t)(void * class_ptr);

typedef struct sample_resource_s
{
    char               *grove_name;
    sampler_func_t      method_ptr;
    void               *class_ptr;

    struct sample_resource_s  *next;
}sample_resource_t;

class SensorSampler
{
public:
    SensorSampler();

    void register_start_resource(sampler_func_t func, void * class_ptr, char * grove_name);
    void register_end_resource(sampler_func_t func, void * class_ptr, char * grove_name);


    void start_sampling(void);
    void sample(void);

    bool allow_sleep;
    bool enabled;

private:
    TIMER_T *timer;
    sample_resource_t * p_first_resource;
    sample_resource_t * p_last_resource;
    sample_resource_t * p_current_resource;
    void register_resource(sampler_func_t func, void * class_ptr, char * grove_name, bool last);
};

#endif