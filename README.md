# 🎄 Świąteczne Losowanie

Rodzinne losowanie prezentów: pada śnieg, migają lampki, prezent się otwiera, kręci się bęben z imionami, a na koniec lecą konfetti i grają dzwoneczki.

## Zasady losowania

- Każda osoba dostaje **osobisty link**, więc nikt nie wylosuje za kogoś innego.
- Wylosowana osoba **znika z puli**, więc nikt nie zostanie wylosowany dwa razy.
- **Losuje się raz.** Odświeżenie strony pokazuje ten sam wynik, więc nie da się „przelosować”.
- **Trafisz na siebie?** Dostajesz **jedną** dodatkową próbę, w której nie da się już trafić na siebie.
- Algorytm pilnuje, żeby **ostatnia osoba nie została sama ze sobą** w puli.
- Organizator **nie widzi, kto kogo wylosował**, więc też może brać udział.

---

## 🚀 Wdrożenie na darmowy hosting: Render.com

Aplikacja działa w całości na serwerach Rendera, więc Twój komputer może być wyłączony.
Wyniki trzymane są w darmowej bazie Postgres, więc przetrwają uśpienie serwera.

### 1. Wrzuć kod na GitHuba

Załóż puste repozytorium na [github.com/new](https://github.com/new), np. `swiateczne-losowanie` (może być prywatne), a potem w folderze projektu:

```bash
git init
git add .
git commit -m "Świąteczne losowanie"
git branch -M main
git remote add origin https://github.com/TWOJ_LOGIN/swiateczne-losowanie.git
git push -u origin main
```

### 2. Utwórz aplikację na Renderze (jednym kliknięciem)

1. Załóż konto na [render.com](https://render.com). Najprościej zalogować się przez GitHuba.
2. Kliknij **New → Blueprint** i wybierz swoje repozytorium.
3. Render odczyta plik `render.yaml` i sam utworzy serwer oraz bazę danych.
4. Poprosi o wartość **`SETUP_KEY`**. To Twoje hasło organizatora: wymyśl coś i zapamiętaj.
5. Kliknij **Deploy Blueprint** i poczekaj 3–5 minut, aż status zmieni się na *Live*.

### 3. Przygotuj losowanie przez stronę

1. Wejdź na `https://swiateczne-losowanie.onrender.com/setup`. Dokładny adres zobaczysz w panelu Rendera.
2. Wpisz hasło (`SETUP_KEY`), uczestników (jedna osoba w linii) i termin zakończenia.
3. Po kliknięciu **Utwórz losowanie** trafisz do **panelu organizatora**. **Zapisz jego adres w zakładkach!** Tylko przez niego masz dostęp do panelu.
4. Kliknij **„📋 Kopiuj wiadomość dla wszystkich”** i wklej ją na rodzinnym WhatsAppie lub Messengerze. Gotowe! 🎉

### Warto wiedzieć o darmowym planie

| | |
|---|---|
| 😴 **Usypianie** | Po 15 minutach bez ruchu serwer zasypia, a pierwsze wejście trwa wtedy ok. minuty. Otwórz stronę sam tuż przed wysłaniem linków, żeby ją „obudzić”. Wyniki są bezpieczne w bazie. |
| 🗓️ **Baza na 30 dni** | Darmowa baza Postgres na Renderze wygasa po 30 dniach. Na jednorazowe losowanie to aż nadto. |
| 🧹 **Po świętach** | W panelu Rendera możesz usunąć serwis i bazę. |
| 🔁 **Losowanie od nowa** | Wejdź ponownie na `/setup` i zaznacz „Zacznij od nowa”. Stare linki przestaną działać. |

---

## Alternatywa: PythonAnywhere

Też jest darmowy, a dane trzymane są w pliku na dysku, bez bazy danych.

1. Załóż konto na [pythonanywhere.com](https://www.pythonanywhere.com) (plan *Beginner*).
2. W konsoli **Bash**: `git clone https://github.com/TWOJ_LOGIN/swiateczne-losowanie.git` i `pip install --user -r swiateczne-losowanie/requirements.txt`.
3. Zakładka **Web → Add a new web app → Manual configuration → Python 3.12**. W pliku WSGI wpisz:
   ```python
   import os, sys
   os.environ["SETUP_KEY"] = "twoje-haslo-organizatora"
   sys.path.insert(0, "/home/TWOJ_LOGIN/swiateczne-losowanie")
   from app import app as application
   ```
4. W tej samej zakładce, w sekcji **Static files**, dodaj: URL `/static/` → katalog `/home/TWOJ_LOGIN/swiateczne-losowanie/static`.
5. Kliknij **Reload** i wejdź na `https://TWOJ_LOGIN.pythonanywhere.com/setup`.

---

## Uruchomienie lokalne (do testów)

```bash
python -m venv venv
venv\Scripts\activate                 # Windows; w MSYS2/Linux: source venv/bin/activate
pip install -r requirements.txt

python setup_losowania.py             # bierze imiona z uczestnicy.txt, aktywne dziś do 23:59
python run.py                         # http://localhost:8000
```

Lokalnie wyniki trafiają do pliku `data/stan.json`. Jeśli ustawisz zmienną `SETUP_KEY`, możesz też korzystać ze strony `/setup`.

## Konfiguracja (zmienne środowiskowe)

| Zmienna | Znaczenie |
|---|---|
| `SETUP_KEY` | Hasło do strony `/setup`. Puste oznacza, że strona jest wyłączona. |
| `DATABASE_URL` | Adres bazy Postgres. Ustawiony: wyniki w bazie; pusty: w pliku `data/stan.json`. |
| `LOSOWANIE_TZ` | Strefa czasowa terminu, domyślnie `Europe/Warsaw`. |

## Struktura projektu

```
app.py               – serwer Flask: strony, API losowania, /setup, panel organizatora
draw.py              – logika losowania (zasady, ochrona przed ślepym zaułkiem)
storage.py           – zapis stanu: plik JSON lub Postgres, z blokadą przy jednoczesnych kliknięciach
config.py            – ustawienia ze zmiennych środowiskowych
setup_losowania.py   – przygotowanie losowania z konsoli (alternatywa dla /setup)
run.py               – lokalne uruchomienie serwera (waitress)
render.yaml          – przepis wdrożenia na Render (serwer + baza)
templates/           – strony HTML (Jinja2)
static/css/style.css – wygląd: prezent, bęben, lampki, karta z wynikiem
static/js/           – śnieg, konfetti, dźwięki (Web Audio), animacja losowania
tests/               – testy (pytest)
```

## Testy

```bash
python -m pytest -q
# z prawdziwym Postgresem:
TEST_DATABASE_URL=postgresql://user:haslo@localhost/baza python -m pytest -q
```
