from flask import Flask, render_template, request, redirect, session, flash, jsonify, g
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pytz
from dateutil import parser
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

from urllib.request import urlopen
# CODE BY SANJAY SESHAN

print("may crash on first run...please run again")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Define database URIs for each room
MEDIA_ROOM_DB_URI = 'sqlite:///media_room.db'
CRAFT_DANCE_ROOM_DB_URI = 'sqlite:///craft_dance_room.db'
KITCHEN_DB_URI = 'sqlite:///kitchen.db'
MUSIC_ROOM_DB_URI = 'sqlite:///music_room.db'
PASSWORDS_DB_URI = 'sqlite:///passwords.db'

# Create engines for each database
media_engine = create_engine(MEDIA_ROOM_DB_URI, echo=True)
craft_engine = create_engine(CRAFT_DANCE_ROOM_DB_URI, echo=True)
kitchen_engine = create_engine(KITCHEN_DB_URI, echo=True)
music_engine = create_engine(MUSIC_ROOM_DB_URI, echo=True)
# passwords = create_engine(PASSWORDS_DB_URI, echo=True)

# Create session makers for each engine
SessionMedia = sessionmaker(bind=media_engine)
SessionCraft = sessionmaker(bind=craft_engine)
SessionKitchen = sessionmaker(bind=kitchen_engine)
SessionMusic = sessionmaker(bind=music_engine)
# SessionPasswords = sessionmaker(bind=passwords)

# Create a single Base for all models
Base = declarative_base()

try:
    f = open("code.txt","r")
    code = f.readline()
    f.close()
except:
    print("could not access code.txt....creating")
    f = open("code.txt","w+")
    f.write("UNSET")
    f.close()

# Reservation model with extend_existing=True to handle multiple rooms sharing the same table name
class ReservationMedia(Base):
    __tablename__ = 'reservations'
    __table_args__ = {'extend_existing': True}  # Add this line
    id = Column(Integer, primary_key=True)
    reserved_time = Column(DateTime, nullable=False)
    user_name = Column(String(100), nullable=False)

class ReservationCraft(Base):
    __tablename__ = 'reservations'
    __table_args__ = {'extend_existing': True}  # Add this line
    id = Column(Integer, primary_key=True)
    reserved_time = Column(DateTime, nullable=False)
    user_name = Column(String(100), nullable=False)

class ReservationKitchen(Base):
    __tablename__ = 'reservations'
    __table_args__ = {'extend_existing': True}  # Add this line
    id = Column(Integer, primary_key=True)
    reserved_time = Column(DateTime, nullable=False)
    user_name = Column(String(100), nullable=False)

class ReservationMusic(Base):
    __tablename__ = 'reservations'
    __table_args__ = {'extend_existing': True}  # Add this line
    id = Column(Integer, primary_key=True)
    reserved_time = Column(DateTime, nullable=False)
    user_name = Column(String(100), nullable=False)



DATABASE = "users.db"

# Database connection
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)"
        )
        db.commit()
    return db



@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# Create the tables if they don't exist
Base.metadata.create_all(media_engine)
Base.metadata.create_all(craft_engine)
Base.metadata.create_all(kitchen_engine)
Base.metadata.create_all(music_engine)

# Setup timezone
eastern = pytz.timezone('America/New_York')

