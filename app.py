from random import seed
from flask import *
import mysql.connector, json
from mysql.connector import errorcode
from collections import defaultdict
from dotenv import load_dotenv
import os
import time
import requests

app=Flask(__name__)
app.secret_key = "*******"
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

load_dotenv()
mydb = mysql.connector.connect(
    host = os.getenv('DB_HOST'),
    user = os.getenv('DB_user'),
    password = os.getenv('DB_PASSWORD'),
    database = os.getenv('DB_DATABASE')
)

class create_dict(dict): 
    def __init__(self): 
        self = dict() 
    def add(self, key, value): 
        self[key] = value

def delete_attraction():
	session.pop("attractionId", None)
	session.pop("attr_name", None)
	session.pop("attr_address", None)
	session.pop("attr_img", None)
	session.pop("date", None)
	session.pop("time", None)
	session.pop("price", None)




# Pages
@app.route("/")
def index():
	return render_template("index.html")
@app.route("/attraction/<id>")
def attraction(id):
	return render_template("attraction.html")
@app.route("/booking")
def booking():
	return render_template("booking.html")
@app.route("/thankyou")
def thankyou():
	return render_template("thankyou.html")
@app.route("/TP")
def TP():
	return render_template("tpE.html")


#API_ATTRACTION
@app.route("/api/attractions", methods = ["GET"])
def api_attractions():
	page = request.args.get('page')
	keywords =request.args.get('keywords')
	cursor = mydb.cursor(buffered=True)
	mydict = create_dict()
	if(page != None or keywords != None):
		nwpage = (int(page)+1)*12-12
		if(keywords != None):
			c_sql = "SELECT COUNT(*) FROM `attraction` WHERE `name` LIKE %s;"
			sql = "SELECT * FROM `attraction` WHERE `name` LIKE %s LIMIT %s, 12;"
			c_check = ("%"+keywords+"%",)
			check = ("%"+keywords+"%", nwpage)
			cursor.execute(c_sql, c_check)
			sum = cursor.fetchone()[0]
		else:
			c_sql = "SELECT COUNT(*) FROM `attraction`;"
			sql = "SELECT * FROM `attraction` LIMIT %s, 12;"
			check = (nwpage,)
			cursor.execute(c_sql)
			sum = cursor.fetchone()[0]
		cursor.execute(sql, check)
	else:
		c_sql = "SELECT COUNT(*) FROM `attraction`;"
		sql = "SELECT * FROM `attraction`;"
		cursor.execute(c_sql)
		sum = cursor.fetchone()[0]
		cursor.execute(sql)
		page = sum

	data = cursor.fetchall()
	mydict = []
	i = 0
	for row in data:
		mydict.append(
		{
			"id":row[0], 
			"name":row[1], 
			"category":row[2], 
			"description":row[3], 
			"address":row[4], 
			"transport":row[5], 
			"mrt":row[6], 
			"latitude":row[7], 
			"longitude":row[8], 
			"images":row[9].split(",")
		})
		i = i+1

	if(mydict != []):
		for j in range(len(data)):
			delete = mydict[j]["images"]
			del(delete[0])
			delete.pop()
	
	cursor.close()

	list = []
	if(mydict == list):
		mydict = None
	if((sum/12) < (int(page)+1)):
		stud_json = json.dumps({"nextPage":None,"data":mydict}, indent=2, ensure_ascii=False)
	else:
		stud_json = json.dumps({"nextPage":str(int(page)+1),"data":mydict}, indent=2, ensure_ascii=False)

	return stud_json

