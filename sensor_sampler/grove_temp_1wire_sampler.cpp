#include "grove_temp_1wire_sampler.h"
#include "grove_temp_1wire.h"
#include "sensor_sampler.h"
#include "wio.h"

void __grove_temp_1wire_sampler_read_temp(void * class_ptr)
{
    GroveTemp1Wire *grove = (GroveTemp1Wire *)class_ptr;
    float temperature;

    wio.postEvent("sensor_sampler_function", "temperature");
    if(grove->read_temp(&temperature))
    {
        wio.postEvent("sensor_sampler_value", temperature);
    }
    else
    {
        wio.postEvent("sensor_sampler_status", "failed");
    }
}

void __grove_temp_1wire_sampler_register(void * sampler_ptr, void * class_ptr, char * grove_name)
{
    SensorSampler *sampler = (SensorSampler *)sampler_ptr;

    sampler->register_start_resource(__grove_temp_1wire_sampler_read_temp, class_ptr, grove_name);
}