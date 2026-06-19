# PyInstaller spec for the desktop build (src/desktop.py).
#
# Streamlit loads app.py dynamically at runtime (not via a Python `import`),
# so PyInstaller's static import analysis can never see what app.py needs --
# everything it (transitively) imports must be listed in hiddenimports below
# by hand. Build with: pyinstaller desktop.spec

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    "src.app", "src.config", "src.state", "src.graph", "src.routing",
    "src.setup_check", "src.nodes", "src.nodes.simplify",
    "src.nodes.capture_screen", "src.nodes.read_screen",
    "src.nodes.speech_in", "src.nodes.speech_out",
]

for pkg in [
    "streamlit", "langchain_ollama", "langchain", "langgraph",
    "faster_whisper", "piper", "mss", "pytesseract", "sounddevice",
]:
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

datas += [("src/app.py", "src"), ("models/piper", "models/piper")]

a = Analysis(
    ["src/desktop.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AccessibilityAssistant",
    console=True,  # keep visible while debugging; flip to False once stable
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="AccessibilityAssistant",
)
