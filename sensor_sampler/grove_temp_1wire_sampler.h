#ifndef __GROVE_TEMP_1WIRE_SAMPLER__
#define __GROVE_TEMP_1WIRE_SAMPLER__

void __grove_temp_1wire_sampler_read_temp(void * class_ptr);
void __grove_temp_1wire_sampler_register(void * sampler_ptr, void * class_ptr, char * grove_name);

#endif