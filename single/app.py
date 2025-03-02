from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pytz
from dateutil import parser

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

eastern = pytz.timezone('America/New_York')

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reserved_time = db.Column(db.DateTime, nullable=False)
    user_name = db.Column(db.String(100), nullable=False)

    __table_args__ = (db.UniqueConstraint('reserved_time', 'user_name', name='unique_reservation'),)

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
    if request.method == "POST":
        if "reserve" in request.form:
            user_name = session.get("user_name", request.form["user_name"])
            selected_time_et = datetime.strptime(request.form["selected_time"], '%Y-%m-%d %H:%M:%S')
            selected_time_et = eastern.localize(selected_time_et)

            if Reservation.query.filter_by(reserved_time=selected_time_et, user_name=user_name).first():
                flash("You already booked this slot!", "error")
            elif Reservation.query.filter_by(reserved_time=selected_time_et).count() >= 5:
                flash("This time slot is full!", "error")
            else:
                new_reservation = Reservation(reserved_time=selected_time_et, user_name=user_name)
                db.session.add(new_reservation)
                db.session.commit()
                flash("Reservation successful!", "success")
                return redirect("/")

        elif "cancel" in request.form:
            reservation_time = parser.parse(request.form["reservation_id"])
            user_name = request.form["user_name"]
            reservation = Reservation.query.filter_by(reserved_time=reservation_time, user_name=user_name).first()
            
            if reservation:
                db.session.delete(reservation)
                db.session.commit()
                flash(f"Reservation for {user_name} at {reservation_time.strftime('%Y-%m-%d %I:%M %p ET')} canceled!", "success")

    time_slots = get_time_slots()
    reservations = Reservation.query.all()
    
    reservations_dict = {}
    for slot in time_slots:
        reservations_dict[slot] = [r.user_name for r in reservations if r.reserved_time.replace(tzinfo=None) == slot.replace(tzinfo=None)]

    current_user = session.get("user_name", "")

    return render_template("index.html", reservations_dict=reservations_dict, current_user=current_user)

@app.route("/set_name", methods=["POST"])
def set_name():
    session["user_name"] = request.form["user_name"]
    return jsonify(success=True)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
