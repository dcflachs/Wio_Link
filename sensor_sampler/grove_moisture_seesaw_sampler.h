#ifndef __GROVE_MOISTURE_SEESAW_SAMPLER__
#define __GROVE_MOISTURE_SEESAW_SAMPLER__

void __grove_moisture_seesaw_sampler_read_temperature(void * class_ptr);
void __grove_moisture_seesaw_sampler_read_moisture(void * class_ptr);

void __grove_moisture_seesaw_sampler_register(void * sampler_ptr, void * class_ptr, char * grove_name);

#endif