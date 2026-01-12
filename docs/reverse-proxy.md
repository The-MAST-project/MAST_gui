an nginx reverse-proxy is configured as follows:
# /etc/nginx/conf.d/mast-wis-control.conf

```nginx
server {
    listen 8000;

    # mast-dash (Django GUI)
    location /mast-dash/ {
        proxy_pass http://localhost:8010/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Proxy-Base /mast-dash/;
        proxy_set_header X-Proxy-Port 8000;
    }

    location /mast-backend/ {
        proxy_pass http://localhost:8002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Proxy-Base /mast-backend/;
        proxy_set_header X-Proxy-Port 8000;
    }

    # wao-safety (Grafana)
    location /wao-safety/ {
        proxy_pass http://10.23.1.25:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Proxy-Base /wao-safety/;
        proxy_set_header X-Proxy-Port 8000;
    }

    # mast-netdata (Netdata)
    location /mast-netdata/ {
        proxy_pass http://localhost:19999/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Proxy-Base /mast-netdata/;
        proxy_set_header X-Proxy-Port 8000;
    }

    # mast-share (File System Service)
    location /mast-share/ {
        proxy_pass http://localhost:8008/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Proxy-Base /mast-share/;
        proxy_set_header X-Proxy-Port 8000;
    }
}
```

django should work both behind the reverse proxy and directly

# What needs to be done so that Django complies with this design?

- **Set `FORCE_SCRIPT_NAME` in Django settings**  
  This ensures Django generates URLs with the correct subpath (e.g., `/mast-dash/`) when behind the proxy.  
  - Use `FORCE_SCRIPT_NAME = '/mast-dash'` when running behind the proxy.
  - Leave unset or `None` when running directly.

- **Set `USE_X_FORWARDED_HOST = True` and `SECURE_PROXY_SSL_HEADER`**  
  This allows Django to respect the proxy headers for host and protocol.

- **Set the script prefix at runtime**  
  In `wsgi.py`, detect the `X-Proxy-Base` header and call `set_script_prefix()` accordingly.  
  This allows Django to dynamically adjust the script prefix for each request.

- **Ensure static and media URLs are correct**  
  - When using a subpath, set `STATIC_URL` and `MEDIA_URL` to include the script prefix.
  - Use `{% get_static_prefix %}` and `{% url ... %}` in templates.

- **Prefix all AJAX/API calls and static asset URLs**  
  - In JavaScript, prepend the script prefix (from a template variable or a global JS variable) to all API endpoints and static file paths.

- **Test both direct and proxied modes**  
  - Direct: Django runs on port 8010, root path (`/`).
  - Proxy: Django is accessed via `/mast-dash/` on port 8000.

- **(Optional) Use environment variables for deployment flexibility**  
  - Set `FORCE_SCRIPT_NAME` and related settings via environment variables so the same codebase works in both modes.

**Summary:**  
Django must be configured to detect and respect the subpath (`/mast-dash/`) when behind the proxy, and to work normally when accessed directly. This involves settings changes, runtime script prefix handling, and careful URL construction in both Python and JavaScript.

`{% url %}` is a Django template tag that generates the correct URL for a given view name (and optional arguments), using Django's URL routing system.  
It ensures that URLs are always correct, respect the current script prefix (such as `/mast-dash/`), and automatically update if your URL patterns change.

**Example:**
```django
<a href="{% url 'myapp:myview' %}">Link</a>
```
This will render as:
```html
<a href="/mast-dash/myapp/myview/">Link</a>
```
when behind the proxy, or as:
```html
<a href="/myapp/myview/">Link</a>
```
when running directly.
