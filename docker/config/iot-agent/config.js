/*
 * IoT Agent UltraLight - Configuration for Testing
 * =================================================
 * Minimal configuration for local integration testing.
 */

const config = {};

// MQTT Configuration
config.mqtt = {
    host: 'mosquitto',
    port: 1883,
    username: '',
    password: '',
    qos: 0,
    retain: false,
    retries: 5,
    retryTime: 5,
    keepalive: 60
};

// HTTP Transport
config.http = {
    port: 7896,
    timeout: 5000
};

// IoT Agent Core Configuration
config.iota = {
    logLevel: 'DEBUG',
    timestamp: true,

    // Orion Context Broker
    contextBroker: {
        host: 'orion',
        port: '1026',
        ngsiVersion: 'v2'
    },

    // IoT Agent Server
    server: {
        port: 4061
    },

    // Resource path
    defaultResource: '/iot/d',

    // Device Registry (MongoDB)
    deviceRegistry: {
        type: 'mongodb'
    },

    // MongoDB Configuration
    mongodb: {
        host: 'mongodb',
        port: '27017',
        db: 'iotagentul'
    },

    // Default service configuration
    service: 'openiot',
    subservice: '/',

    // Provider URL
    providerUrl: 'http://iotagent-ul:4061',

    // Device registration duration
    deviceRegistrationDuration: 'P20Y',

    // Default entity type
    defaultType: 'Thing',

    // Static types (empty for dynamic provisioning)
    types: {}
};

// Additional settings
config.autocast = true;
config.configRetrieval = false;
config.defaultKey = 'TEF';
config.defaultTransport = 'MQTT';

module.exports = config;
