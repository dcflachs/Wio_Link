#include "grove_m5unit_env2_sampler.h"
#include "grove_m5unit_env2.h"
#include "sensor_sampler.h"
#include "wio.h"

void __grove_m5unit_env2_sampler_read_temperature_barom(void * class_ptr)
{
    GroveM5UnitENV2 *grove = (GroveM5UnitENV2 *)class_ptr;
    float temperature;

    wio.postEvent("sensor_sampler_function", "temperature_barom");
    if(grove->read_temperature_barom(&temperature))
    {
        wio.postEvent("sensor_sampler_value", temperature);
    }
    else
    {
        wio.postEvent("sensor_sampler_status", "failed");
    }
}

void __grove_m5unit_env2_sampler_read_pressure(void * class_ptr)
{
    GroveM5UnitENV2 *grove = (GroveM5UnitENV2 *)class_ptr;
    int32_t  pressure;

    wio.postEvent("sensor_sampler_function", "pressure");
    if(grove->read_pressure(&pressure))
    {
        wio.postEvent("sensor_sampler_value", pressure);
    }
    else
    {
        wio.postEvent("sensor_sampler_status", "failed");
    }
}

void __grove_m5unit_env2_sampler_read_temperature_humid(void * class_ptr)
{
    GroveM5UnitENV2 *grove = (GroveM5UnitENV2 *)class_ptr;
    float temperature;

    wio.postEvent("sensor_sampler_function", "temperature_humid");
    if(grove->read_temperature_humid(&temperature))
    {
        wio.postEvent("sensor_sampler_value", temperature);
    }
    else
    {
        wio.postEvent("sensor_sampler_status", "failed");
    }
}

void __grove_m5unit_env2_sampler_read_humidity(void * class_ptr)
{
    GroveM5UnitENV2 *grove = (GroveM5UnitENV2 *)class_ptr;
    float humidity;

    wio.postEvent("sensor_sampler_function", "humidity");
    if(grove->read_humidity(&humidity))
    {
        wio.postEvent("sensor_sampler_value", humidity);
    }
    else
    {
        wio.postEvent("sensor_sampler_status", "failed");
    }
}

void __grove_m5unit_env2_sampler_read_altitude(void * class_ptr)
{
    GroveM5UnitENV2 *grove = (GroveM5UnitENV2 *)class_ptr;
    float altitude;

    wio.postEvent("sensor_sampler_function", "altitude");
    if(grove->read_altitude(&altitude))
    {
        wio.postEvent("sensor_sampler_value", altitude);
    }
    else
    {
        wio.postEvent("sensor_sampler_status", "failed");
    }
}

void __grove_m5unit_env2_sampler_register(void * sampler_ptr, void * class_ptr, char * grove_name)
{
    SensorSampler *sampler = (SensorSampler *)sampler_ptr;

    sampler->register_last_resource(__grove_m5unit_env2_sampler_read_temperature_barom, class_ptr, grove_name);
    sampler->register_last_resource(__grove_m5unit_env2_sampler_read_pressure, class_ptr, grove_name);
    sampler->register_last_resource(__grove_m5unit_env2_sampler_read_temperature_humid, class_ptr, grove_name);
    sampler->register_last_resource(__grove_m5unit_env2_sampler_read_humidity, class_ptr, grove_name);
    sampler->register_last_resource(__grove_m5unit_env2_sampler_read_altitude, class_ptr, grove_name);
}
