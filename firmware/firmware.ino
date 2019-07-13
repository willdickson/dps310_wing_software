#include <Dps310.h>

// Constants
// -------------------------------------------------------------------------------------------------------
const int16_t NUM_SENSOR = 52;
const int16_t MEASUREMENT_RATE = 7;
const int16_t OVERSAMPLE_RATE = 1; 
const uint32_t SAMPLE_PERIOD = 20000;
const int16_t CS_PIN[NUM_SENSOR] = {
     0,  1, 2,   3,  4,  5,  6,  7,  8,  9, 10, 14, 15, 16, 17, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,30,
    31, 32, 33, 34, 35, 36, 37, 38, 39, 46, 45, 44, 43, 50, 49, 48, 42, 41, 40, 53, 52, 51, 57, 56, 55, 54
    }; 


// Function Prototypes
// --------------------------------------------------------------------------------------------------------
void new_sample_callback();
bool initialize_sensors();
void read_samples(float samples[NUM_SENSOR]);
void send_data(float samples[NUM_SENSOR]);

// Global Variables
// --------------------------------------------------------------------------------------------------------
Dps310 sensor[NUM_SENSOR]; 
IntervalTimer sampleTimer;
volatile bool new_sample_flag = false;


// --------------------------------------------------------------------------------------------------------
// setup function
// 
// Called when firmware starts.  Used for initialization of hardware, etc.
//
//----------------------------------------------------------------------------------------------------------
void setup()
{
    Serial.begin(115200);
    bool ok = initialize_sensors();
    if (!ok) 
    {
        Serial.println("error initializing sensors");
        while(true) {}

    }
    sampleTimer.begin(new_sample_callback, SAMPLE_PERIOD);
}



//----------------------------------------------------------------------------------------------------------
// loop function
//
// Called over and over again in a loop. Used for taking actions, etc.
//
// ---------------------------------------------------------------------------------------------------------
void loop()
{
    static bool send_flag = false; 

    while (Serial.available() > 0)
    {
        uint8_t cmd = Serial.read();
        switch (cmd)
        {
            case 'b':
                send_flag = true;
                break;

            case 'e':
                send_flag = false; 
                break;

            default:
                break;
        }
    }
    float pressure_samples[NUM_SENSOR];
    if (new_sample_flag) 
    {
        new_sample_flag = false;
        read_samples(pressure_samples);
        if (send_flag)
        {
            send_data(pressure_samples);
        }
    }
}


//----------------------------------------------------------------------------------------------------------
// new_sample_callback
//
// Interrupt service routine called on timer or pin interrupt. Used to set flag indicating that a new set
// of samples should be acquired from the sensors.
//
// ---------------------------------------------------------------------------------------------------------
void new_sample_callback()
{
    new_sample_flag = true;
}


// ---------------------------------------------------------------------------------------------------------
// initialize sensors
// 
// Setups SPI comminications with sensors and sets sensor measurement mode.
// 
// ---------------------------------------------------------------------------------------------------------
bool initialize_sensors()
{
    bool ok = true;

    // Setup SPI communications for sensors
    for (int16_t i=0; i< NUM_SENSOR; i++)
    {
        sensor[i].begin(SPI, CS_PIN[i]);
    }

    // Put sensors into continuous measurement mode
    for (int16_t i=0; i< NUM_SENSOR; i++) 
    {
        int16_t ret = sensor[i].startMeasurePressureCont(MEASUREMENT_RATE, OVERSAMPLE_RATE);
        if (ret != 0)
        {
            ok = false;
        }
    }
    return ok;
}



// --------------------------------------------------------------------------------------------------------
// read_samples
// 
// Read a set of samples from the sensors.
//
// ---------------------------------------------------------------------------------------------------------
void read_samples(float samples[NUM_SENSOR]) 
{
    for (int16_t i=0; i<NUM_SENSOR; i++)
    {
        uint8_t pressure_count = 20;
        float pressure[pressure_count];

        uint8_t temperature_count = 20;
        float temperature[temperature_count];

        int16_t ret = sensor[i].getContResults(temperature, temperature_count, pressure, pressure_count);
        if (ret !=0 )
        {
            samples[i] = -1.0;
        }
        if (pressure_count == 0)
        {
            samples[i] = 0.0;
        }
        else
        {
            samples[i] = pressure[pressure_count-1];
        }
    }
}


// -----------------------------------------------------------------------------------------------------------
// send_data
//
// Sends sensor data to host PC via USB/Serial
//
// -----------------------------------------------------------------------------------------------------------
void send_data(float samples[NUM_SENSOR])
{
    for (int16_t i=0; i<NUM_SENSOR; i++)
    {
        Serial.print(samples[i]);
        if (i < NUM_SENSOR -1)
        {   
            Serial.print(",");
        }
    }
    Serial.println();
}