@app.route("/api/attraction/<attractionId>", methods = ["GET"])
def att_id(attractionId):
	cursor = mydb.cursor(buffered=True)
	mydict = create_dict()
	sql = "SELECT * FROM `attraction` WHERE `id` = %s;"
	check = (attractionId,)
	cursor.execute(sql, check)
	data = cursor.fetchall()
	cursor.close()
	mydict = []
	for row in data:
		mydict.append(
		{
			"id":row[0], 
			"name":row[1], 
			"category":row[2], 
			"description":row[3], 
			"address":row[4], 
			"transport":row[5], 
			"mrt":row[6], 
			"latitude":row[7], 
			"longitude":row[8], 
			"images":row[9].split(",")
		})
	if(mydict != []):
		delete = mydict[0]["images"]
		del(delete[0])
		delete.pop()

	stud_json = json.dumps({"data":mydict}, indent=2, ensure_ascii=False)
	return stud_json


@app.route("/api/user", methods = ["GET", "POST", "PATCH", "DELETE"])
def user():
	if (request.method == "GET"):
		if "id" in session:
			mem_dict = {
				"id": session["id"],
				"name":  session["name"],
				"email":  session["email"]
			}
			stud_json = json.dumps({"data": mem_dict}, indent=2, ensure_ascii=False)
		else:
			stud_json = json.dumps({"data": None}, indent=2, ensure_ascii=False)
		return stud_json, 200
	elif (request.method == "POST"):
		data = request.get_json()
		sname = data['name']
		semail = data['email']
		spassword = data['password']
		cursor = mydb.cursor()
		sql = "SELECT `email` FROM `user` WHERE `email` = %s ;"
		check_user = (semail,)
		cursor.execute(sql, check_user)
		new_check = 0
		for check in cursor:
			new_check = check[0]
		if (new_check == semail):
			cursor.close()
			return jsonify({"error":True,"message":"此電子郵件已被註冊"}), 400
		else:
			sql = "INSERT INTO `user` (name, password, email) VALUES ( %s, %s, %s );"
			member_data = (sname, spassword, semail)
			cursor.execute(sql, member_data)
			mydb.commit()
			cursor.close()
			return jsonify({"ok": True}), 200
	elif (request.method == "PATCH"):
		data = request.get_json()
		uemail = data['email']
		upassword = data['password']
		cursor = mydb.cursor(buffered=True)
		sql = "SELECT `id`, `name`, `email`, `password` FROM `user` WHERE `email` = %s AND `password` = %s ;"
		check_data = (uemail, upassword)
		cursor.execute(sql, check_data)
		mydb.commit()
		rid = 0
		rname = 0
		remail = 0
		rpw = 0
		for id, name, email, pw in cursor:
			rid = id
			rname = name
			remail = email
			rpw = pw
		cursor.close()
		if (remail == uemail and rpw == upassword):
			session["id"] = rid
			session["name"] = rname
			session["email"] = remail
			return jsonify({"ok": True}), 200
		else:
			return jsonify({"error":True,"message":"此帳號未註冊"}), 400
	elif (request.method == "DELETE"):
		session.pop("id", None)
		stud_json = json.dumps({"ok": True}, indent=2, ensure_ascii=False)
		return stud_json, 200


@app.route("/api/booking", methods = ["GET", "POST", "DELETE"])
def api_booking():
	if(request.method == "GET"):
		if "id" in session:
			if "attractionId" in session:
				attraction_dict = {
					"id": session["attractionId"],
					"name": session["attr_name"],
					"address": session["attr_address"],
					"image" : session["attr_img"]
				}	
				mydict = {"attraction": attraction_dict, "date": session["date"], "time": session["time"],"price": session["price"]}
				
				stud_json = json.dumps({"data": mydict}, indent=2, ensure_ascii=False)
				return stud_json, 200
			else:
				return jsonify({"data": None}), 200
		else:
			return jsonify({"error": True, "message":"未登入系統，拒絕存取"}), 403

	elif(request.method == "POST"):
		if "id" in session:
			data = request.get_json()
			session["attractionId"] = data["id"]
			session["attr_name"] = data["attr_name"]
			session["attr_address"] = data["address"]
			session["attr_img"] = data["img"]
			session["date"] = data["date"]
			session["time"] = data["time"]
			session["price"] = data["money"]
			return jsonify({"ok": True}), 200
		elif "id" not in session:
			return jsonify({"error": True, "message":"未登入系統，拒絕存取"}), 403
		else:
			return jsonify({"error": True, "message":"檔案建立失敗"}), 400

	elif(request.method == "DELETE"):
		if "id" in session:
			delete_attraction()
			return jsonify({"ok":True}), 200
		else:
			return jsonify({"error": True, "message":"未登入系統，拒絕存取"}), 403


