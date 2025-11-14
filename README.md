# HTTP Proxy

A simple HTTP proxy that receives POST requests and forwards them to a destination URL provided in the request body. It supports an optional allowlist for source IPs.

## Configuration

The proxy is configured using a single environment variable:

| Variable      | Description                               | Default |
|---------------|-------------------------------------------|---------|
| `ALLOWED_IPS` | A comma-separated list of allowed source IPs. If empty, all sources are allowed. | `""`    |

## Usage

To use the proxy, send a `POST` request to it with a JSON body containing the `method` and `destination` for the forwarded request.

### Request Body

The request body must be a JSON object with the following keys:

| Key           | Description                               | Required |
|---------------|-------------------------------------------|----------|
| `method`      | The HTTP method to use for the forwarded request. Can be `GET` or `POST`. | Yes      |
| `destination` | The full URL to forward the request to.   | Yes      |
| `...`         | Any other key-value pairs will be passed as the JSON body for `POST` requests or as query parameters for `GET` requests. | No       |

### Examples

**Forwarding a GET request:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"method": "GET", "destination": "http://example.com/api"}' \
  http://localhost:5000/
```

**Forwarding a POST request:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"method": "POST", "destination": "http://example.com/api", "key": "value"}' \
  http://localhost:5000/
```

## Running with Docker

1.  **Build the Docker image:**
    ```bash
    docker build -t http-proxy .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -p 5000:5000 \
      -e ALLOWED_IPS="127.0.0.1,192.168.1.100" \
      http-proxy
    ```

## Running with Docker Compose

The `docker-compose.yml` file is pre-configured for local development.

1.  **Start the proxy:**
    ```bash
    docker-compose up
    ```

2.  **To run in detached mode:**
    ```bash
    docker-compose up -d
    ```

## Testing

To run the unit tests:

```bash
python -m unittest discover tests
```
