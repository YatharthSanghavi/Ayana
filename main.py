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
            
            print(f"Login successful! Welcome back, {user.email}")
            return redirect(url_for("root"))

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
    user_id=session["user_id"]

    return render_template("pages/dashboard.html")

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
        
        response=supabase.table("plan_trips").insert({
            "user_id":session["user_id"],
            "destination": details.get('destination'),
            "days":details.get('days'),
            "budget":details.get('budget'),
            "travelers":details.get('travelers'),
            "trip_type":details.get('tripType'),
            "interests":details.get('interests'),
            "markdown":generated_plan.get('markdown'),
            "budget_data":generated_plan.get('budget'),
            "locations":generated_plan.get('locations')
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
      
      # Enforce day limit on the markdown output
      if "markdown" in generated_plan:
        generated_plan["markdown"] = enforce_day_limit(generated_plan["markdown"], planned_days)
      
      return jsonify(
        {
          "data": generated_plan,
          "meta": {
            "requestedDays": requested_days,
            "plannedDays": planned_days,
            "maxDays": 30,
          },
          "map":map_html,
        }
      )
    except Exception as e:
        return jsonify({"error": f"Failed to generate road trip plan: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)