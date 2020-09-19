#ifndef __GROVE_M5UNIT_ENV2_SAMPLER__
#define __GROVE_M5UNIT_ENV2_SAMPLER__

void __grove_m5unit_env2_sampler_read_temperature_barom(void * class_ptr);
void __grove_m5unit_env2_sampler_read_pressure(void * class_ptr);
void __grove_m5unit_env2_sampler_read_temperature_humid(void * class_ptr);
void __grove_m5unit_env2_sampler_read_humidity(void * class_ptr);
void __grove_m5unit_env2_sampler_read_altitude(void * class_ptr);

void __grove_m5unit_env2_sampler_register(void * sampler_ptr, void * class_ptr, char * grove_name);

#endif