@app.route("/api/orders", methods = ["POST"])
def order_post():
	if "id" in session:
		data = request.get_json()
		order_no = str(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))) + str(time.time()).replace('.', '')[-4:]
		price = data["order"]["price"]
		attr_id = data["order"]["trip"]["attraction"]["id"]
		attr_name = data["order"]["trip"]["attraction"]["name"]
		attr_address = data["order"]["trip"]["attraction"]["address"]
		attr_image = data["order"]["trip"]["attraction"]["image"]
		go_date = data["order"]["trip"]["date"]
		go_time = data["order"]["trip"]["time"]
		contact_name = data["order"]["contact"]["name"]
		contact_email = data["order"]["contact"]["email"]
		contact_phone = data["order"]["contact"]["phone"]
		url = "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
		toTP = {
			"prime": data["prime"],
			"partner_key": os.getenv("partner_key"),
			"merchant_id": os.getenv("merchant_id"),
			"details":"TapPay Test",
			"amount": price,
			"cardholder": {
				"phone_number": contact_phone,
				"name": contact_name,
				"email": contact_email,
			},
			"remember": True
		}
		head = {
			"content-type" : "application/json;",
			"x-api-key" : os.getenv("partner_key")
			}
		send_TP = json.dumps(toTP, indent=2)
		Tprequest = requests.post(url, headers = head, data = send_TP)
		status = json.loads(Tprequest.text)["status"]

		if(status == 0): 
			status_message = "付款成功"
			delete_attraction()
		else: 
			status_message = "付款失敗"


		cursor = mydb.cursor(buffered=True)
		sql = """INSERT INTO `booking` (number, price, attr_id, attr_name, attr_address, attr_image, date, time, contact_name, contact_email, contact_phone, status)
				 VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s );"""
		booking_data = (order_no, price, attr_id, attr_name, attr_address, attr_image, go_date, go_time, contact_name, contact_email, contact_phone, status)
		cursor.execute(sql, booking_data)
		mydb.commit()   
		cursor.close()
		
		return jsonify({"data": {"number":order_no, "payment":{"status":status, "message":status_message}}}), 200
	elif "id" not in session:
		return jsonify({"error": True, "message":"未登入系統，拒絕存取"}), 403
	else:
		return jsonify({"error": True, "message":"訂單建立錯誤"}), 400


@app.route("/api/order/<orderNumber>", methods = ["GET"])
def order_get(orderNumber):
	if "id" in session:
		cursor = mydb.cursor(buffered=True)
		sql = "SELECT * FROM `booking` WHERE `number` = %s;"
		check = (orderNumber,)
		cursor.execute(sql, check)
		data = cursor.fetchall()
		cursor.close()
		if (data != []):
			for row in data:
				order = {
					"data":{
						"number" : row[1],
						"price" : row[2],
						"trip" : {
							"attraction" : {
								"id" : row[3],
								"name" : row[4],
								"address" : row[5],
								"image" : row[6]
							},
							"date" : row[7],
							"time" : row[8]
						},
						"contact" : {
							"name" : row[9],
							"email" : row[10],
							"phone" : row[11]
						},
						"status" : row[12]
					}
				}
			stud_json = json.dumps(order, indent=2, ensure_ascii=False)
			return stud_json, 200
		else:
			stud_json = json.dumps({"data":None}, indent=2, ensure_ascii=False)
			return stud_json, 200
	else:
		return jsonify({"error": True, "message":"未登入系統，拒絕存取"}), 403

app.run(host="0.0.0.0", port=3000)
