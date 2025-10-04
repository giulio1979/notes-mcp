# Web Server Troubleshooting Guide

## Quick Start

The web server is running successfully! Access it at:
- **Primary URL**: `http://localhost:5000`
- **Alternative**: `http://127.0.0.1:5000`
- **Network**: `http://192.168.178.100:5000` (from other devices on your network)

## Common Issues & Solutions

### Issue 1: "Site can't be reached" or "Connection refused"

**Solution:**
1. Verify the server is running:
   ```bash
   # Look for this output:
   # * Running on http://127.0.0.1:5000
   ```

2. Check if port 5000 is blocked:
   ```powershell
   # Windows: Check if port is in use
   netstat -ano | findstr :5000
   ```

3. Try the alternative URL: `http://127.0.0.1:5000` instead of `localhost`

### Issue 2: Browser shows "Loading..." but nothing appears

**Solution:**
1. **Clear browser cache**: Ctrl+Shift+Delete (Chrome/Edge) or Ctrl+Shift+R (hard refresh)
2. **Try incognito/private mode**: This bypasses cache and extensions
3. **Check browser console**: Press F12, look for JavaScript errors

### Issue 3: Firewall blocking access

**Solution (Windows):**
1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Find Python and check both Private and Public networks
4. Or temporarily disable firewall to test

### Issue 4: Wrong port or URL

**Correct URLs:**
- ✅ `http://localhost:5000`
- ✅ `http://127.0.0.1:5000`
- ❌ `https://localhost:5000` (no HTTPS)
- ❌ `localhost:5000` (missing http://)
- ❌ `http://localhost` (missing :5000)

### Issue 5: Server crashes on startup

**Check logs for:**
```
Error: Address already in use
```

**Solution:**
```powershell
# Kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F

# Or use different port
python -m src.web_server
# Then edit src/web_server.py to change port
```

## Verify Server is Running

### Check Terminal Output
You should see:
```
* Serving Flask app 'web_server'
* Debug mode: on
* Running on http://127.0.0.1:5000
* Running on http://192.168.178.100:5000
Press CTRL+C to quit
```

### Test from Command Line
```powershell
# PowerShell
Invoke-WebRequest http://localhost:5000

# Or use curl (if installed)
curl http://localhost:5000
```

Should return HTML content with "Notes Manager" in it.

## Browser-Specific Issues

### Chrome/Edge
- Clear cache: Settings → Privacy → Clear browsing data
- Disable extensions that might block local servers
- Check DevTools Console (F12) for errors

### Firefox
- Clear cache: Options → Privacy → Clear Data
- Check if "Enhanced Tracking Protection" is blocking
- Try "about:config" → check network settings

### Safari
- Clear cache: Develop → Empty Caches
- Check Preferences → Privacy settings

## Still Not Working?

### Step-by-step debugging:

1. **Verify Python environment**
   ```powershell
   D:/Nextcloud/BackupWork/CURRENT/notes-mcp/.venv/Scripts/python.exe --version
   ```

2. **Check if Flask is installed**
   ```powershell
   D:/Nextcloud/BackupWork/CURRENT/notes-mcp/.venv/Scripts/python.exe -c "import flask; print(flask.__version__)"
   ```

3. **Test Flask directly**
   ```powershell
   D:/Nextcloud/BackupWork/CURRENT/notes-mcp/.venv/Scripts/python.exe -c "from flask import Flask; app = Flask('test'); print('Flask OK')"
   ```

4. **Check templates exist**
   ```powershell
   dir src\templates
   # Should show: base.html, index.html, note.html, project.html, search.html
   ```

5. **Try different port**
   Edit `src/web_server.py`, find the `main()` function:
   ```python
   port = int(os.environ.get("PORT", 5000))  # Change 5000 to 8080
   ```

6. **Check for errors in terminal**
   Look for any Python tracebacks or error messages

## Test Pages

Once the server is running, test these URLs:

1. **Home page**: `http://localhost:5000/`
   - Should show list of projects

2. **Search page**: `http://localhost:5000/search`
   - Should show search form

3. **Demo project**: `http://localhost:5000/project/Demo%20Project`
   - Should show notes in Demo Project

4. **Rebuild index**: `http://localhost:5000/rebuild_index`
   - Should redirect to home with message

5. **API endpoint**: `http://localhost:5000/api/deep-link/project/Demo%20Project`
   - Should return JSON

## Expected Server Output

When working correctly, you'll see requests in the terminal:
```
127.0.0.1 - - [04/Oct/2025 19:09:01] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [04/Oct/2025 19:09:09] "GET /project/Demo%20Project HTTP/1.1" 200 -
```

- `200` = Success ✅
- `404` = Page not found ❌
- `500` = Server error ❌

## Production Deployment

For production use, don't use the Flask development server. Instead:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "src.web_server:app"
```

Or use the Docker deployment:
```bash
docker-compose up web-interface
```

## Get Help

If none of these solutions work:

1. Check the terminal output for error messages
2. Copy the full error traceback
3. Check if port 5000 is available
4. Try restarting your computer (sometimes helps with port conflicts)
5. Verify all dependencies are installed: `pip install -e .`

## Quick Test Script

Save this as `test_web.py`:
```python
import requests
try:
    response = requests.get('http://localhost:5000')
    if response.status_code == 200:
        print("✓ Web server is working!")
        print(f"Content length: {len(response.text)} bytes")
    else:
        print(f"✗ Server returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to server. Is it running?")
except Exception as e:
    print(f"✗ Error: {e}")
```

Run it:
```bash
pip install requests
python test_web.py
```

## Contact

For more help, check:
- [README.md](README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [DOCKER.md](DOCKER.md) - Docker deployment guide
