# Scrapper Ultimate

Aplicație Python cu interfață web (HTML + Tailwind) pentru extragerea automată de date de pe site-uri (scraping), cu programare, variabile (XPath/CSS/constant), verificare și inserare în baze de date, plus notificări email.

## Funcționalități

- **Autentificare**: La prima pornire – pagină de setup (creare user/parolă). Apoi mereu pagina de login.
- **Joburi**: Creare joburi cu URL, programare (zi și oră), activare/dezactivare, rulare manuală.
- **Variabile**: Pe fiecare job poți defini variabile:
  - **XPath** sau **CSS** – extragere valoare de pe site
  - **Constant** – valoare fixă
  - **Formatare**: eliminare %, eliminare simbol valutar, spații, întreg, zecimal, dată ISO etc.
- **Baze de date**: Configurare conexiuni **PostgreSQL**, **MySQL**, **SQLite**, **Oracle**. Mai multe conexiuni per tip. La fiecare job alegi o conexiune.
- **Verificare și inserare**: Bloc **Verificare** – un `SELECT` care returnează un count; dacă count > 0, **nu** se execută blocul **Inserare**. Dacă verificarea este dezactivată, se execută direct inserarea. În SQL poți folosi variabilele cu sintaxa `{nume_variabilă}`.
- **Email**: Configurare SMTP, test trimitere. Per job: activare email la succes și/sau la eroare.
- **Loguri**: Pagină dedicată cu toate logurile (execuții, emailuri, erori).

## Instalare

```bash
cd SCRAPPER_ULTIMATE
pip install -r requirements.txt
```

Pentru **PostgreSQL** (opțional):

```bash
pip install psycopg2-binary
```

Pentru **Oracle** (opțional):

```bash
pip install oracledb
```

## Windows și Linux

Aplicația este compatibilă cu **Windows** și **Linux**. Căile fișierelor sunt gestionate cu `pathlib`; URI-ul SQLite folosește forward slashes pe toate sistemele. Pentru joburile cu **Selenium**: pe Windows se folosește Chrome (ChromeDriver în PATH); pe Linux, dacă Chrome nu este disponibil, se încearcă automat Firefox (geckodriver).

## Pornire

```bash
python run.py
```

Aplicația pornește pe `http://0.0.0.0:5000`.

- Dacă nu există niciun utilizator → se deschide **Setup** (creare cont).
- Dacă există utilizatori → se deschide **Login**. După autentificare → meniul principal (Joburi, Baze de date, Email, Loguri).

## Structură

- `app/` – Flask, modele, rute, scheduler, scraper, db_runner, email_sender, job_runner
- `templates/` – HTML cu Tailwind (setup, login, joburi, baze de date, email, loguri)
- `config.py` – configurare (SECRET_KEY, SQLite app.db)
- `run.py` – punct de intrare

## Utilizare rapidă

1. **Setup / Login** – creare cont sau autentificare.
2. **Baze de date** – adaugă cel puțin o conexiune (ex. SQLite cu cale fișier).
3. **Email** (opțional) – adaugă o configurare SMTP și testează.
4. **Joburi** – Job nou: nume, URL, zile + oră programare, variabile (XPath/CSS/constant + formatare), conexiune DB, bloc verificare (SELECT count), bloc inserare (INSERT cu `{variabile}`), opțiuni email.
5. **Loguri** – vezi execuțiile, reușite/erori și trimiteri email.

Variabilele se folosesc în SQL sub formă `{nume}` (ex: `INSERT INTO tabel (val) VALUES ('{price}');`). Înainte de rularea SQL, variabilele sunt înlocuite cu valorile extrase de pe site (sau constante).
