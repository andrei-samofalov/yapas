# Async Server

This project is an asynchronous server built using Python's `asyncio.create_server`,
designed for efficient request handling. It features a simple router-based request dispatcher,
static file serving, and logging configuration.
The server can handle both `GET` and `POST` requests and allows for easy route registration.

## Features

- **Async server** powered by `asyncio.create_server`
- **Customizable logging** via log levels (debug, info, warning, error)
- **Static file serving** (optional)
- **Simple router-based dispatching** for request handling
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
python -m yapas --host <host_ip> --port <port_number> --static_path <path_to_static_files> --log_level <log_level>
```

### Example

```bash
python -m yapas --host 127.0.0.1 --port 8080 --static_path ./static --log_level info
```

### Parameters:

* `host`: IP address of the server (default: `0.0.0.0`)
* `port`: Port to bind the server to (default: `8079`)
* `static_path`: Optional path to serve static files from (default: `None`)
* `log_level`: Logging level (`debug`, `info`, `warning`, `error`) (default: `debug`)

### Error Handling

The server supports custom error handling for common HTTP errors:

* `404 Not Found`: Raised if a route is not found.
* `405 Method Not Allowed`: Raised if the requested method is not supported by the route.
* `500 Internal Server Error`: Raised for any unhandled exceptions.

### Static File Serving

You can serve static files by providing the `--static_path` argument.

### Backlog

#### HTTP Request Handling

* **Reverse Proxy Support**: Implement a basic reverse proxy feature to forward requests
  to another backend server, retaining client headers such as `User-Agent` and `Cookies`.
* **SSL/TLS Support**: Add HTTPS support using Python's built-in `ssl` module
  to enable secure communication over SSL/TLS.
* **Round Robin Load Balancing**: Extend reverse proxying to support multiple backend servers
  with a round-robin load balancing algorithm for better distribution of incoming requests.

#### Configuration and Customization

* ✅ **Signal Handling**: Implement proper signal handling to gracefully terminate (`SIGTERM`)
  or restart (`SIGHUP`) the server when required.

#### Static Content Management

* **Custom Error Pages**: Provide support for customizable error pages for common HTTP statuses
  such as 404 Not Found and 500 Internal Server Error.
* **Basic Caching**: Implement basic in-memory caching for static content to reduce load times
  for frequently accessed files by caching them for a configurable amount of time.

#### Logging and Error Handling

* **Enhanced Error Logging**: Improve logging of request details
  (e.g., date, time, HTTP method, URI, and response status) and provide detailed error logs
  for debugging.

### License

This project is licensed under the MIT License.




