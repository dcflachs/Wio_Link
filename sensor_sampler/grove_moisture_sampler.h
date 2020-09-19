#ifndef __GROVE_MOISTURE_SAMPLER__
#define __GROVE_MOISTURE_SAMPLER__

void __grove_moisture_sampler_read_moisture(void * class_ptr);

void __grove_moisture_sampler_register(void * sampler_ptr, void * class_ptr, char * grove_name);

#endif