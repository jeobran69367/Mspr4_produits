# RabbitMQ Connection Fix - Railway Deployment

## Overview

This document describes the fixes made to ensure reliable RabbitMQ connectivity on Railway and proper cross-service communication.

## Problem Statement

The original issue was that the application was not consistently connecting to RabbitMQ on Railway, and the message routing was not properly configured for cross-service communication (e.g., `produits.deleted.commandes`).

## Changes Made

### 1. Enhanced EventProducer (`app/events/producer.py`)

**Connection Improvements:**
- ✅ Railway environment variable priority: `RABBITMQ_PRIVATE_URL` > `RABBITMQ_URL` > constructed URL
- ✅ SSL/TLS support for `amqps://` connections
- ✅ Retry logic with exponential backoff (3 attempts)
- ✅ Connection state management
- ✅ Automatic reconnection on publish failures
- ✅ Heartbeat monitoring (30s)
- ✅ Proper connection timeouts (10s)

**Routing Key Format:**
- General events: `produits.{event_type}` (e.g., `produits.product.deleted`)
- Cross-service events: `produits.{event_type}.{target_service}` (e.g., `produits.product.deleted.commandes`)

**Health Check:**
- Added `health_check()` method for monitoring connection status
- Returns connection state, service name, and exchange info

### 2. Enhanced EventConsumer (`app/events/consumer.py`)

**Connection Improvements:**
- ✅ Same Railway URL priority as producer
- ✅ SSL/TLS support
- ✅ Retry logic with exponential backoff
- ✅ Message TTL (24 hours)
- ✅ Queue length limit (10,000 messages)
- ✅ QoS prefetch limit (10 messages)

**Health Check:**
- Added `health_check()` method
- Returns queue statistics including message count

### 3. Updated API Endpoints

**Products API (`app/api/v1/products.py`):**
- ✅ `POST /products/` - Publishes to general + commandes service
- ✅ `PUT /products/{id}` - Publishes to general + commandes service
- ✅ `DELETE /products/{id}` - Publishes to general + commandes + clients services

**Stock API (`app/api/v1/stock.py`):**
- ✅ `PUT /stock/{id}` - Publishes to general + commandes service
- ✅ `POST /stock/product/{id}/adjust` - Publishes to general + commandes service
- ✅ Low stock alerts - Published to general + commandes service

### 4. Enhanced Health Check Endpoint (`app/main.py`)

**GET /health:**
```json
{
  "status": "healthy",
  "service": "products",
  "rabbitmq": {
    "status": "healthy",
    "service": "produits",
    "rabbitmq": "connected",
    "exchange": "mspr.events"
  }
}
```

## Environment Variables

The application now supports the following Railway-specific environment variables:

| Variable | Priority | Description |
|----------|----------|-------------|
| `RABBITMQ_PRIVATE_URL` | 1 (Highest) | Railway private network URL (recommended) |
| `RABBITMQ_URL` | 2 | Public Railway URL or local URL |
| `RABBITMQ_HOST` | 3 | Individual components (fallback) |
| `RABBITMQ_PORT` | 3 | |
| `RABBITMQ_USERNAME` | 3 | |
| `RABBITMQ_PASSWORD` | 3 | |
| `RABBITMQ_NODENAME` | Info only | Railway provides this for reference |
| `SERVICE_NAME` | Required | Service identifier (default: "produits") |
| `RABBITMQ_EXCHANGE` | Required | Exchange name (default: "mspr.events") |

## Testing

### Test Connection

Run the connection test script:

```bash
python test_rabbitmq_connection.py
```

This will test:
- Producer connection
- Consumer connection
- Event publishing
- Health checks

### Test Routing Keys

The routing keys follow this pattern:

```
produits.{event_type}.{target_service}
```

Examples:
- `produits.product.created` - General event
- `produits.product.created.commandes` - Sent to commandes service
- `produits.product.deleted.commandes` - Product deleted, notify commandes
- `produits.product.deleted.clients` - Product deleted, notify clients
- `produits.stock.updated.commandes` - Stock updated, notify commandes
- `produits.stock.low_alert.commandes` - Low stock alert to commandes

## Event Types

The following events are published:

