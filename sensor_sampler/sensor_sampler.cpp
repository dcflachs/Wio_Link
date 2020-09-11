/*
 * sensor_sampler.cpp
 *
 * Author     : dcflachs
 */

#include "sensor_sampler.h"
#include "rpc_stream.h"

#define SENSOR_SAMPLER_START_DELAY_MS 100
#define SENSOR_SAMPLER_SAMPLE_DELAY_MS 10

extern resource_t *p_first_resource;

static void timer_handler(void *para);

SensorSampler::SensorSampler()
{
    this->allow_sleep = true;
    this->timer = (TIMER_T *)malloc(sizeof(TIMER_T));
    this->p_current_resource = NULL;

    // suli_soft_timer_install(timer, SENSOR_SAMPLER_START_DELAY_MS, timer_handler, this, false);
}

bool SensorSampler::read_allow_sleep(bool *allow)
{
    *allow = this->allow_sleep;
    return true;
}

bool SensorSampler::write_allow_sleep(bool allow)
{
    this->allow_sleep = allow;
    return true;
}

void SensorSampler::_sample_function(void)
{
    if(this->p_current_resource == NULL)
    {
        if(p_first_resource)
        {
            this->p_current_resource = p_first_resource;
        }
        else
        {
            return;
        }
    }

    //TODO
    POST_EVENT(sample_grove_name, p_current_resource->grove_name);

    this->p_current_resource = this->p_current_resource->next;
    suli_soft_timer_install(timer, SENSOR_SAMPLER_SAMPLE_DELAY_MS, timer_handler, this, false);
}

static void timer_handler(void *para)
{
    SensorSampler *g = (SensorSampler *)para;
    g->_sample_function();
}

//Function Wrappers
static bool __write_allow_sleep_wrapper(void *class_ptr, char *method_name, void *input_pack)
{
    SensorSampler *grove = (SensorSampler *)class_ptr;
    uint8_t *arg_ptr = (uint8_t *)input_pack;
    bool allow;

    memcpy(&allow, arg_ptr, sizeof(bool)); arg_ptr += sizeof(bool);

    if(grove->write_allow_sleep(allow))
    {
        writer_print(TYPE_STRING, "\"OK\"");
        return true;
    }
    else
    {
        writer_print(TYPE_STRING, "\"");
        // writer_print(TYPE_STRING, grove->get_last_error());
        writer_print(TYPE_STRING, "ERROR");
        writer_print(TYPE_STRING, "\"");
        return false;
    }
}

static bool __read_allow_sleep_wrapper(void *class_ptr, char *method_name, void *input_pack)
{
    SensorSampler *grove = (SensorSampler *)class_ptr;
    uint8_t *arg_ptr = (uint8_t *)input_pack;
    bool allow;

    if(grove->read_allow_sleep(&allow))
    {
        writer_print(TYPE_STRING, "{");
        writer_print(TYPE_STRING, "\"allow\":");
        writer_print(TYPE_BOOL, &allow);
        writer_print(TYPE_STRING, "}");
        return true;
    }else
    {
        writer_print(TYPE_STRING, "\"");
        // writer_print(TYPE_STRING, grove->get_last_error());
        writer_print(TYPE_STRING, "ERROR");
        writer_print(TYPE_STRING, "\"");
        return false;
    }
}

// static bool __sensor_sampler_on_power_on(void *class_ptr, char *method_name, void *input_pack)
// {
//     SensorSampler *grove = (SensorSampler *)class_ptr;
//     return grove->on_power_on();
// }

// static bool __sensor_sampler_on_power_off(void *class_ptr, char *method_name, void *input_pack)
// {
//     SensorSampler *grove = (SensorSampler *)class_ptr;
//     return grove->on_power_off();
// }

//Resource Initialization 

SensorSampler *SensorSampler_ins;

static void SensorSampler_register_rpc_server_resources(void)
{
    uint8_t arg_types[MAX_INPUT_ARG_LEN];

    SensorSampler_ins = new SensorSampler();

    memset(arg_types, TYPE_NONE, MAX_INPUT_ARG_LEN);
    rpc_server_register_method("SensorSampler", "allow_sleep", METHOD_READ, __read_allow_sleep_wrapper, SensorSampler_ins, arg_types);

    memset(arg_types, TYPE_NONE, MAX_INPUT_ARG_LEN);
    arg_types[0] = TYPE_BOOL;
    rpc_server_register_method("SensorSampler", "allow_sleep", METHOD_WRITE, __write_allow_sleep_wrapper, SensorSampler_ins, arg_types);

    // memset(arg_types, TYPE_NONE, MAX_INPUT_ARG_LEN);
    // rpc_server_register_method("SensorSampler", "?poweron", METHOD_INTERNAL, __grove_example_on_power_on, SensorSampler_ins, arg_types);
    // memset(arg_types, TYPE_NONE, MAX_INPUT_ARG_LEN);
    // rpc_server_register_method("SensorSampler", "?poweroff", METHOD_INTERNAL, __grove_example_on_power_off, SensorSampler_ins, arg_types);

    SensorSampler_ins->attach_event_reporter_for_sample_bool_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_float_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_grove_name(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_int16_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_int32_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_int8_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_int_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_string_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_uint16_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_uint32_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_uint8_value(rpc_server_event_report);
    SensorSampler_ins->attach_event_reporter_for_sample_value_name(rpc_server_event_report);
}