# Quaderno - app di note con Kivy

## Avvio su Windows

1. Apri il terminale di VS Code nella cartella `QuadernoKivy`.
2. Attiva l'ambiente virtuale che hai già creato:

   ```bat
   C:\ProgettiPython\kivy_venv\Scripts\activate
   ```

3. Installa Kivy se non è già disponibile nell'ambiente:

   ```bat
   python -m pip install "kivy[base]"
   ```

4. Avvia l'app:

   ```bat
   python main.py
   ```

## Funzioni incluse

- Creazione di nuove note
- Modifica di titolo e testo
- Salvataggio automatico
- Ricerca nel titolo e nel contenuto
- Eliminazione della nota selezionata
- Persistenza dei dati in un file JSON

I dati sono salvati nella cartella dati utente di Kivy/Windows, non nella cartella del codice.

## APK

Questa versione è pensata prima per essere provata su Windows. Quando avremo verificato il funzionamento e adattato l'interfaccia alle dimensioni del telefono, prepareremo la compilazione Android con Buildozer tramite WSL2/Linux.
