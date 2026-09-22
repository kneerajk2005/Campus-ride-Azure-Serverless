import os
import json
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions
import logging
import uuid
from azure.identity import DefaultAzureCredential
from datetime import datetime
import smtplib
from email.mime.text import MIMEText


# ----------------------------------------------------------------
#   ADMIN LOGIN FUNCTIONssss
# ----------------------------------------------------------------


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
@app.route(route="ad_login", methods=["POST"])
def ad_login(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Admin login API called")

    # Cosmos DB configuration
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = "   "

    try:
        # ✅ Parse JSON request body
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON format"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        username = req_body.get("username")
        password = req_body.get("password")

        if not username or not password:
            return func.HttpResponse(
                json.dumps({"error": "Username and password required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # ✅ Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        # ✅ Query for matching credentials
        query = f"SELECT * FROM c WHERE c.username = '{username}' AND c.password = '{password}'"
        results = list(container.query_items(query=query, enable_cross_partition_query=True))

        if len(results) == 1:

            response_body = {
            "message": "Login successful",
            "session_id": username  # ✅ return session for frontend
    }

            response = func.HttpResponse(
        json.dumps(response_body),
        mimetype="application/json",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )
            # ✅ Optional cookie for session
            response.headers.add("Set-Cookie", f"ad_session={username}; Path=/; HttpOnly; Max-Age=3600")
            return response
        else:
            return func.HttpResponse(
                json.dumps({"error": "Invalid username or password"}),
                mimetype="application/json",
                status_code=401,
                headers={"Access-Control-Allow-Origin": "*"}
            )

    except Exception as e:
        logging.error(f"Error in login: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )




@app.route(route="student_view", methods=["GET"])
def student_view(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("📥 Admin request to view all student details received.")

    # ✅ Admin session validation
    cookie = req.headers.get("Cookie", "")
    session_from_cookie = None

    if "ad_session=" in cookie:
        try:
            session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()
        except Exception:
            session_from_cookie = None

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        logging.warning("⚠️ Unauthorized access — admin session missing.")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized — admin session missing."}),
            status_code=401,
            mimetype="application/json"
        )

    logging.info(f"✅ Admin session validated: {ad_name}")

    # 🔧 Cosmos DB Configuration
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        # 🌐 Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_ID)
        container = database.get_container_client(CONTAINER_ID)

        # 📦 Retrieve students
        students = list(container.read_all_items())

        if not students:
            logging.warning("⚠️ No student entries found.")
            return func.HttpResponse(
                json.dumps({"error": "No student entries found."}),
                status_code=404,
                mimetype="application/json"
            )

        # 🎯 Filter required fields
        filtered_students = []
        for s in students:
            filtered_students.append({
                "student_id": s.get("student_id"),
                "name": s.get("name"),
                "department": s.get("department"),
                "year": s.get("year"),
                "pickup_location": s.get("pickup_location"),
                "bus_number": s.get("bus_number"),
                "contact": s.get("contact"),
                "username1": s.get("username1"),
                "password1": s.get("password1"),
                "email": s.get("email")
            })

        # ✅ Return response
        return func.HttpResponse(
            json.dumps({"students": filtered_students}, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"❌ Cosmos DB Error: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Cosmos DB error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

    except Exception as ex:
        logging.error(f"❗Unexpected Error: {ex}")
        return func.HttpResponse(
            json.dumps({"error": f"Unexpected error: {str(ex)}"}),
            status_code=500,
            mimetype="application/json"
        )
    

def send_email(to_email, subject, body):
    try:
        sender_email = "kneerajk2005@gmail.com"
        sender_password = "khwr zrnf dfba eais"  

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()

        print(f"Email sent to {to_email}")

    except Exception as e:
        print(f"Email failed: {str(e)}")




@app.route(route="add_student", methods=["POST"])
def add_student(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Add student request received.")

    # 🔧 Cosmos DB setup
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = ""

    # ✅ Admin session validation
    cookie = req.headers.get("Cookie", "")
    session_from_cookie = None

    if "ad_session=" in cookie:
        try:
            session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()
        except Exception:
            session_from_cookie = None

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        logging.warning("Unauthorized access attempt detected — no session found.")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized access — admin session missing."}),
            status_code=401,
            mimetype="application/json"
        )

    logging.info(f"Admin session validated: {ad_name}")

    try:
        # 📥 Parse JSON data from POST request
        try:
            data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON format."}),
                status_code=400,
                mimetype="application/json"
            )

        required_fields = [
            "student_id", "name", "department", "year",
            "pickup_location", "bus_number", "contact_number",
            "username", "password","email"
        ]
        for field in required_fields:
            if field not in data:
                return func.HttpResponse(
                    json.dumps({"error": f"Missing field: {field}"}),
                    status_code=400,
                    mimetype="application/json"
                )

        # 🌐 Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_ID)
        container = database.get_container_client(CONTAINER_ID)

        # 🧩 Create student document
        student_doc = {
            "id": str(uuid.uuid4()),
            "student_id": data["student_id"],
            "name": data["name"],
            "department": data["department"],
            "year": data["year"],
            "pickup_location": data["pickup_location"],
            "bus_number": data["bus_number"],
            "contact": data["contact_number"],
            "username1": data["username"],
            "password1": data["password"],
            "email": data["email"]

        }

        # 🚀 Insert document into Cosmos DB
        container.create_item(body=student_doc)

        
        email_body = f"""
        Welcome to Campus Ride 🚍

        Username: {data['username']}
        Password: {data['password']}

        Please login to access your dashboard.
        """

        send_email(data["email"], "Student Account Created", email_body)


        return func.HttpResponse(
            json.dumps({"message": "Student added successfully!", "student": student_doc}),
            status_code=201,
            mimetype="application/json"
        )
    

    except exceptions.CosmosResourceExistsError:
        return func.HttpResponse(
            json.dumps({"error": "Student with this ID already exists."}),
            status_code=409,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error adding student: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
 

@app.route(route="update_student", methods=["GET", "POST"])
def update_student(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Update student request received.")

    # 🔧 Cosmos DB setup
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = ""


    cookie = req.headers.get("Cookie", "")
    session_from_cookie = None

    if "ad_session=" in cookie:
        try:
            session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()
        except Exception:
            session_from_cookie = None

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        logging.warning("Unauthorized access attempt detected — no session found.")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized access — admin session missing."}),
            status_code=401,
            mimetype="application/json"
        )

    logging.info(f"Admin session validated: {ad_name}")



    try:
        # 🌐 Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_ID)
        container = database.get_container_client(CONTAINER_ID)

        # 🧩 POST request → Update student record
        if req.method == "POST":
            try:
                data = req.get_json()
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid JSON format."}),
                    status_code=400,
                    mimetype="application/json"
                )

            required_fields = ["student_id", "name", "department", "year", "pickup_location", "bus_number", "contact_number","email"]
            for field in required_fields:
                if field not in data:
                    return func.HttpResponse(
                        json.dumps({"error": f"Missing field: {field}"}),
                        status_code=400,
                        mimetype="application/json"
                    )

            student_id = data["student_id"]

            # 🔍 Find the student document by student_id
            query = "SELECT * FROM c WHERE c.student_id = @student_id"
            parameters = [{"name": "@student_id", "value": student_id}]
            results = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if not results:
                return func.HttpResponse(
                    json.dumps({"error": "Student not found."}),
                    status_code=404,
                    mimetype="application/json"
                )

            student_doc = results[0]  # existing document

            # 🛠 Update fields
            student_doc["name"] = data["name"]
            student_doc["department"] = data["department"]
            student_doc["year"] = data["year"]
            student_doc["pickup_location"] = data["pickup_location"]
            student_doc["bus_number"] = data["bus_number"]
            student_doc["contact"] = data["contact_number"]
            student_doc["email"] = data["email"]
            # 💾 Replace the existing item in Cosmos DB
            container.replace_item(item=student_doc["id"], body=student_doc)

            return func.HttpResponse(
                json.dumps({"message": "Student updated successfully.", "student": student_doc}),
                status_code=200,
                mimetype="application/json"
            )

        # 📦 GET request → Fetch all students
        elif req.method == "GET":
            students = list(container.query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True
            ))

            if not students:
                return func.HttpResponse(
                    json.dumps({"error": "No student entries found."}),
                    status_code=404,
                    mimetype="application/json"
                )

            return func.HttpResponse(
                json.dumps({"students": students}),
                status_code=200,
                mimetype="application/json"
            )

    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Cosmos DB error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    

#bus
@app.route(route="add_bus", methods=["POST"])
def add_bus(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Add bus request received.")

    # ✅ Admin session validation
    cookie = req.headers.get("Cookie", "")
    session_from_cookie = None

    if "ad_session=" in cookie:
        try:
            session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()
        except Exception:
            session_from_cookie = None

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        logging.warning("⚠️ Unauthorized access — admin session missing.")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized — admin session missing."}),
            status_code=401,
            mimetype="application/json"
        )

    logging.info(f"✅ Admin session validated: {ad_name}")

    # Cosmos DB configuration
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        # Parse JSON data from request body
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON format. Please send valid data."}),
                status_code=400,
                mimetype="application/json"
            )

        # Extract fields
        required = ["bus_id", "name", "route", "bus_no", "maximum_seating", "minimum_seating", "contact", "address", "username", "password","email"]
        for field in required:
            if field not in req_body or not req_body[field]:
                return func.HttpResponse(
                    json.dumps({"error": f"Missing field: {field}"}),
                    status_code=400,
                    mimetype="application/json"
                )

        bus_id = req_body["bus_id"]

        # Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_ID)
        container = database.get_container_client(CONTAINER_ID)

        # Check if bus already exists
        query = f"SELECT * FROM c WHERE c.bus_id = '{bus_id}'"
        existing_bus = list(container.query_items(query=query, enable_cross_partition_query=True))

        if existing_bus:
            return func.HttpResponse(
                json.dumps({"error": f"Bus with ID {bus_id} already exists."}),
                status_code=409,
                mimetype="application/json"
            )

        # Prepare document to insert
        bus_data = {
            "id": bus_id,
            "bus_id": req_body["bus_id"],
            "name": req_body["name"],
            "route": req_body["route"],
            "bus_no": req_body["bus_no"],
            "maximum_seating": req_body["maximum_seating"],
            "minimum_seating": req_body["minimum_seating"],
            "contact": req_body["contact"],
            "address": req_body["address"],
            "username": req_body["username"],
            "password": req_body["password"],
            "email": req_body["email"]

        }

        # Insert into Cosmos DB
        container.create_item(body=bus_data)

        return func.HttpResponse(
            json.dumps({"message": "✅ Bus added successfully!", "bus": bus_data}, indent=2),
            status_code=201,
            mimetype="application/json"
        )

    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"❌ Cosmos DB error: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Database error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"❗Unexpected error: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
    
@app.route(route="busview", methods=["GET"])
def busview(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Bus view request received.")

    # ✅ Admin session validation
    cookie = req.headers.get("Cookie", "")
    session_from_cookie = None

    if "ad_session=" in cookie:
        try:
            session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()
        except Exception:
            session_from_cookie = None

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        logging.warning("⚠️ Unauthorized access — admin session missing.")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized — admin session missing."}),
            status_code=401,
            mimetype="application/json"
        )

    logging.info(f"✅ Admin session validated: {ad_name}")

    # ✅ Cosmos DB setup
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_ID)
        container = database.get_container_client(CONTAINER_ID)

        query = "SELECT * FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))

        cleaned = []
        for item in items:
            cleaned.append({
                "bus_id": item.get("bus_id"),
                "name": item.get("name"),
                "route": item.get("route"),
                "bus_no": item.get("bus_no"),
                "maximum_seating": item.get("maximum_seating"),
                "minimum_seating": item.get("minimum_seating"),
                "contact": item.get("contact"),
                "address": item.get("address"),
                "username": item.get("username"),
                "email": item.get("email")
            })

        if not cleaned:
            return func.HttpResponse(
                json.dumps({"message": "No bus entries found."}),
                mimetype="application/json",
                status_code=404
            )

        return func.HttpResponse(
            json.dumps(cleaned, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"❗Error fetching buses: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )




@app.route(route="update_bus", methods=["POST", "GET"])
def update_bus(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Update bus request received.")

    # ✅ Admin session validation
    cookie = req.headers.get("Cookie", "")
    session_from_cookie = None

    if "ad_session=" in cookie:
        try:
            session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()
        except Exception:
            session_from_cookie = None

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        logging.warning("⚠️ Unauthorized access — admin session missing.")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized — admin session missing."}),
            status_code=401,
            mimetype="application/json"
        )

    logging.info(f"✅ Admin session validated: {ad_name}")

    # Cosmos DB Config
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        # ✅ POST: Update bus data
        if req.method == "POST":
            try:
                req_body = req.get_json()
            except:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid JSON body"}),
                    status_code=400,
                    mimetype="application/json"
                )

            bus_id = req_body.get("bus_id")

            if not bus_id:
                return func.HttpResponse(
                    json.dumps({"error": "bus_id is required"}),
                    status_code=400,
                    mimetype="application/json"
                )

            # 🔍 Find bus document
            query = f"SELECT * FROM c WHERE c.bus_id = '{bus_id}'"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))

            if not items:
                return func.HttpResponse(
                    json.dumps({"error": "Bus not found"}),
                    status_code=404,
                    mimetype="application/json"
                )

            bus_doc = items[0]

            # ✏️ Update allowed fields
            for key in ["name", "route", "bus_no", "maximum_seating", "minimum_seating", "contact", "address","email"]:
                if req_body.get(key):
                    bus_doc[key] = req_body.get(key)

            # 💾 Save updated document
            container.replace_item(item=bus_doc, body=bus_doc)

            return func.HttpResponse(
                json.dumps({"message": "✅ Bus updated successfully"}),
                status_code=200,
                mimetype="application/json"
            )

        # ✅ GET: Return all buses
        query = "SELECT * FROM c"
        buses = list(container.query_items(query=query, enable_cross_partition_query=True))

        output = [
            {
                "bus_id": b.get("bus_id"),
                "name": b.get("name"),
                "route": b.get("route"),
                "bus_no": b.get("bus_no"),
                "maximum_seating": b.get("maximum_seating"),
                "minimum_seating": b.get("minimum_seating"),
                "contact": b.get("contact"),
                "address": b.get("address"),
                "email": b.get("email")

            }
            for b in buses
        ]

        return func.HttpResponse(
            json.dumps(output, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    except exceptions.CosmosHttpResponseError as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )



@app.route(route="ad_notification", methods=["GET"])
def ad_notification(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Fetching all admin notifications...")

    # ✅ Admin session validation
    cookie = req.headers.get("Cookie", "")
    session_from_cookie = None

    if "ad_session=" in cookie:
        try:
            session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()
        except:
            session_from_cookie = None

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        logging.warning("⚠️ Unauthorized access — admin session missing.")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized — admin session missing."}),
            status_code=401,
            mimetype="application/json"
        )

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_ID)
        container = database.get_container_client(CONTAINER_ID)

        items = list(container.read_all_items())

        notifications = [
            {"title": item.get("title"), "message": item.get("message")}
            for item in items
        ]

        return func.HttpResponse(
            json.dumps({"notifications": notifications}, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error fetching notifications: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="add_notification", methods=["POST"])
def add_notification(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Add notification request received.")

    # ✅ Admin session validation
    cookie = req.headers.get("Cookie", "")
    session_from_cookie = None

    if "ad_session=" in cookie:
        try:
            session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()
        except:
            session_from_cookie = None

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        logging.warning("⚠️ Unauthorized access — admin session missing.")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized — admin session missing."}),
            status_code=401,
            mimetype="application/json"
        )

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        data = req.get_json()

        if not all(key in data for key in ("id", "title", "message")):
            return func.HttpResponse(
                json.dumps({"error": "Missing one of id, title, or message"}),
                status_code=400,
                mimetype="application/json"
            )

        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_ID)
        container = database.get_container_client(CONTAINER_ID)

        container.create_item(data)

        return func.HttpResponse(
            json.dumps({"message": "Notification added successfully!"}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error adding notification: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="ad_message", methods=["GET"])
def ad_message(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Fetching all messages...")

    # ✅ Admin Session Validation
    cookie = req.headers.get("Cookie", "")
    session_from_cookie = None

    if "ad_session=" in cookie:
        try:
            session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()
        except Exception:
            session_from_cookie = None

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        logging.warning("Unauthorized access attempt — no admin session.")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized access — admin session missing."}),
            status_code=401,
            mimetype="application/json"
        )

    logging.info(f"✅ Admin session validated: {ad_name}")

    # Cosmos DB Configuration
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        # Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
        database = client.get_database_client(DATABASE_ID)
        container = database.get_container_client(CONTAINER_ID)

        # Fetch all message records
        items = list(container.read_all_items())

        if not items:
            return func.HttpResponse(
                json.dumps({"message": "No messages found."}),
                mimetype="application/json",
                status_code=200
            )

        # Sort messages by date/time (newest first)
        messages_sorted = sorted(items, key=lambda x: x.get("date_time", ""), reverse=True)

        messages = [
            {
                "name": item.get("name"),
                "email": item.get("email"),
                "message": item.get("message"),
                "date_time": item.get("date_time")
            }
            for item in messages_sorted
        ]

        return func.HttpResponse(
            json.dumps(messages, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error fetching messages: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="ad_dashboard", methods=["GET"])
def ad_dashboard(req: func.HttpRequest) -> func.HttpResponse:

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "

    
    session_from_cookie = None
    cookie = req.headers.get("Cookie")
    if cookie and "ad_session=" in cookie:
        session_from_cookie = cookie.split("ad_session=")[1].split(";")[0].strip()

    session_from_header = req.headers.get("ad_session")
    ad_name = session_from_header.strip() if session_from_header else session_from_cookie

    if not ad_name:
        return func.HttpResponse(
        json.dumps({"error": "Unauthorized. Please login as admin."}),
        mimetype="application/json",
        status_code=401
    )

    logging.info(f"Admin session validated: {ad_name}")

    try:
        # 🔗 Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)

        # Containers
        student_container = db.get_container_client("student")
        bus_container = db.get_container_client("bus")
        location_container = db.get_container_client("bus_location")

        # 📊 Calculate dashboard stats
        total_students = len(list(student_container.read_all_items()))
        total_buses = len(list(bus_container.read_all_items()))
        total_drivers = total_buses  # Assuming 1 driver per bus

        # Count active buses from location data
        locations = list(location_container.read_all_items())
        buses_on_route = len({loc.get("bus_no") for loc in locations if loc.get("status") == "active"})

        # ✅ Prepare response
        data = {
            "total_students": total_students,
            "total_buses": total_buses,
            "total_drivers": total_drivers,
            "buses_on_route": buses_on_route
        }

        return func.HttpResponse(
            json.dumps(data, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="ad_map", methods=["GET"])
def ad_map(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Admin requesting live bus locations...")

    # ===== SIMPLE SESSION CHECK =====
    session_value = None

    # --- Check Cookie ---
    cookie = req.headers.get("Cookie", "")
    if "ad_session=" in cookie:
        try:
            session_value = cookie.split("ad_session=")[1].split(";")[0].strip()
        except:
            session_value = None

    # --- Check Header ---
    header_session = req.headers.get("ad_session")
    if header_session:
        session_value = header_session.strip()

    # If no session → block access
    if not session_value:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized. Please login."}),
            status_code=401,
            mimetype="application/json"
        )

    # ===== COSMOS DB CONNECTION =====
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        items = list(container.read_all_items())

        buses = []
        for item in items:
            lat = item.get("latitude")
            lon = item.get("longitude")
            if not lat or not lon:
                continue

            buses.append({
                "username": item.get("username"),
                "bus_no": item.get("bus_no"),
                "latitude": float(lat),
                "longitude": float(lon),
                "last_updated": item.get("updated_at")
            })

        return func.HttpResponse(
            json.dumps(buses),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="student_login", methods=["POST"])
def student_login(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Student login API called")

    # Cosmos DB configuration
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = ""

    try:
        # ✅ Parse request JSON safely
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON format"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        username = req_body.get("username1")
        password = req_body.get("password1")

        # ✅ Validate inputs
        if not username or not password:
            return func.HttpResponse(
                json.dumps({"error": "Username and password required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # ✅ Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        # ✅ Query for matching student record
        query = f"SELECT * FROM c WHERE c.username1 = '{username}' AND c.password1 = '{password}'"
        results = list(container.query_items(query=query, enable_cross_partition_query=True))

        if len(results) == 1:
            student_data = results[0]

            # ✅ Prepare JSON response body
            response_body = {
                "message": "Login successful",
                "session_id": username,      # session identifier
                "student_data": student_data  # student details for local use
            }

            # ✅ Create response object
            response = func.HttpResponse(
                json.dumps(response_body),
                mimetype="application/json",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": "true"
                }
            )

            # ✅ Set session cookie
            response.headers.add(
                "Set-Cookie",
                f"st_session={username}; Path=/; HttpOnly; Secure; SameSite=None; Max-Age=3600"
            )

            logging.info(f"✅ Student '{username}' logged in successfully.")
            return response

        else:
            # ❌ Invalid credentials
            return func.HttpResponse(
                json.dumps({"error": "Invalid username or password"}),
                mimetype="application/json",
                status_code=401,
                headers={"Access-Control-Allow-Origin": "*"}
            )

    except Exception as e:
        logging.error(f"Error in student_login: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )

        
@app.route(route="student_profile", methods=["GET"])
def student_profile(req: func.HttpRequest) -> func.HttpResponse:

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "

    try:
        username = req.params.get("username1")

        if not username:
            return func.HttpResponse(
                json.dumps({"error": "username1 required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client("student")

        query = f"SELECT * FROM c WHERE c.username1 = '{username}'"
        result = list(container.query_items(query=query, enable_cross_partition_query=True))

        if not result:
            return func.HttpResponse(
                json.dumps({"error": "Student not found"}),
                mimetype="application/json",
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        return func.HttpResponse(
            json.dumps(result[0]),
            mimetype="application/json",
            status_code=200,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )


@app.route(route="student_busdetails", methods=["POST"])
def studentss_busdetails(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Student Bus Details API called")

    # Cosmos DB config
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    STUDENT_CONTAINER = "student"
    BUS_CONTAINER = "bus"

    try:
        # ✅ Read request body JSON safely
        req_body = req.get_json() 
        username = req_body.get("username1")   # Frontend sends "username"

        if not username:
            return func.HttpResponse(
                json.dumps({"error": "Username is required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # ✅ Connect DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        student_container = db.get_container_client(STUDENT_CONTAINER)

        # ✅ Query student using correct field name `username1`
        query = f"SELECT * FROM c WHERE c.username1 = '{username}'"
        student_result = list(student_container.query_items(query=query, enable_cross_partition_query=True))

        if len(student_result) == 0:
            return func.HttpResponse(
                json.dumps({"error": "Student not found"}),
                mimetype="application/json",
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # ✅ Extract assigned bus number
        bus_number = student_result[0].get("bus_number")

        # ✅ Fetch bus details
        bus_container = db.get_container_client(BUS_CONTAINER)
        query_bus = f"SELECT * FROM c WHERE c.bus_no = '{bus_number}'"
        bus_data = list(bus_container.query_items(query=query_bus, enable_cross_partition_query=True))

        if len(bus_data) == 0:
            return func.HttpResponse(
                json.dumps({"error": "Bus details not found"}),
                mimetype="application/json",
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # ✅ Success
        return func.HttpResponse(
            json.dumps({"bus_details": bus_data[0]}),
            mimetype="application/json",
            status_code=200,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )




@app.route(route="update_pickup", methods=["POST"])
def update_pickup(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Update pickup API called")

    # Cosmos DB configuration
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        # ✅ Parse JSON request body safely
        req_body = req.get_json()

        username = req_body.get("username1")
        new_pickup = req_body.get("pickup_location")

        if not username or not new_pickup:
            return func.HttpResponse(
                json.dumps({"error": "username and pickup_location required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # ✅ Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        # ✅ Get student record
        query = f"SELECT * FROM c WHERE c.username1 = '{username}'"
        results = list(container.query_items(query=query, enable_cross_partition_query=True))

        if len(results) != 1:
            return func.HttpResponse(
                json.dumps({"error": "Student not found"}),
                mimetype="application/json",
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        student = results[0]
        student['pickup_location'] = new_pickup   # ✅ Update field locally

        # ✅ Save changes back to Cosmos DB
        container.upsert_item(student)

        return func.HttpResponse(
            json.dumps({"message": "Pickup location updated successfully."}),
            mimetype="application/json",
            status_code=200,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )
    
@app.route(route="std_notification", methods=["GET"])
def std_notification(req: func.HttpRequest) -> func.HttpResponse:

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "

    try:
        # ✅ OPTIONAL: username check (for validation only)
        username = req.params.get("username1")

        if not username:
            return func.HttpResponse(
                json.dumps({"error": "username1 required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # ✅ Connect DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client("notify")

        items = list(container.read_all_items())

        notifications = [
            {
                "title": item.get("title"),
                "message": item.get("message")
            }
            for item in items
        ]

        return func.HttpResponse(
            json.dumps(notifications),
            mimetype="application/json",
            status_code=200,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )

@app.route(route="student_map", methods=["GET", "OPTIONS"])
def student_map(req: func.HttpRequest) -> func.HttpResponse:
  

    logging.info("✅ Student Map API Triggered")

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    STUDENT_CONTAINER = "student"
    BUS_LOCATION_CONTAINER = "bus_location"

    # ✅ Handle OPTIONS (CORS preflight)
    if req.method == "OPTIONS":
        return func.HttpResponse(
            "",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    username = req.params.get("username1")
    if not username:
        return func.HttpResponse(
            json.dumps({"error": "username required"}),
            mimetype="application/json",
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"},
        )

    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)

        # ✅ Fetch student to get assigned bus number
        student_container = db.get_container_client(STUDENT_CONTAINER)
        student_query = "SELECT * FROM c WHERE c.username1=@u"
        params = [{"name": "@u", "value": username}]
        student_data = list(
            student_container.query_items(
                query=student_query, parameters=params, enable_cross_partition_query=True
            )
        )

        if not student_data:
            return func.HttpResponse(
                json.dumps({"error": "Student not found"}),
                mimetype="application/json",
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"},
            )

        bus_number = student_data[0].get("bus_number")
        if not bus_number:
            return func.HttpResponse(
                json.dumps({"error": "No bus assigned to this student"}),
                mimetype="application/json",
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"},
            )

        # ✅ Fetch latest bus location
        bus_container = db.get_container_client(BUS_LOCATION_CONTAINER)
        bus_query = "SELECT * FROM c WHERE c.bus_no=@b"
        params = [{"name": "@b", "value": bus_number}]
        bus_result = list(
            bus_container.query_items(
                query=bus_query, parameters=params, enable_cross_partition_query=True
            )
        )

        if not bus_result:
            return func.HttpResponse(
                json.dumps({
                    "bus_number": bus_number,
                    "location": None,
                    "message": "Bus not active yet."
                }),
                mimetype="application/json",
                status_code=200,
                headers={"Access-Control-Allow-Origin": "*"},
            )

        bus = bus_result[0]
        payload = {
            "bus_number": bus_number,
            "latitude": bus.get("latitude"),
            "longitude": bus.get("longitude"),
            "username": bus.get("username"),
            "last_updated": bus.get("updated_at"),
        }

        return func.HttpResponse(
            json.dumps(payload, indent=2),
            mimetype="application/json",
            status_code=200,
            headers={"Access-Control-Allow-Origin": "*"},
        )

    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"},
        )


@app.route(route="contact_student", methods=["POST"])
def contact_student(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("📩 Contact Student API Called")

    # 🔧 Cosmos DB Config
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "YOUR_KEY"
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        # =========================
        # ✅ STEP 1: SESSION HANDLING (FIXED)
        # =========================
        session_username = None

        # 🔹 Option 1: Header
        session_username = req.headers.get("st_session")

        # 🔹 Option 2: Cookie fallback
        if not session_username:
            cookies = req.headers.get("Cookie", "")
            if cookies:
                cookie_dict = {}
                for item in cookies.split(";"):
                    if "=" in item:
                        key, value = item.strip().split("=", 1)
                        cookie_dict[key] = value
                session_username = cookie_dict.get("st_session")

        if not session_username:
            return func.HttpResponse(
                json.dumps({"error": "Unauthorized — Please log in"}),
                mimetype="application/json",
                status_code=401,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": "true"
                }
            )

        logging.info(f"✅ Session user: {session_username}")

        # =========================
        # ✅ STEP 2: PARSE JSON
        # =========================
        try:
            body = req.get_json()
        except:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON format"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        name = body.get("name")
        email = body.get("email")
        message = body.get("message")
        terms_accepted = 1 if body.get("terms_accepted") == True else 0

        # =========================
        # ✅ STEP 3: VALIDATION
        # =========================
        if not name or not email or not message:
            return func.HttpResponse(
                json.dumps({"error": "Name, Email, and Message are required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # =========================
        # ✅ STEP 4: CONNECT DB
        # =========================
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        # =========================
        # ✅ STEP 5: CREATE DOCUMENT
        # =========================
        new_message = {
            "id": str(uuid.uuid4()),
            "username": session_username,
            "name": name,
            "email": email,
            "message": message,
            "terms_accepted": terms_accepted,
            "date_time": datetime.utcnow().isoformat()
        }

        container.create_item(new_message)

        # =========================
        # ✅ STEP 6: RESPONSE
        # =========================
        return func.HttpResponse(
            json.dumps({"message": "Message sent successfully ✅"}),
            mimetype="application/json",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        )

    except Exception as e:
        logging.error(f"❌ Error in contact_student: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Server Error: {str(e)}"}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )


@app.route(route="driver_login", methods=["POST"])
def driver_login(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("driver login API called")

    # Cosmos DB configuration
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        # ✅ Safe JSON parse
        req_body = req.get_json()

        username = req_body.get("username")
        password = req_body.get("password")

        # Validate input
        if not username or not password:
            return func.HttpResponse(
                json.dumps({"error": "Username and password required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        # Query driver record
        query = f"SELECT * FROM c WHERE c.username = '{username}' AND c.password = '{password}'"
        results = list(container.query_items(query=query, enable_cross_partition_query=True))

        if len(results) == 1:
            driver_data = results[0]   # ✅ Corrected variable

            response_body = {
                "message": "driver login successful",
                "driver_data": driver_data
            }

            return func.HttpResponse(
                json.dumps(response_body),
                mimetype="application/json",
                status_code=200,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        else:
            return func.HttpResponse(
                json.dumps({"error": "Invalid username or password"}),
                mimetype="application/json",
                status_code=401,
                headers={"Access-Control-Allow-Origin": "*"}
            )

    except Exception as e:
        logging.error(f"Error in driver login: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Server error: " + str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )
    
        

@app.route(route="driver_dashboard", methods=["POST"])
def driver_dashboard(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Driver Dashboard API Called")

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        # ✅ Safe JSON Parse
        try:
            req_body = req.get_json()
        except:
            return func.HttpResponse(
                json.dumps({"error": "Request must be JSON"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        username = req_body.get("username")

        if not username:
            return func.HttpResponse(
                json.dumps({"error": "Username is required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        # ✅ Query Driver Profile
        query = """
        SELECT c.bus_id, c.name, c.contact, c.bus_no, c.address, c.license, c.email
        FROM c WHERE c.username = @username
        """
        params = [{"name": "@username", "value": username}]

        results = list(container.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True
        ))

        if len(results) == 1:
            return func.HttpResponse(
                json.dumps({"driver_profile": results[0]}),
                mimetype="application/json",
                status_code=200,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        return func.HttpResponse(
            json.dumps({"error": "Driver not found"}),
            mimetype="application/json",
            status_code=404,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        logging.error(f"Error in driver dashboard: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Server error: " + str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )

@app.route(route="driver_student_list", methods=["POST"])
def driver_student_list(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Driver Student List API Called")

    # Cosmos DB configuration
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    BUS_CONTAINER = "bus"
    STUDENT_CONTAINER = "student"

    try:
        # ✅ Safe parse JSON
        try:
            req_body = req.get_json()
        except:
            return func.HttpResponse(
                json.dumps({"error": "Request must be JSON"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        username = req_body.get("username")

        if not username:
            return func.HttpResponse(
                json.dumps({"error": "Username is required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # Connect to Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        bus_container = db.get_container_client(BUS_CONTAINER)
        student_container = db.get_container_client(STUDENT_CONTAINER)

        # ✅ 1. Get driver's bus number
        query_bus = """
        SELECT c.bus_no FROM c WHERE c.username = @username
        """
        params_bus = [{"name": "@username", "value": username}]
        
        bus_result = list(bus_container.query_items(
            query=query_bus,
            parameters=params_bus,
            enable_cross_partition_query=True
        ))

        if len(bus_result) == 0:
            return func.HttpResponse(
                json.dumps({"error": "Driver not found"}),
                mimetype="application/json",
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        bus_no = bus_result[0]["bus_no"]

        # ✅ 2. Fetch students assigned to this bus
        query_students = """
        SELECT c.name, c.pickup_location, c.department, c.contact, c.email
        FROM c WHERE c.bus_number = @bus_no
        """
        params_students = [{"name": "@bus_no", "value": bus_no}]

        students = list(student_container.query_items(
            query=query_students,
            parameters=params_students,
            enable_cross_partition_query=True
        ))

        return func.HttpResponse(
            json.dumps({"bus_no": bus_no, "students": students}),
            mimetype="application/json",
            status_code=200,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        logging.error(f"Error in driver_student_list: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Server error: " + str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )


@app.route(route="driver_notifications", methods=["GET"])
def driver_notifications(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Driver Notifications API Called")

    # Cosmos DB configuration
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        query = "SELECT * FROM c "
        results = list(container.query_items(query=query, enable_cross_partition_query=True))

        return func.HttpResponse(
            json.dumps({"notifications": results}),
            mimetype="application/json",
            status_code=200,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        logging.error(f"Error in driver_notifications: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Server error " + str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )


@app.route(route="contact_driver", methods=["POST"])
def contact_driver(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Contact Driver API Called")

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "
    CONTAINER_ID = " "

    try:
        # Parse JSON safely
        try:
            data = req.get_json()
        except:
            return func.HttpResponse(
                json.dumps({"error": "Request must be JSON"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        name = data.get("name")
        email = data.get("email")
        phone_no = data.get("phone_no")
        role = data.get("role")
        message = data.get("message")
        terms_accepted = data.get("terms_accepted", False)

        if not name or not email or not phone_no or not role or not message:
            return func.HttpResponse(
                json.dumps({"error": "All fields are required"}),
                mimetype="application/json",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)
        container = db.get_container_client(CONTAINER_ID)

        new_msg = {
            "id": str(uuid.uuid4()),  # Unique message ID
            "name": name,
            "email": email,
            "phone_no": phone_no,
            "role": role,
            "message": message,
            "terms_accepted": terms_accepted,
            "submitted_at": str(datetime.utcnow())
        }

        container.upsert_item(new_msg)

        return func.HttpResponse(
            json.dumps({"success": "Message sent successfully!"}),
            mimetype="application/json",
            status_code=200,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        logging.error(f"Error in contact_driver: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Server error: " + str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )



@app.route(route="start_bus", methods=["POST"])
def start_bus(req: func.HttpRequest) -> func.HttpResponse:

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "

    try:
        data = req.get_json()
        username = data.get("username")

        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client("   ")

        bus_container = db.get_container_client("bus")
        notify_container = db.get_container_client("notify")

        result = list(bus_container.query_items(
            query="SELECT * FROM c WHERE c.username=@u",
            parameters=[{"name": "@u", "value": username}],
            enable_cross_partition_query=True
        ))

        if not result:
            return func.HttpResponse("Driver not found", status_code=404)

        bus_no = result[0]["bus_no"]

        # ✅ ADD NOTIFICATION
        notify_container.create_item({
            "id": str(uuid.uuid4()),
            "title": "Bus Started 🚍",
            "message": f"Bus {bus_no} has started.",
            "timestamp": datetime.utcnow().isoformat()
        })

        return func.HttpResponse(
            json.dumps({"message": "Bus started"}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)

@app.route(route="update_location", methods=["POST", "OPTIONS"])
def update_location(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("🛰️ Update Location API Called")

    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    DATABASE_ID = "   "

    # ✅ CORS (OPTIONS)
    if req.method == "OPTIONS":
        return func.HttpResponse(
            "",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    try:
        # ✅ Parse request
        try:
            data = req.get_json()
        except:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON"}),
                status_code=400,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        username = data.get("username")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if not username or latitude is None or longitude is None:
            return func.HttpResponse(
                json.dumps({"error": "username, latitude & longitude required"}),
                status_code=400,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        # ✅ Connect Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DATABASE_ID)

        bus_container = db.get_container_client("bus")
        location_container = db.get_container_client("bus_location")

        # ✅ Get bus number using driver username
        query = "SELECT c.bus_no FROM c WHERE c.username=@u"
        params = [{"name": "@u", "value": username}]

        result = list(bus_container.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True
        ))

        if not result:
            return func.HttpResponse(
                json.dumps({"error": "Driver not found"}),
                status_code=404,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        # 🔥 IMPORTANT: Ensure string type
        bus_no = str(result[0]["bus_no"])

        logging.info(f"Driver: {username} → Bus: {bus_no}")

        # ✅ Prepare document (UPSERT = INSERT or UPDATE)
        location_doc = {
            "id": bus_no,                 # unique per bus
            "bus_no": bus_no,             # MUST match partition key
            "username": username,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "status": "active",
            "updated_at": datetime.utcnow().isoformat()
        }

        logging.info(f"Saving location: {location_doc}")

        # ✅ UPSERT (key logic)
        location_container.upsert_item(location_doc)

        return func.HttpResponse(
            json.dumps({"message": "Location updated successfully"}),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    except Exception as e:
        logging.error(f"❌ Error in update_location: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

@app.route(route="stop_bus", methods=["POST"])
def stop_bus(req: func.HttpRequest) -> func.HttpResponse:
    COSMOS_ENDPOINT = " "
    COSMOS_KEY = "   "
    try:
        data = req.get_json()
        username = data.get("username")

        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client("   ")

        bus_container = db.get_container_client("bus")
        notify_container = db.get_container_client("notify")

        result = list(bus_container.query_items(
            query="SELECT * FROM c WHERE c.username=@u",
            parameters=[{"name": "@u", "value": username}],
            enable_cross_partition_query=True
        ))

        bus_no = result[0]["bus_no"]

        # ✅ ADD NOTIFICATION
        notify_container.create_item({
            "id": str(uuid.uuid4()),
            "title": "Bus Stopped 🛑",
            "message": f"Bus {bus_no} has stopped.",
            "timestamp": datetime.utcnow().isoformat()
        })

        return func.HttpResponse(
            json.dumps({"message": "Bus stopped"}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)


@app.route(route="get_maps_config", methods=["GET", "OPTIONS"])
def get_maps_config(req: func.HttpRequest) -> func.HttpResponse:

    if req.method == "OPTIONS":
        return func.HttpResponse("", status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        })
    AZURE_MAPS_KEY = " "

    # ✅ Read key from App Settings — never hardcoded
    maps_key = AZURE_MAPS_KEY

    if not maps_key:
        return func.HttpResponse(
            json.dumps({"error": "Maps key not configured"}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"},
        )

    return func.HttpResponse(
        json.dumps({"key": maps_key}),
        mimetype="application/json",
        status_code=200,
        headers={"Access-Control-Allow-Origin": "*"},
    )

