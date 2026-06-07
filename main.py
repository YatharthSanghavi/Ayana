from functools import wraps
from flask import Flask, request, jsonify, redirect, url_for, render_template, session
from ai.plan import call_gemini
from day_date.day_date_check import enforce_day_limit,compute_road_trip_days
from geo.map import build_plan_trip_map
from ai.prompt import build_plan_trip_prompt,build_road_trip_prompt
from db.db import supabase, get_user_supabase

app = Flask(__name__)
app.secret_key = "your-super-secret-development-key"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("render_login"))
        return f(*args, **kwargs)
    return decorated_function

@app.get("/")
def root():
    return render_template("index.html")

@app.get("/auth/login")
def render_login():
    return render_template("auth/login.html")

@app.post("/auth/login")
def login():
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                session["user_id"] = response.user.id
                session["user_email"] = response.user.email
                session["access_token"] = response.session.access_token
                session["refresh_token"] = response.session.refresh_token
                return redirect(url_for("root"))
            
            return redirect(url_for("dashboard"))

        except Exception as e:
            return render_template("auth/login.html", error="Invalid email or password.")

@app.get("/auth/signup")
def render_signup():
    return render_template("auth/signup.html")

@app.post("/auth/signup")
def signup():
    if request.method=="POST":
        fname=request.form["fname"]
        lname=request.form["lname"]
        email=request.form["email"]
        password=request.form["password"]

        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "firstname": fname,
                        "lastname": lname
                    }
                }
            })
            if response.user:
                return redirect(url_for("render_login"))
            else:
                return render_template("auth/signup.html", error="Registration failed. try again")
        except Exception as e:
            return render_template("auth/signup.html", error=f"Registration failed: {str(e)}")
    return render_template("auth/signup.html")

@app.get("/auth/logout")
def logout():
    session.clear()
    supabase.auth.sign_out()
    return redirect(url_for("render_login"))

@app.get("/dashboard")
@login_required
def dashboard():
    import json
    user_id = session["user_id"]

    user_db = get_user_supabase()

    profile = (
        user_db.table("profiles")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )

    plan_trips = (
        user_db.table("plan_trips")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    road_trips = (
        user_db.table("road_trips")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    
    trips = []

    for trip in plan_trips.data:
        trips.append({
            **trip,
            "trip_type": trip.get("trip_type", "itinerary")
        })
    for trip in road_trips.data:
        trips.append({
            **trip,
            "trip_type": "road_trip",
            "destination": f"{trip['start_location']} → {trip['end_location']}"
        })

    return render_template(
        "pages/dashboard.html",
        user=profile.data,
        trips_json=json.dumps(trips)
    )

@app.get("/plan-trip")
@login_required
def render_plan_trip():
    return render_template("pages/plan-trip.html")

@app.post("/plan-trip")
@login_required
def plan_trip():
    details = request.get_json(silent=True)
    if not details:
        return jsonify({"error": "No JSON body provided"}), 400

    try:
        prompt = build_plan_trip_prompt(details)
        generated_plan = call_gemini(prompt)
        locations_list = generated_plan.get("locations", [])
        map_html = build_plan_trip_map(locations_list)

        user_db = get_user_supabase()

        response = user_db.table("plan_trips").insert({
            "user_id": session["user_id"],
            "destination": details.get('destination'),
            "days": details.get('days'),
            "budget": details.get('budget'),
            "travelers": details.get('travelers'),
            "trip_type": details.get('tripType'),
            "interests": details.get('interests'),
            "markdown": generated_plan.get('markdown'),
            "budget_data": generated_plan.get('budget'),
            "locations": generated_plan.get('locations'),
        }).execute()

        return jsonify({"data": generated_plan,"map":map_html})
    except Exception as e:
        print({str(e)})
        return jsonify({"error": f"Failed to generate itinerary: {str(e)}"}), 500

@app.get("/road-trip")
@login_required
def render_road_trip():
    return render_template("pages/road-trip.html")

@app.post("/road-trip")
@login_required
def road_trip():
    details = request.get_json(silent=True)
    if not details:
        return jsonify({"error": "No JSON body provided"}), 400

    try:
        requested_days, planned_days = compute_road_trip_days(
            details.get("startDate", ""),
            details.get("endDate", ""),
            max_days=30,
        )
        details["requestedDays"] = requested_days
        details["plannedDays"] = planned_days

        prompt = build_road_trip_prompt(details)
        generated_plan = call_gemini(prompt)
        locations_list = generated_plan.get("locations", [])
        map_html = build_plan_trip_map(locations_list)

        if "markdown" in generated_plan:
            generated_plan["markdown"] = enforce_day_limit(generated_plan["markdown"], planned_days)
    
        user_db = get_user_supabase()

        response=user_db.table("road_trips").insert({
            "user_id": session["user_id"],
            "start_location": details.get("startLocation"),
            "end_location": details.get("endLocation"),
            "start_date": details.get("startDate"),
            "end_date": details.get("endDate"),
            "vehicle": details.get("vehicle"),
            "travelers": details.get("travelers"),
            "budget": details.get("budget"),
            "days": planned_days,
            "markdown": generated_plan.get("markdown"),
            "budget_data": generated_plan.get("budget"),
            "locations": generated_plan.get("locations"),
        }).execute()

        return jsonify({
            "data": generated_plan,
            "meta": {
                "requestedDays": requested_days,
                "plannedDays": planned_days,
                "maxDays": 30,
            },
            "map": map_html,
        })
    except Exception as e:
        return jsonify({"error": f"Failed to generate road trip plan: {str(e)}"}), 500

@app.delete("/api/trips/<trip_id>")
@login_required
def delete_trip(trip_id):
    try:
        user_id = session["user_id"]
        body = request.get_json(silent=True) or {}
        trip_type = body.get("tripType")

        user_db = get_user_supabase()
        table = "road_trips" if trip_type == "road_trip" else "plan_trips"

        response = user_db.table(table).delete(count="exact").eq("id", trip_id).eq("user_id", user_id).execute()

        if response.count and response.count > 0:
            return jsonify({"message": "Trip deleted successfully."}), 200

        return jsonify({"error": "Trip not found."}), 404
    except Exception as e:
        print(f"Error deleting trip: {str(e)}")
        return jsonify({"error": f"Failed to delete trip: {str(e)}"}), 500

if __name__ == "__main__":
    app.run()