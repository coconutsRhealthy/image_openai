import mysql.connector

# Functie om webshop-URL + naam op te slaan in DB (indien nog niet aanwezig)
def store_webshops(webshops: dict):
    try:
        # Verbind met MySQL
        db_connection = mysql.connector.connect(
            host="localhost",
            user="appuser",
            password="app_password",
            database="py_diski_webshops"
        )
        cursor = db_connection.cursor()

        for webshop_name, url in webshops.items():

            # Check of deze URL al in de database zit
            cursor.execute(
                "SELECT id FROM webshop_info WHERE webshop_url = %s",
                (url,)
            )
            existing = cursor.fetchone()

            if existing:
                print(f"Webshop already exists in DB: {webshop_name} ({url})")
                continue

            # Voeg toe aan DB
            insert_query = """
                INSERT INTO webshop_info (webshop_url, webshop_name)
                VALUES (%s, %s)
            """
            cursor.execute(insert_query, (url, webshop_name))
            db_connection.commit()
            print(f"Inserted: {webshop_name} ({url})")

        # Sluit verbinding
        cursor.close()
        db_connection.close()

    except mysql.connector.Error as err:
        print(f"Database error: {err}")

# Test block
if __name__ == "__main__":
    webshops = {
        "about-you": "https://en.aboutyou.nl/your-shop",
        "adidas": "https://www.adidas.nl/",
        "aimnsportswear": "https://www.aimnsportswear.nl/",
        "airup": "https://shop.air-up.com/nl/en",
        "albelli": "https://www.albelli.nl/",
        "aliexpress": "http://nl.aliexpress.com/",
        "amazon": "https://www.amazon.nl/",
        "arket": "https://www.arket.com/en-nl/",
        "asos": "https://www.asos.com/nl/dames/",
        "aybl": "https://nl.aybl.com",
        "bershka": "https://www.bershka.com/nl/h-woman.html",
        "bijenkorf": "https://www.debijenkorf.nl/",
        "bjornborg": "https://www.bjornborg.com/nl/",
        "bodyandfit.com": "https://www.bodyandfit.com",
        "bol.com": "https://www.bol.com/nl/nl/",
        "boohoo": "https://nl.boohoo.com/",
        "boozyshop": "https://www.boozyshop.nl/",
        "burga": "https://burga.nl/",
        "bylashbabe": "https://bylashbabe.nl/",
        "cabaulifestyle": "https://cabaulifestyle.com/",
        "charlottetilbury": "https://www.charlottetilbury.com/nl",
        "cider": "https://www.shopcider.com/",
        "colourfulrebel": "https://colourfulrebel.com/",
        "coolblue": "https://www.coolblue.nl/",
        "costes": "https://www.costesfashion.com/nl-nl",
        "cottonclub": "https://www.cottonclub.nl/nl-nl",
        "creamyfabrics": "https://creamyfabrics.com/nl",
        "decathlon": "https://www.decathlon.nl/",
        "deloox": "https://www.deloox.nl/",
        "desenio": "https://desenio.nl/",
        "dilling": "https://www.dilling.nl/",
        "douglas": "https://www.douglas.nl/nl",
        "dyson": "https://www.dyson.nl/nl",
        "emmasleepnl": "https://www.emma-sleep.nl/",
        "emyjewels": "https://emyjewels.com/",
        "esn": "https://nl.esn.com/",
        "estrid": "https://estrid.com/en-nl/pages/home",
        "esuals": "https://www.esuals.nl/",
        "etos": "https://www.etos.nl/",
        "famousstore": "https://www.famous-store.nl/",
        "fashiontiger.nl": "https://fashiontiger.nl/",
        "footlocker": "https://www.footlocker.nl/",
        "geurwolkje": "https://geurwolkje.nl/",
        "ginatricot": "https://www.ginatricot.com/nl",
        "gisou": "https://gisou.com/",
        "greetz.nl": "https://www.greetz.nl/nl/",
        "gutsgusto": "https://www.gutsgusto.com/en",
        "gymshark": "https://nl.gymshark.com/",
        "haarshop.nl": "https://www.haarshop.nl/",
        "hellofresh.nl": "https://www.hellofresh.nl/",
        "hema": "https://www.hema.nl/",
        "hm": "https://www2.hm.com/nl_nl/index.html",
        "hollandandbarrett": "https://www.hollandandbarrett.nl/",
        "hunkemoller": "https://www.hunkemoller.nl/",
        "iciparisxl": "https://www.iciparisxl.nl/",
        "idealofsweden": "https://idealofsweden.nl/",
        "jdsports": "https://www.jdsports.nl/",
        "kaartje2go": "https://www.kaartje2go.nl/",
        "kaptenandson": "https://kapten-son.com/nl",
        "koreanskincare": "https://koreanskincare.nl/",
        "kruidvat": "https://www.kruidvat.nl/",
        "leolive": "https://le-olive.com/",
        "loavies": "https://www.loavies.com/nl/",
        "lookfantastic": "https://www.lookfantastic.nl",
        "loopearplugs": "https://www.loopearplugs.com/?country=NL",
        "loungeunderwear": "https://nl.lounge.com/",
        "lucardi": "https://www.lucardi.nl/",
        "lyko": "https://lyko.com/nl",
        "mango": "https://shop.mango.com/nl/nl",
        "mediamarkt": "https://www.mediamarkt.nl/",
        "meetmethere": "https://meet-me-there.com/?country=NL",
        "merodacosmetics": "https://merodacosmetics.nl/",
        "mimamsterdam": "https://www.mimamsterdam.com/nl/",
        "minre": "https://www.minre.nl/",
        "mostwanted": "https://most-wanted.com/",
        "myjewellery": "https://www.my-jewellery.com/nl-nl",
        "myproteinnl": "https://nl.myprotein.com/",
        "nakdfashion": "https://www.na-kd.com/nl",
        "nike": "https://www.nike.com/nl/en/",
        "ninjakitchen": "https://ninjakitchen.nl/",
        "notino": "https://www.notino.nl/",
        "oliviakate": "https://oliviakate.nl/",
        "omoda": "https://www.omoda.nl/",
        "only": "https://www.only.com/en-nl",
        "otrium": "https://www.otrium.nl/dames",
        "pandora": "https://nl.pandora.net/",
        "parfumado": "https://parfumado.com/",
        "parfumdreams.nl": "https://www.parfumdreams.nl/",
        "paulaschoice.nl": "https://www.paulaschoice.nl/nl",
        "pinkgellac": "https://pinkgellac.com/nl",
        "plutosport": "https://www.plutosport.nl/",
        "pullandbear": "https://www.pullandbear.com/nl/",
        "rituals": "https://www.rituals.com/nl-nl/home",
        "scuffers": "https://scuffers.com/",
        "sellpy": "https://www.sellpy.nl/",
        "shein": "https://nl.shein.com/",
        "shoeby": "https://www.shoeby.nl/",
        "sissy-boy": "https://www.sissy-boy.com/",
        "sizzthebrand": "https://sizzthebrand.com/",
        "smartphonehoesjes.nl": "https://www.smartphonehoesjes.nl/",
        "snipes": "https://www.snipes.com/nl-nl/",
        "snuggs": "https://snuggs.nl/",
        "sophiamae": "https://sophia-mae.com/",
        "spacenk.com": "https://www.spacenk.com/nl/home",
        "stradivarius": "https://www.stradivarius.com/nl/",
        "stronger": "https://www.strongerlabel.com/nl",
        "temu": "https://www.temu.com/nl-en",
        "tessv": "https://www.tessv.nl/",
        "thesting": "https://www.thesting.com/nl-nl/dames",
        "thingsilikethingsilove": "https://www.thingsilikethingsilove.com/",
        "thuisbezorgd": "https://www.thuisbezorgd.nl/",
        "uniqlo": "https://www.uniqlo.com/nl/nl/",
        "upfront": "https://upfront.nl/",
        "urbanoutfitters": "https://www.urbanoutfitters.com/",
        "veromoda": "https://www.veromoda.com/nl-nl",
        "weekday": "https://www.weekday.com/nl-nl/women/",
        "wehkamp": "https://www.wehkamp.nl/",
        "westwing": "https://www.westwing.nl/",
        "xenos": "https://www.xenos.nl/",
        "xoxowildhearts": "https://www.xoxowildhearts.com/",
        "xxlnutrition": "https://xxlnutrition.com/nl",
        "yoursurprise": "https://www.yoursurprise.nl/",
        "zalando": "https://www.zalando.nl/dames-home/",
        "zara": "https://www.zara.com/nl/",
        "zelesta.nl": "https://zelesta.nl/"
    }

    store_webshops(webshops)
