#include "grove_moisture_seesaw_sampler.h"
#include "grove_moisture_seesaw.h"
#include "sensor_sampler.h"
#include "wio.h"

void __grove_moisture_seesaw_sampler_read_temperature(void * class_ptr)
{
    GroveMoistureSeesaw *grove = (GroveMoistureSeesaw *)class_ptr;
    float temperature;

    wio.postEvent("sensor_sampler_function", "temperature");
    if(grove->read_temperature(&temperature))
    {
        wio.postEvent("sensor_sampler_value", temperature);
    }
    else
    {
        wio.postEvent("sensor_sampler_status", "failed");
    }
}

void __grove_moisture_seesaw_sampler_read_moisture(void * class_ptr)
{
    GroveMoistureSeesaw *grove = (GroveMoistureSeesaw *)class_ptr;
    uint16_t moisture;

    wio.postEvent("sensor_sampler_function", "moisture");
    if(grove->read_moisture(&moisture))
    {
        wio.postEvent("sensor_sampler_value", moisture);
    }
    else
    {
        wio.postEvent("sensor_sampler_status", "failed");
    }
}