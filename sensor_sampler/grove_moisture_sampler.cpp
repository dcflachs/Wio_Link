#include "grove_moisture_sampler.h"
#include "grove_moisture_class.h"
#include "sensor_sampler.h"
#include "wio.h"

void __grove_moisture_sampler_read_moisture(void * class_ptr)
{
    GroveMoisture *grove = (GroveMoisture *)class_ptr;
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

void __grove_moisture_sampler_register(void * sampler_ptr, void * class_ptr, char * grove_name)
{
    SensorSampler *sampler = (SensorSampler *)sampler_ptr;

    sampler->register_start_resource(__grove_moisture_sampler_read_moisture, class_ptr, grove_name);
}