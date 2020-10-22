/*
 * sensor_sampler.cpp
 *
 * Author     : dcflachs
 */

#include "sensor_sampler.h"
#include "wio.h"
#include "rpc_server.h"

extern "C"
{
#include "user_interface.h"
}

#define SENSOR_SAMPLER_RTC_MEM_BLOCK ((uint8_t) 96) 
#define SENSOR_SAMPLER_RTC_MEM_SENTINEL     0xC0FFEE01

#define SENSOR_SAMPLER_START_DELAY_MS 4000
#define SENSOR_SAMPLER_SAMPLE_DELAY_MS 100
#define SENSOR_SAMPLER_PRE_SLEEP_DELAY_MS 300
#define SENSOR_SAMPLER_SLEEP_DELAY_MS 10
#define SENSOR_SAMPLER_SLEEP_SPIN_MAX 50

#define SENSOR_SAMPLER_SAMPLE_TIME_S 900 //15 min
// #define SENSOR_SAMPLER_SAMPLE_TIME_S 60 //1 min

bool __plugin_pm_sleep(void *class_ptr, char *method_name, void *input_pack);
bool __plugin_pm_power_the_groves(void *class_ptr, char *method_name, void *input_pack);

static void timer_handler(void * data)
{
    SensorSampler * p_sampler = (SensorSampler *) data;
    if(p_sampler == NULL)
        return;

    if(p_sampler->enabled)
    {
        p_sampler->sample();
    }
}

SensorSampler::SensorSampler()
{
    this->timer = (TIMER_T *)malloc(sizeof(TIMER_T));
    this->p_first_resource = NULL;
    this->p_last_resource = NULL;
    this->p_current_resource = NULL;
    this->allow_sleep = true;
    this->enabled = true;
    this->ready_sleep = false;
    this->pre_sleep_counter = 0;
    this->sleep_time = SENSOR_SAMPLER_SAMPLE_TIME_S;
    
    system_rtc_mem_read(SENSOR_SAMPLER_RTC_MEM_BLOCK, &this->rtc_mem, sizeof(this->rtc_mem));
    if(this->rtc_mem.sentinel != SENSOR_SAMPLER_RTC_MEM_SENTINEL)
    {
        this->rtc_mem.sentinel = SENSOR_SAMPLER_RTC_MEM_SENTINEL;
        this->rtc_mem.last_uptime = 0;
        wio.postEvent("Debug", "Failed to load from RTC MEM");
    }

    wio.registerVar("allow_sleep", this->allow_sleep);
    wio.registerVar("sampler_enabled", this->enabled);
    wio.registerVar("sleep_time", this->sleep_time);
}

void SensorSampler::start_sampling(void)
{
    if(this->p_first_resource != NULL)
    {
        this->p_current_resource = this->p_first_resource;
        suli_soft_timer_install(this->timer, SENSOR_SAMPLER_START_DELAY_MS, timer_handler, this, true);
        wio.postEvent("Sensor Sampler State", "Start");
    }
}

void SensorSampler::sample(void)
{
    if((this->p_current_resource != NULL) && (this->enabled))
    {
        if(this->p_current_resource != NULL)
        {
            //Do the start_sampling
            // wio.postEvent("Sensor Sampler State", "Sample");
            wio.postEvent("sensor_sampler_grove", this->p_current_resource->grove_name);
            this->p_current_resource->method_ptr(this->p_current_resource->class_ptr);
        }

        if(this->p_current_resource == this->p_first_resource)
        {
            suli_soft_timer_control_interval(this->timer, SENSOR_SAMPLER_SAMPLE_DELAY_MS);
        }
        
        if(this->p_current_resource == this->p_last_resource)
        {
            if(this->rtc_mem.last_uptime != 0)
                wio.postEvent("sensor_sampler_uptime", this->rtc_mem.last_uptime);

            suli_soft_timer_control_interval(this->timer, SENSOR_SAMPLER_PRE_SLEEP_DELAY_MS);
            bool arg_pack[2] = {false, false};
            __plugin_pm_power_the_groves(NULL, NULL, arg_pack);
        }

        this->p_current_resource = this->p_current_resource->next;  
    }
    else
    {   
        if(!(this->ready_sleep))
        {
            suli_soft_timer_control_interval(this->timer, SENSOR_SAMPLER_SLEEP_DELAY_MS);
            this->ready_sleep = true;
            // wio.postEvent("sensor_sampler_current_uptime", (uint32_t)millis());
        }
        else
        {   
            if((rpc_server_event_queue_size() == 0) || (this->pre_sleep_counter++ > SENSOR_SAMPLER_SLEEP_SPIN_MAX))
            {
                this->timer->repeat = false; 
                // wio.postEvent("sensor_sampler_allow_sleep", this->allow_sleep);
                if(this->allow_sleep)
                {
                    this->rtc_mem.last_uptime = (uint32_t)millis();
                    system_rtc_mem_write(SENSOR_SAMPLER_RTC_MEM_BLOCK, &this->rtc_mem, sizeof(this->rtc_mem));
                    
                    uint32_t arg_pack[2] = {this->sleep_time, 0};
                    __plugin_pm_sleep(NULL, NULL, arg_pack);
                }
            }
        }
    }
}

void SensorSampler::register_resource(sampler_func_t func, void * class_ptr, char * grove_name, bool last)
{
    sample_resource_t * p_res = (sample_resource_t *) malloc(sizeof(sample_resource_t));
    if(p_res == NULL) return;

    p_res->class_ptr = class_ptr;
    p_res->grove_name = grove_name;
    p_res->method_ptr = func;
    p_res->next = NULL;

    if(this->p_first_resource == NULL)
    {
        this->p_first_resource = p_res;
        this->p_last_resource = p_res;
    }
    else if(last)
    {
        this->p_last_resource->next = p_res;
        this->p_last_resource = p_res;
    }
    else
    {
        p_res->next = this->p_first_resource;
        this->p_first_resource = p_res;
    }
}

void SensorSampler::register_start_resource(sampler_func_t func, void * class_ptr, char * grove_name)
{
    this->register_resource(func, class_ptr, grove_name, false);
}

void SensorSampler::register_end_resource(sampler_func_t func, void * class_ptr, char * grove_name)
{
    this->register_resource(func, class_ptr, grove_name, true);
}