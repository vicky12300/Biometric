# Windows ADMS Quick Setup Guide

## 🚀 Quick Start (3 Steps)

### 1️⃣ Configure Firewall
```cmd
Right-click configure_windows_firewall.bat → Run as administrator
```

### 2️⃣ Run Diagnostic
```cmd
python diagnose_windows_adms.py
```

### 3️⃣ Configure Device
- Server Address: `192.168.1.14`
- Server Port: `8000`
- HTTPS: `OFF`

---

## ✅ Verification Commands

### Check if port is open:
```cmd
netstat -an | findstr :8000
```

### Ping device:
```cmd
ping 192.168.1.119
```

### Test ADMS listener:
```cmd
curl http://192.168.1.14:8000/?SN=TEST
```

---

## 🔧 Your Configuration

| Component | Value |
|-----------|-------|
| Windows Server IP | 192.168.1.14 |
| Device IP | 192.168.1.119 |
| ADMS Port | 8000 |
| Device Serial | NYU7260401414 |
| Network | 192.168.1.x/24 |

---

## 🐛 Quick Troubleshooting

### Port already in use?
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Firewall blocking?
```cmd
netsh advfirewall firewall show rule name=all | findstr 8000
```

### Can't reach device?
```cmd
ping 192.168.1.119
tracert 192.168.1.119
```

---

## 📝 Expected Console Output

When working correctly:
```
[ADMS] Listener started on port 8000
[ADMS] GET /?SN=NYU7260401414 | SN=NYU7260401414
[ADMS] ✅ Sent registration response
[ADMS] POST /?SN=NYU7260401414 | table=ATTLOG
[ADMS] ✅ Punch: emp=101 time=2025-01-15 09:00:00
```

---

## 🆘 Still Not Working?

1. Run as Administrator
2. Disable antivirus temporarily
3. Check Windows Event Viewer
4. Try port 8080 instead of 8000
5. See `WINDOWS_ADMS_FIX.md` for detailed guide

---

## 📚 Files Reference

- `configure_windows_firewall.bat` - Firewall setup
- `diagnose_windows_adms.py` - Diagnostic tool
- `WINDOWS_ADMS_FIX.md` - Complete troubleshooting guide
- `adms_listener.py` - ADMS listener code
