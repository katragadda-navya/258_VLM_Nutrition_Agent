# VS Code Setup Guide - VLM Nutrition Agent

Complete step-by-step instructions to run this project in VS Code.

## Prerequisites

Before starting, ensure you have:
- ✅ Python 3.10+ installed
- ✅ Node.js 18+ installed
- ✅ Ollama installed and running
- ✅ VS Code installed

## Step 1: Open Project in VS Code

1. **Launch VS Code**
2. **Open the project folder**:
   - Click `File` → `Open Folder...`
   - Navigate to: `/Users/urvashikohale/Downloads/food_vlm_fastapi_react 5`
   - Click `Open`

## Step 2: Install VS Code Extensions (Recommended)

Install these extensions for better development experience:
- **Python** (by Microsoft) - for Python support
- **Pylance** (by Microsoft) - Python language server
- **ESLint** (by Microsoft) - JavaScript linting
- **Prettier** (by Prettier) - Code formatting

## Step 3: Set Up Backend (Python/FastAPI)

### 3.1 Open Integrated Terminal
- Press `` Ctrl + ` `` (backtick) or `View` → `Terminal`
- This opens the integrated terminal at the bottom of VS Code

### 3.2 Navigate to Backend Directory
```bash
cd backend
```

### 3.3 Create Python Virtual Environment (Optional but Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
```

### 3.4 Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3.5 Verify Environment Variables
The `.env` file should already exist with:
```bash
USDA_FDC_API_KEY=b1mdyndQhgaICOs2ENnZxxafV1so343eO5UTWZFf
OLLAMA_MODEL=qwen3-vl:8b
OLLAMA_LLAVA_MODEL=llava:7b-v1.6
OLLAMA_MINICPM_MODEL=minicpm-v:8b
OLLAMA_HOST=http://localhost:11434
```

### 3.6 Start Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

**Keep this terminal running!**

## Step 4: Set Up Frontend (React/Vite)

### 4.1 Open New Terminal
- Click the `+` icon in the terminal panel to open a new terminal
- Or press `` Ctrl + Shift + ` ``

### 4.2 Navigate to Frontend Directory
```bash
cd frontend
```

### 4.3 Install Node Dependencies (if not already installed)
```bash
npm install
```

### 4.4 Start Frontend Development Server
```bash
npm run dev
```

You should see:
```
VITE v5.4.21  ready in 242 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**Keep this terminal running too!**

## Step 5: Set Up Ollama Models

### 5.1 Open Another New Terminal
Click the `+` icon again to open a third terminal.

### 5.2 Pull Required Models
```bash
# Pull the default model (Qwen3-VL)
ollama pull qwen3-vl:8b

# Pull LLaVA (optional)
ollama pull llava:7b-v1.6

# Pull MiniCPM-V (optional)
ollama pull minicpm-v:8b
```

### 5.3 Verify Ollama is Running
```bash
ollama list
```

You should see your installed models listed.

## Step 6: Open the Application

1. **Open your browser** (Chrome, Firefox, Safari, etc.)
2. **Navigate to**: http://localhost:5173
3. You should see the "🥗 VLM Nutrition Agent" interface

## Step 7: Test the Application

1. **Select backend**: "ollama (local)"
2. **Select model**: Choose any model (e.g., "Qwen3-VL 8B" or "MiniCPM-V 2.6 8B")
3. **Upload a food image**: Click "Choose File" and select a food photo
4. **Click "Analyze"**: Wait for the results

## VS Code Workspace Layout

For optimal development, arrange your VS Code like this:

```
┌─────────────────────────────────────────┐
│  Explorer (Ctrl+Shift+E)                │
│  ├── backend/                           │
│  │   ├── app/                           │
│  │   │   ├── main.py                    │
│  │   │   ├── vlm.py                     │
│  │   │   └── fdc.py                     │
│  │   ├── .env                           │
│  │   └── requirements.txt               │
│  └── frontend/                          │
│      ├── src/                           │
│      │   ├── App.jsx                    │
│      │   └── lib/api.js                 │
│      └── package.json                   │
├─────────────────────────────────────────┤
│  Editor Area (your code files)          │
│                                         │
├─────────────────────────────────────────┤
│  Terminal Panel (Ctrl+`)                │
│  ├── Terminal 1: backend (uvicorn)     │
│  ├── Terminal 2: frontend (npm)        │
│  └── Terminal 3: free for commands     │
└─────────────────────────────────────────┘
```

## Useful VS Code Shortcuts

- **Toggle Terminal**: `` Ctrl + ` ``
- **New Terminal**: `` Ctrl + Shift + ` ``
- **Split Terminal**: `Cmd + \` (Mac) or `Ctrl + \` (Windows/Linux)
- **Toggle Sidebar**: `Cmd + B` (Mac) or `Ctrl + B` (Windows/Linux)
- **Quick Open File**: `Cmd + P` (Mac) or `Ctrl + P` (Windows/Linux)
- **Command Palette**: `Cmd + Shift + P` (Mac) or `Ctrl + Shift + P` (Windows/Linux)

## Debugging in VS Code

### Backend (Python)
1. Click the **Run and Debug** icon (Ctrl+Shift+D)
2. Click **"create a launch.json file"**
3. Select **"Python"** → **"FastAPI"**
4. Set breakpoints by clicking left of line numbers
5. Press **F5** to start debugging

### Frontend (React)
1. Install **"Debugger for Chrome"** extension
2. Use browser DevTools (F12) for debugging
3. Or use `console.log()` statements

## Stopping the Servers

To stop the servers:
1. **Backend**: Go to the backend terminal and press `Ctrl + C`
2. **Frontend**: Go to the frontend terminal and press `Ctrl + C`

## Troubleshooting

### Port Already in Use
If you see "port already in use" errors:
```bash
# Find and kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Find and kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

### Python Module Not Found
```bash
cd backend
pip install -r requirements.txt
```

### Node Modules Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Ollama Not Running
```bash
# Start Ollama service
ollama serve
```

## Project Structure

```
food_vlm_fastapi_react 5/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI routes
│   │   ├── vlm.py           # Vision-language model logic
│   │   └── fdc.py           # USDA FoodData Central API
│   ├── .env                 # Environment variables
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── lib/api.js       # API client
│   │   └── main.jsx         # Entry point
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
└── README.md                # Project documentation
```

## Next Steps

- Modify `backend/app/vlm.py` to customize model behavior
- Edit `frontend/src/App.jsx` to change the UI
- Add new models to the dropdown in `App.jsx`
- Customize nutrition tips in `backend/app/fdc.py`

Happy coding! 🚀
