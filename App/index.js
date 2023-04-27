const { app, BrowserWindow, nativeImage } = require("electron");
const { spawn } = require('child_process');


let theWindow;

function createWindow() {
    theWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
    },
  });
  theWindow.loadFile("index.html");

}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {

  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  // Esse evento é disparado pelo MacOS quando clica no ícone do aplicativo no Dock.
  // Basicamente cria a janela se não foi criada.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
