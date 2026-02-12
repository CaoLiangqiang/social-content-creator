const mongoose = require('mongoose');
const logger = require('../utils/logger');

const mongoConfig = {
  uri: process.env.MONGO_URI || 'mongodb://localhost:27017/social_content',
  options: {
    maxPoolSize: parseInt(process.env.MONGO_POOL_SIZE || '20'),
    minPoolSize: parseInt(process.env.MONGO_POOL_MIN || '5'),
    connectTimeoutMS: 10000,
    socketTimeoutMS: 45000,
    serverSelectionTimeoutMS: 5000,
  }
};

let isConnected = false;

async function connect() {
  if (isConnected) {
    logger.debug('MongoDB: Already connected');
    return mongoose.connection;
  }

  try {
    mongoose.set('strictQuery', true);
    
    await mongoose.connect(mongoConfig.uri, mongoConfig.options);
    isConnected = true;
    
    logger.info('MongoDB: Connected successfully', {
      host: mongoose.connection.host,
      port: mongoose.connection.port,
      database: mongoose.connection.name
    });
    
    mongoose.connection.on('error', (err) => {
      logger.error('MongoDB: Connection error', err);
      isConnected = false;
    });
    
    mongoose.connection.on('disconnected', () => {
      logger.warn('MongoDB: Disconnected');
      isConnected = false;
    });
    
    mongoose.connection.on('reconnected', () => {
      logger.info('MongoDB: Reconnected');
      isConnected = true;
    });
    
    return mongoose.connection;
  } catch (error) {
    logger.error('MongoDB: Connection failed', error);
    throw error;
  }
}

async function disconnect() {
  if (!isConnected) {
    return;
  }
  
  await mongoose.disconnect();
  isConnected = false;
  logger.info('MongoDB: Disconnected');
}

function getConnection() {
  return mongoose.connection;
}

function isConnectedToMongo() {
  return isConnected && mongoose.connection.readyState === 1;
}

async function testConnection() {
  try {
    if (!isConnectedToMongo()) {
      await connect();
    }
    
    await mongoose.connection.db.admin().ping();
    logger.info('MongoDB: Connection test successful');
    return true;
  } catch (error) {
    logger.error('MongoDB: Connection test failed', error);
    return false;
  }
}

module.exports = {
  connect,
  disconnect,
  getConnection,
  isConnectedToMongo,
  testConnection,
  mongoose
};
