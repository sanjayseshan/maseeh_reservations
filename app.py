from flask import Flask, render_template, request, redirect, session, flash, jsonify
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pytz
from dateutil import parser

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Define database URIs for each room
MEDIA_ROOM_DB_URI = 'sqlite:///media_room.db'
CRAFT_DANCE_ROOM_DB_URI = 'sqlite:///craft_dance_room.db'
KITCHEN_DB_URI = 'sqlite:///kitchen.db'
MUSIC_ROOM_DB_URI = 'sqlite:///music_room.db'

# Create engines for each database
media_engine = create_engine(MEDIA_ROOM_DB_URI, echo=True)
craft_engine = create_engine(CRAFT_DANCE_ROOM_DB_URI, echo=True)
kitchen_engine = create_engine(KITCHEN_DB_URI, echo=True)
music_engine = create_engine(MUSIC_ROOM_DB_URI, echo=True)

# Create session makers for each engine
SessionMedia = sessionmaker(bind=media_engine)
SessionCraft = sessionmaker(bind=craft_engine)
SessionKitchen = sessionmaker(bind=kitchen_engine)
SessionMusic = sessionmaker(bind=music_engine)

# Create a single Base for all models
Base = declarative_base()

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

    time_slots = []
    while now <= end:
        time_slots.append(now)
        now += timedelta(minutes=30)
    
    return time_slots

@app.route("/", methods=["GET", "POST"])
def index():
    room = session.get("room", "media_room")

    # Handle reservation logic
    if request.method == "POST":
        if "reserve" in request.form:
            user_name = session.get("user_name", request.form["user_name"])
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

    for slot in time_slots:
        reservations_dict[slot] = [r.user_name for r in reservations if r.reserved_time.replace(tzinfo=None) == slot.replace(tzinfo=None)]

    # current_user = user_name
    current_user = session.get("user_name", "")
    return render_template("index.html", reservations_dict=reservations_dict, current_user=current_user, room=room)

@app.route("/set_name", methods=["POST"])
def set_name():
    session["user_name"] = request.form["user_name"]
    # flash("Your name has been set!", "success")
    return jsonify(success=True)

@app.route("/select_room/<room>", methods=["GET"])
def select_room(room):
    session["room"] = room
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
