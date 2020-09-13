/*
 * sensor_sampler.cpp
 *
 * Author     : dcflachs
 */

#include "sensor_sampler.h"
#include "rpc_stream.h"
#include "wio.h"
#include "Arduino.h"

#define SENSOR_SAMPLER_START_DELAY_MS 500
#define SENSOR_SAMPLER_SAMPLE_DELAY_MS 100

extern resource_t *p_first_resource;

static void timer_handler(void *para);

SensorSampler::SensorSampler()
{
    this->allow_sleep = true;
    this->timer = (TIMER_T *)malloc(sizeof(TIMER_T));
    this->p_current_resource = NULL;

    wio.registerVar("allow_sleep", this->allow_sleep);

    // wio.postEvent("sensor_sampler_start", true);
    suli_soft_timer_install(timer, SENSOR_SAMPLER_START_DELAY_MS, timer_handler, this, true);
}

void SensorSampler::_sample_function(void)
{
    if(this->p_current_resource == NULL)
    {
        if(p_first_resource)
        {
            this->p_current_resource = p_first_resource;
            suli_soft_timer_control_interval(timer, SENSOR_SAMPLER_SAMPLE_DELAY_MS);
        }
        else
        {
            timer->repeat = false;
            return;
        }
    }

    //TODO
    if(p_current_resource->rw == METHOD_READ)
    {
        wio.postEvent("sample_grove_name", p_current_resource->grove_name);
        wio.postEvent("sample_value_name", p_current_resource->method_name);
        // switch(p_current_resource->arg_types)
    }

    if(this->p_current_resource->next != NULL)
    {
        this->p_current_resource = this->p_current_resource->next;
    }
    else
    {
        this->p_current_resource = NULL;
        timer->repeat = false;

        uint32_t time = millis();
        wio.postEvent("sensor_sampler_uptime", time);
    }
}

static void timer_handler(void *para)
{
    SensorSampler *g = (SensorSampler *)para;
    g->_sample_function();
}