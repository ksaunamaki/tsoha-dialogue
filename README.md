# Dialogue - yksinkertainen keskustelufoorumi Pythonilla & Flaskilla

Tämä repository sisältää Helsingin Yliopiston Tietokannat ja web-ohjelmointi ("Tsoha") -kurssin harjoitustyöprojektin.

Projekti on toteutettu Pythonilla (3.10 tai uudempi toimii) ja Flaskilla, käyttäen Poetrya kirjastojenhallintaan. Käyttö vaatii (helpoiten paikalliselle koneelle) asennetun PostgreSQL -tietokannan.

Sovellus on kehitetty ja testattu macOS Monterey (12.x) version alaisuudessa, mutta se pitäisi toimia millä tahansa käyttöjärjestelmällä mikä täyttää tekniset vaatimukset ajoympäristön osalta.

## Asennus

### Tietokanta

Luo uusi tyhjä tietokanta haluttuun PostgreSQL instanssiin, oletusnimenä tietokannalle sovelluksessa on **dialogue** mutta se voi olla jotain muutakin. Sovellus ei luo itse tietokantaa, mutta alustaa sen tarvitsemat taulut osana käyttöönottoa.

Tämä onnistuu mm. käyttäen PostgreSQL:n cli-työkalua *psql*:

```psql
create database dialogue;
```

### Sovellus

Kloonaa repository haluamaasi hakemistoon koneella, johon on asennettu [Python 3](https://www.python.org/downloads/) sekä siihen [Poetry paketinhallinta](https://python-poetry.org/).

Kun repository on kloonattu, tulee ensin asentaa Poetryn avulla tarvittavat riippuvuudet. Suorita seuraava komento repositoryn juurihakemistossa:

```shell
poetry install
```

Kun Poetry on asentanut kirjastot, aja sovelluksen ensikonfigurointi setup.py tiedoston avulla:

```shell
poetry run python3 src/setup.py
```

Ensivaiheessa konfiguroidaan tietokantayhteys, mikäli PostgreSQL tietokanta on asennettu samalle koneelle ja tietokannalle käytettiin oletusnimeä (**dialogue**), voi kahteen ensimmäiseen kohtaan vastata pelkällä enter-näppäimen painalluksella. Jos tietokantapalvelin on jossain muussa osoitteessa ja/tai nimellä, pitää ne määritellä tässä.

Lisäksi voidaan määritellä tietokantayhteydellä käyttänimi ja salasana, mikäli autentikointiasetukset tietokannassa sitä edellyttävät.

Kun tietokantaparametrit ovat syötetty, asetusohjelma kirjoittaa yhteyden tiedot *src/* hakemistoon **.env** tiedostoon, josta varsinainen sovellus ne löytää.

Seuraavaksi asetusohjelma yrittää käyttää määriteltyjä yhteysasetuksia ja muodostaa yhteyden tietokantaan - mikäli tämä vaihe ei mene läpi, korjaa asetuksia joko ajamalla asetusohjelma uudestaan ja muokkaamalla parametreja, tai manuaalisesti editoimalla .env tiedostoa.

Mikäli yhteys toimii, asetusohjelma tarkistaa ja luo tarvittavat tietokantataulut tietokantaan. Mikäli tämä vaihe ei mene läpi, tarkista että yhteyden käyttämällä käyttäjätunnuksella on riittävät oikeudet PostgreSQL palvelimella olevaan tietokantaan. Vaihtoehtoisesti voit ajaa *src/* hakemistossa olevan tables.sql tiedoston sisällön manuaalisesti haluamallasi PostgreSQL client ohjelmistolla.

Kun taulut on tarkistettu, lopuksi asetusohjelma antaa mahdollisuuden muuttaa foorumisovelluksen nimeä (oletuksena **Default Dialogue Site**) sekä muuttaa tietokannassa olevien sovelluksen käyttäjätunnuksien statusta pääkäyttäjiksi (superuser). Koska yhtään käyttäjätiliä ei ole vielä tässä vaiheessa luotu sovellukseen, näitä oikeuksien muutoksia voi tulla myöhemmin takaisin tekemään ajamalla setup.py ohjelman uudelleen.

## Sovelluksen ajo

Kun sovellus on konfiguroitu, sen voi käynnistää Poetryn hallitseman virtuaaliympäristön sisällä seuraavilla komennoilla:

```shell
poetry shell
cd src
flask run
```

Tämä käynnistää paikallisen instanssin Flask sovelluksesta osoitteeseen http://127.0.0.1:5000.

Foorumia voi selailla kirjautumatta sisään, mutta uusien aiheiden (topic) sekä viestien (post) lähettämistä varten pyydetään kirjautumaan jo aiemmin luodulla käyttäjätunnuksella sisään, tai luomaan uusi käyttäjätunnus. Lisäksi aiheiden ylösäänestys (upvote) sekä yksityisviestin lähettäminen toisille käyttäjille edellyttää kirjautumista.

Yksityisviestejä voi lähettää klikkaamalla toisen käyttäjätunnuksen nimen vieressä olevaa kirjekuorikuvaketta luettaessa olemassaolevia julkisia viestejä tai vastaamalla omalle käyttälle lähetettyyn viestiin.

Mikäli käyttäjätunnukselle on annettu superuser -oikeudet setup.py asetusohjelman kautta, voi olemassaolevia viestejä myös poistaa aiheiden alta.
