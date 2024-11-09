# Async Server

This project is an asynchronous server built using Python's `asyncio.create_server`,
designed for efficient request handling. It features a simple router-based request dispatcher,
static file serving, and logging configuration.
The server can handle both `GET` and `POST` requests and allows for easy route registration.

## Features

- **Async server** powered by `asyncio.create_server`
- **Customizable logging** via log levels (debug, info, warning, error)
- **Static file serving** (optional)
- **Simple router-based dispatching** for request handling, configured in `locations.ini`
- **Error handling** for 404 (Not Found), 405 (Method Not Allowed), and 500 (Internal Server Error)
- **Flexible configuration** for host, port, and log levels

## How to Run

### Default Run

The server starts on `0.0.0.0:8079` by default. You can run the server with the following command:

```bash
python -m yapas
```

### Custom Parameters

You can customize the server's host, port, static file path, and logging level
with the following command-line options:

```bash
python -m yapas --host <host_ip> --port <port_number> --log_level <log_level>
```

### Example

```bash
python -m yapas --host 127.0.0.1 --port 8080 --log_level info --use_proxy
```

### Parameters:

* `host`: IP address of the server (default: `0.0.0.0`)
* `port`: Port to bind the server to (default: `8079`)
* `log_level`: Logging level (`debug`, `info`, `warning`, `error`) (default: `debug`)
* `use_proxy`: use or not pre-set reverse proxy (see `locations.ini`), 
ensure `localhost:8000` is listened, if this parameter is set

### Error Handling

The server supports custom error handling for common HTTP errors:

* `404 Not Found`: Raised if a route is not found.
* `405 Method Not Allowed`: Raised if the requested method is not supported by the route.
* `500 Internal Server Error`: Raised for any unhandled exceptions.

### Static Content Management

* Basic in-memory caching is implemented for static content.

### Signal Handling

* Server listens signals to gracefully terminate (`SIGTERM`) or restart (`SIGHUP`).

### Proxy support

* Server supports a basic reverse proxy feature to forward requests to another backend server,
  retaining client headers such as `User-Agent` and `Cookies`.

### Backlog

* **SSL/TLS Support**: Add HTTPS support using Python's built-in `ssl` module
  to enable secure communication over SSL/TLS.
* **Round Robin Load Balancing**: Extend reverse proxying to support multiple backend servers
  with a round-robin load balancing algorithm for better distribution of incoming requests.

### License

This project is licensed under the MIT License.