def get_time_slots():
    now = datetime.now(eastern).replace(second=0, microsecond=0, minute=(datetime.now().minute // 30) * 30)
    end = now + timedelta(days=7)
    if "user" in session and session["user"] == "MHEC":
        end = now + timedelta(days=14)
        now = now - timedelta(days=7)


    time_slots = []
    while now <= end:
        time_slots.append(now)
        now += timedelta(minutes=30)
    
    return time_slots

@app.route("/", methods=["GET", "POST"])
def index():
    room = session.get("room", "media_room")

    db = get_db()
    accounts = [(y,z) for x,y,z in db.execute("SELECT * FROM users").fetchall()]
    print(accounts)

    # Handle reservation logic
    if request.method == "POST":
        if "password" in request.form:
            if request.form["user_name"] != "MHEC":
                session["user_name"] = request.form["user_name"].lower()
            else:
                session["user_name"] = request.form["user_name"]

            session["password"] = request.form["password"]

            if ("@" in session["user_name"]):
                flash("No special characters like @ in kerb -- do not include @mit.edu", "error")
            else:
                username = session.get("user_name", "")
                password = session.get("password", "")
                # username = request.form["username"]
                # password = request.form["password"]

                db = get_db()
                user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

                if user:
                    # If user exists, check password
                    if user[2] == password:
                        session["user"] = username
                        flash("Logged in", "success")
                        session["loggedin"] = True
                        # return redirect("/")
                    else:
                        flash("Incorrect Password", "error")
                        # session["user_name"] = ""
                        # session["password"] = ""
                        session["loggedin"] = False
                        # return "Invalid password. <a href='/auth'>Try again</a>"
                else:
                    # If user does not exist, register them
                    db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                    db.commit()
                    session["user"] = username
                    # return redirect("/")
                    flash("Registered", "success")
                    session["loggedin"] = True
                
            
            # flash("Incorrect Password", "error")
        elif "kerb_user_name" in request.form:
            toverify = request.form["kerb_user_name"]
            url = "https://seshan.scripts.mit.edu/certdec.php?auth="+toverify
            page = urlopen(url)
            html_bytes = page.read()
            try:
                html = html_bytes.decode("utf-8")
                print(html.strip())
                ret = html.strip()
                if "@MIT.EDU" in ret:
                    session["user_name"] = ret.split("@MIT.EDU")[0]
                    session["user"] = session["user_name"]
                    session["password"] = "KERBEROS CERTIFICATE AUTHENTICATION"
                    flash("Logged in with MIT Certificates for "+ret.split(",")[1], "success")
                    session["loggedin"] = True
            except:
                print("ERROR CERT")
                pass
        elif "reserve" in request.form:
            user_name = session.get("user_name", request.form["user_name"])
            # password = session.get("password", request.form["password"])
            selected_time_et = datetime.strptime(request.form["selected_time"], '%Y-%m-%d %H:%M:%S')
            selected_time_et = eastern.localize(selected_time_et)

            if room == "media_room":
                session_db = SessionMedia()
                reservation_model = ReservationMedia
            elif room == "craft_dance_room":
                session_db = SessionCraft()
                reservation_model = ReservationCraft
            elif room == "kitchen":
                session_db = SessionKitchen()
                reservation_model = ReservationKitchen
            elif room == "music_room":
                session_db = SessionMusic()
                reservation_model = ReservationMusic

            # Check if the reservation already exists or is full
            if session_db.query(reservation_model).filter_by(reserved_time=selected_time_et, user_name=user_name).first():
                flash("You already booked this slot!", "error")
            elif session_db.query(reservation_model).filter_by(reserved_time=selected_time_et).count() >= 5:
                flash("This time slot is full!", "error")
            else:
                new_reservation = reservation_model(reserved_time=selected_time_et, user_name=user_name)
                session_db.add(new_reservation)
                session_db.commit()
                flash("Reservation successful!", "success")
                return redirect("/")

        elif "cancel" in request.form:
            reservation_time = parser.parse(request.form["reservation_id"])
            user_name = request.form["user_name"]
            # password = request.form["password"]

            if room == "media_room":
                session_db = SessionMedia()
                reservation_model = ReservationMedia
            elif room == "craft_dance_room":
                session_db = SessionCraft()
                reservation_model = ReservationCraft
            elif room == "kitchen":
                session_db = SessionKitchen()
                reservation_model = ReservationKitchen
            elif room == "music_room":
                session_db = SessionMusic()
                reservation_model = ReservationMusic

            reservation = session_db.query(reservation_model).filter_by(reserved_time=reservation_time, user_name=user_name).first()
            
            if reservation:
                session_db.delete(reservation)
                session_db.commit()
                flash(f"Reservation for {user_name} at {reservation_time.strftime('%Y-%m-%d %I:%M %p ET')} canceled!", "success")

    time_slots = get_time_slots()
    reservations_dict = {}
    if room == "media_room":
        session_db = SessionMedia()
        reservations = session_db.query(ReservationMedia).all()
    elif room == "craft_dance_room":
        session_db = SessionCraft()
        reservations = session_db.query(ReservationCraft).all()
    elif room == "kitchen":
        session_db = SessionKitchen()
        reservations = session_db.query(ReservationKitchen).all()
    elif room == "music_room":
        session_db = SessionMusic()
        reservations = session_db.query(ReservationMusic).all()

    try:
        for slot in time_slots:
            reservations_dict[slot] = [r.user_name for r in reservations if r.reserved_time.replace(tzinfo=None) == slot.replace(tzinfo=None)]
    except:
        print("error")
        pass
    # current_user = user_name
    f = open("code.txt","r")
    code = f.readline()
    print(code)
    f.close()

    current_user = session.get("user_name", "")
    password = session.get("password", "")
    loggedin = session.get("loggedin", "")
    return render_template("index.html", reservations_dict=reservations_dict, current_user=current_user, password=password, room=room, loggedin=loggedin, accounts=accounts, code=code)

@app.route("/cert_set_name", methods=["POST"])
def cert_set_name():
    session["user_name"] = request.form["user_name"]
    session["user"] = session["user_name"]
    flash("Logged in", "success")
    session["loggedin"] = True
    # flash("Your name has been set!", "success")
    return jsonify(success=True)

@app.route("/set_name", methods=["POST"])
def set_name():
    session["user_name"] = request.form["user_name"]

    # flash("Your name has been set!", "success")
    return jsonify(success=True)

@app.route("/set_password", methods=["POST"])
def set_password():
    session["password"] = request.form["password"]
    print(request.form["password"])
    # flash("Your name has been set!", "success")
    return jsonify(success=True)

@app.route("/admin", methods=["GET","POST"])
def admin():
    session["room"] = "admin"
    room = session.get("room", "media_room")


    db = get_db()

    # Handle reservation logic
    if request.method == "POST":
        if "password" in request.form:
            if request.form["user_name"] != "MHEC":
                session["user_name"] = request.form["user_name"].lower()
            else:
                session["user_name"] = request.form["user_name"]

            session["password"] = request.form["password"]

            if ("@" in session["user_name"]):
                flash("No special characters like @ in kerb -- do not include @mit.edu", "error")
            else:
                username = session.get("user_name", "")
                password = session.get("password", "")
                # username = request.form["username"]
                # password = request.form["password"]

                db = get_db()
                user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

                if user:
                    # If user exists, check password
                    if user[2] == password:
                        session["user"] = username
                        flash("Logged in", "success")
                        session["loggedin"] = True
                        # return redirect("/")
                    else:
                        flash("Incorrect Password", "error")
                        # session["user_name"] = ""
                        # session["password"] = ""
                        session["loggedin"] = False
                        # return "Invalid password. <a href='/auth'>Try again</a>"
                else:
                    # If user does not exist, register them
                    db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                    db.commit()
                    session["user"] = username
                    # return redirect("/")
                    flash("Registered", "success")
                    session["loggedin"] = True
                
            
            # flash("Incorrect Password", "error")
        elif "uname" in request.form:
                uname = request.form["uname"]
                db.execute("DELETE from users WHERE username = ?", (uname,))
                db.commit()
                # return redirect("/")
                flash("Deleted "+uname, "success")
        elif "code" in request.form:
                code = request.form["code"]
                f = open("code.txt","w")
                f.write(code)
                f.close()
                flash("Updated Kitchen code", "success")


    f = open("code.txt","r")
    code = f.readline()
    print(code)
    f.close()
  
            # flash("Incorrect Password", "error")
    accounts = [(y,z) for x,y,z in db.execute("SELECT * FROM users").fetchall()]
    print(accounts)        
    # current_user = user_name
    current_user = session.get("user_name", "")
    password = session.get("password", "")
    loggedin = session.get("loggedin", "")
    return render_template("admin.html", current_user=current_user, password=password, room=room, loggedin=loggedin, accounts=accounts, code=code)

@app.route("/select_room/<room>", methods=["GET","POST"])
def select_room(room):
    session["room"] = room
    return index()
    # return redirect("/")

    # return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
