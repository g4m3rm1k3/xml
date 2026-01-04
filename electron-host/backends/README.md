# This is where you put your PyInstaller-built backends

## How to add a backend:

1. Build your Flask/FastAPI app with PyInstaller:
   ```
   pyinstaller --name my-app --onedir wsgi.py
   ```

2. Copy the entire output folder here:
   ```
   dist/my-app/  -->  backends/my-app/
   ```

3. (Optional) Create a metadata.json in the folder:
   ```json
   {
       "displayName": "My Application",
       "description": "What this app does",
       "version": "1.0.0"
   }
   ```

4. Restart the launcher - your app will appear!

## Requirements for your Python app:

- Must read port from APP_PORT environment variable
- Must have a /health endpoint that returns 200 OK
- Must bind to 127.0.0.1