| Event Type | General Routing Key | Cross-Service Routing Keys |
|------------|-------------------|---------------------------|
| `product.created` | `produits.product.created` | `produits.product.created.commandes` |
| `product.updated` | `produits.product.updated` | `produits.product.updated.commandes` |
| `product.deleted` | `produits.product.deleted` | `produits.product.deleted.commandes`<br>`produits.product.deleted.clients` |
| `stock.updated` | `produits.stock.updated` | `produits.stock.updated.commandes` |
| `stock.low_alert` | `produits.stock.low_alert` | `produits.stock.low_alert.commandes` |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Railway RabbitMQ                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Exchange: mspr.events (TOPIC)                │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         │                  │                  │             │
│    ┌────▼─────┐       ┌───▼────┐       ┌────▼─────┐       │
│    │ produits │       │commandes│       │ clients  │       │
│    │  .queue  │       │  .queue │       │  .queue  │       │
│    └──────────┘       └─────────┘       └──────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Routing Bindings:**
- `produits.queue` binds to `produits.#`
- `commandes.queue` binds to `produits.*.commandes` and `commandes.#`
- `clients.queue` binds to `produits.*.clients` and `clients.#`

## Monitoring

### Health Check

Check the health endpoint to monitor RabbitMQ status:

```bash
curl http://localhost:8000/health
```

### Logs

The application logs all RabbitMQ operations with clear emoji indicators:
- 🔗 Connection attempts
- ✅ Successful operations
- ❌ Failures
- 📤 Published events
- 📥 Received messages
- 📊 Health status

### Connection Failures

If connection fails:
1. Check environment variables are set correctly
2. Verify Railway RabbitMQ service is running
3. Check logs for specific error messages
4. Verify SSL/TLS is enabled if using `amqps://`

## Deployment

### Railway Deployment

1. Ensure Railway RabbitMQ plugin is installed
2. Railway automatically provides these variables:
   - `RABBITMQ_URL`
   - `RABBITMQ_PRIVATE_URL` (preferred)
   - `RABBITMQ_NODENAME`
   - Others as needed

3. Set service-specific variables:
   - `SERVICE_NAME=produits`
   - `RABBITMQ_EXCHANGE=mspr.events`

4. Deploy and monitor `/health` endpoint

### Local Development

For local development without Railway:

```bash
# Option 1: Use docker-compose (includes RabbitMQ)
docker-compose up -d

# Option 2: Local RabbitMQ
export RABBITMQ_URL=amqp://guest:guest@localhost:5672/
export SERVICE_NAME=produits
export RABBITMQ_EXCHANGE=mspr.events
```

## Troubleshooting

### Connection Keeps Failing

1. **Check URL priority**: Private URL > Public URL > Constructed URL
2. **Verify SSL**: Use `amqps://` for Railway, `amqp://` for local
3. **Check timeouts**: Default 10s, increase if network is slow
4. **Review logs**: Look for specific AMQP errors

### Events Not Received by Other Services

1. **Verify routing keys**: Must match pattern `produits.{event}.{service}`
2. **Check queue bindings**: Other services must bind to correct patterns
3. **Test with RabbitMQ Management UI**: Publish test messages manually
4. **Verify exchange**: Must be TOPIC type, not DIRECT or FANOUT

### Health Check Shows Disconnected

1. **Connection may be lazy**: First API call triggers connection
2. **Check retry exhausted**: May need to restart service
3. **Verify credentials**: Check Railway environment variables
4. **Network issues**: Check Railway service status

## Best Practices

1. **Always use RABBITMQ_PRIVATE_URL on Railway** - Better performance and security
2. **Monitor health endpoint** - Include in uptime monitoring
3. **Handle connection failures gracefully** - Don't fail requests if RabbitMQ is down
4. **Use persistent messages** - DeliveryMode.PERSISTENT for all events
5. **Set appropriate TTL** - Messages expire after 24 hours
6. **Limit queue length** - Prevents memory issues (10,000 messages)
7. **Use heartbeats** - 30s heartbeat keeps connection alive

## References

- [RabbitMQ AMQP Concepts](https://www.rabbitmq.com/tutorials/amqp-concepts.html)
- [Railway RabbitMQ Plugin](https://railway.app/template/rabbitmq)
- [aio-pika Documentation](https://aio-pika.readthedocs.io/)
