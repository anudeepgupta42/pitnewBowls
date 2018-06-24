# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, session, redirect,url_for
from sqlite3 import Error
import json,apiai, requests, sqlite3, os
import pandas as pd
import matplotlib.pyplot as plt

#os.chdir(r"C:\Users\Deepu\Desktop\pitney bowls")
print(os.getcwd())

application = Flask(__name__)
reply = ''
application.secret_key = '12345'
  

@application.route('/', methods=['POST','GET'])
def login():
    error = None
    if request.method == 'POST':
        username_form  = request.form['username']
        password_form  = request.form['password']
        con = create_connection()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT COUNT(email) FROM user_table WHERE email = ?", (username_form,)) 
        if cur.fetchone()[0]:
            cur.execute("SELECT PASSWORD, EMAIL,NAME FROM user_table WHERE email = ?", (username_form,))
            for row in cur.fetchall():
                print(row[0])
                print(row[1])
                if password_form.strip() == str(row[0]).strip():
                    session['username'] = row[2]
                    session['email'] = row[1]
                    User = session.get('username')
                    return render_template('index.html', username=User)
                else:
                    error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)


@application.route('/logout', methods=['POST','GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))
   
    

@application.route("/get")
def get_bot_response():

    user_email= session.get('email')
    priority_lst = {'low': 1 ,'medium': 2 , 'high':3,  'urgent': 4}
    """ Fetching user dialog from UI """
    userText = request.args.get('msg')

    airequest = Dialogflow_connection() 
    
    airequest.query = userText
    airesponse = airequest.getresponse()
    raw_data = airesponse.read()
	# JSON default
    encoding = airesponse.info().get_content_charset('utf8')  
   
    obj = json.loads(raw_data.decode(encoding))
    
    reply = obj['result']['fulfillment']['speech']
    action=str(obj['result']['action']).lower()
    print(action)
    print(str(obj['result']['parameters']))
    
    if action=='cart_show':
        
        print("In show cart")
        reply = cart_show(user_email) 
        obj = ''
            
    if action=='cart_update':
        
        print("In update cart")
        item_action = str(obj['result']['parameters']['cart__action'])
        product_id = str(obj['result']['parameters']['product_id'])
        qty = 1
        
        if (item_action != '' and product_id != ''):
            reply = cart_update(user_email, item_action, product_id,qty)

            obj = ''
            
    if action=='check_out':
        
        print("In check out")
        CVV = str(obj['result']['parameters']['security-code'])
        card_num = str(obj['result']['parameters']['card-number'])
        name = str(obj['result']['parameters']['name'])
        reply = obj['result']['fulfillment']['speech']
        
        if (CVV != '' and card_num != '' and name != ''):
            ord_id = cart_checkout(user_email)
            reply = reply + " <b>" + ord_id + "</b>"

            obj = ''
    
    if action=='order_show':
        
        print("In order show")

        reply = order_show(user_email)

        obj = ''
    
    if action=='order_status':
        
        print("In order status")
        order_id = str(obj['result']['parameters']['order_id'])

        
        if (order_id != ''):
            reply = order_status(user_email, order_id)

            obj = ''

    if action=='return_order':
        
        print("In order return")
        order_id = str(obj['result']['parameters']['order_id'])
        product_id = str(obj['result']['parameters']['product_id'])

        
        if (order_id != '' and product_id != ''):
            reply = return_order(user_email, order_id,product_id)

            obj = ''

    if action=='complaint':
        
        print("In complaint")
        description = str(obj['result']['parameters']['ticket_description'])
        ticket_type = str(obj['result']['parameters']['ticket_type'])
        priority = str(obj['result']['parameters']['ticket_priority'])
        product_id = str(obj['result']['parameters']['product_id'])
        order_id = str(obj['result']['parameters']['order_id'])
        query = description
        if (order_id != ''):
            query = description + " order id: " + order_id
        
        if (product_id != ''):
            query = description + " product id: " + product_id        
        
        status=2
        if (query != '' and priority != '' and ticket_type != '' ):
            priority_conv = priority_lst[priority.lower()]
            ticket_id = log_ticket(ticket_type, query, user_email, priority_conv, status)
            print(ticket_id)
            reply = "<b>Ticket: " + str(ticket_id) + "</b> is raised with <b>"+ str(priority) + "</b> prioriy " + " as <b>" + query + "</b>"

            obj = ''        
            

    if action=='ticket_show':
        
        print("In show ticket")
        ticket_id=str(obj['result']['parameters']['ticket_id'])
        display =str(obj['result']['parameters']['display'])
        
        if (ticket_id != '' and display != ''):
            
            res = show_ticket(ticket_id)
            if res.status_code == 200:
                print ("Request processed successfully, the response is given below")
                priority_map = {1:'low', 2:'medium', 3:'high', 4:'urgent'}
               
                L1 = "please find below the ticket details"
                L2 = " <br /> <b>Ticket Id</b>: " + str(res.json()['id'])
                L3 = " <br /> <b>Requestor Email</b>: " + res.json()['requester']['email']
                L4 = " <br /> <b>Ticket Type</b>: " + res.json()['type']
                L5 = " <br /> <b>Ticket Description</b>: " + res.json()['description_text']
                
                prioroty_disp = priority_map[res.json()['priority']]
                L6 = " <br /> <b>Priority</b>: " + str(prioroty_disp)

                reply = L1 + L2 + L6 + L3 + L4 + L5 

            else:
                    reply = "Failed to fetch ticket details, please check with a valid ticket id"

            
            obj = ''
            
    

    if action=='ticket_update':
        
        print("In update ticket")
        ticket_id=str(obj['result']['parameters']['ticket_id'])
        tkt_priority=str(obj['result']['parameters']['ticket_priority'][0])
        update=str(obj['result']['parameters']['ticket_update'])
        
        reply = obj['result']['fulfillment']['speech']

        print(ticket_id)
        
        if (ticket_id != '' and tkt_priority != '' and update != ''):
            
            tkt_priority = priority_lst[tkt_priority.lower()]
            res = update_ticket(ticket_id, tkt_priority)

            if res.status_code != 200:
                reply = "Failed to update ticket, please check with a valid ticket id and priority"

            obj = ''    
    return str(reply)
    
    
@application.route('/foo', methods=['POST','GET'])
def tickets():
    con = create_connection()
    print("In function")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from TICKETS")
    rows = cur.fetchall()
    return render_template("list.html",rows = rows)
        
def main():
    application.run()
    #application.run(host='0.0.0.0', port=5151)

def Dialogflow_connection():
    
    CLIENT_ACCESS_TOKEN = '399b08ccc77a481a9dd029c80b4c35af'
    ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
    airequest = ai.text_request()
    airequest.lang = 'de'  # optional, default value equal 'en'
    airequest.session_id = "<SESSION ID, UNIQUE FOR EACH USER>"
    return airequest

def create_connection():

    try:
        conn = sqlite3.connect('Estore.db')
        return conn
    except Error as e:
        print(e)
    return None

def dialogflow_entity(order_id):
    url = 'https://api.api.ai/v1/entities/order_id/entries?v=20150910'
    
    headers = {'Authorization': 'Bearer'+ 'd8a156f859204d299226e8976d244484' ,'Content-Type': 'application/json'}
    
    data = " [ { 'value': '" + order_id  + "' } ] "
    response = requests.post(url,headers=headers,data=data)
    print(response)
    print(response.json)
    
def log_ticket(ticket_type, query, user_email, priority, status):
	api_key = "LJCORVMBzDrBtD6IrPe"
	domain = "hackerearth01"
	password = "x"
	ticket_id = ""


	headers = { 'Content-Type' : 'application/json' }

	ticket = {
		'subject' : ticket_type,
		'description' : query,
		'email' : user_email,
		'type': ticket_type,
		'priority' : priority,
		'status' : status,
        'source' : 7,
	}

	r = requests.post("https://"+ domain +".freshdesk.com/api/v2/tickets", auth = (api_key, password), headers = headers, data = json.dumps(ticket))

	if r.status_code == 201:
	  print ("Ticket created successfully, the response is given below")
	  ticket_id = r.json()['id']
	  print ("Location Header : " + r.headers['Location'])
	  return ticket_id
	else:
	  print ("Failed to create ticket, errors are displayed below,")
	  response = r.json()
	  print (response["errors"])

	  print ("x-request-id : " + r.headers['x-request-id'])
	  print ("Status Code : " + str(r.status_code))
	  return ticket_id

def show_ticket(ticket_id):
    api_key = "LJCORVMBzDrBtD6IrPe"
    domain = "hackerearth01"
    password = "x"

    res = requests.get("https://"+ domain +".freshdesk.com/api/v2/tickets/"+ ticket_id +"?include=requester", auth = (api_key, password))
    return res

def update_ticket(ticket_id,priority):
	api_key = "LJCORVMBzDrBtD6IrPe"
	domain = "hackerearth01"
	password = "x"

	headers = { 'Content-Type' : 'application/json' }

	ticket = {
	  'priority' : int(priority),
	}

	res = requests.put("https://"+ domain +".freshdesk.com/api/v2/tickets/"+ticket_id, auth = (api_key, password), headers = headers, data = json.dumps(ticket))
	return res

""" to get the tickets(JSON) requested by current user(pass email id as in put parameter) which are open """
def get_tickets(user_email):
    api_key = "LJCORVMBzDrBtD6IrPe"
    domain = "hackerearth01"
    password = "x"
    res = requests.get("https://"+ domain +".freshdesk.com/api/v2/tickets?email=" + user_email + "&filter=new_and_my_open", auth = (api_key, password))
    return res
"""
# 
for row in res.json():
    print("Ticket Id: " + str(row['id']))
    print("Description: " + row['description_text'])
    print("Priority: " + str(row['priority']))
    print("Type: " + row['type'])
"""

@application.route('/dashboard', methods=['POST','GET'])
def dashboard():
      con = create_connection()
      con.row_factory = sqlite3.Row
      cur = con.cursor()
      username = session.get('username')
      email= session.get('email')
      cur.execute("select * from VM_INSTANCE WHERE USER_NAME=?",(username,))

      rows = cur.fetchall()
      print(rows)
      dataframe = pd.read_sql_query("select * from TICKETS where NAME='" + username + "'" , con)

      print(dataframe['CATEGORY'])
      print(dataframe['CATEGORY'].value_counts())

      fig = plt.figure()    
      dataframe.groupby('CATEGORY').size().plot(kind='bar')
      path='static/media/graph_' +username + '.png'

      print(path)
      fig.savefig(path)

      print("path ",path)
      open_tickets=get_tickets(email)
      dataframe=pd.DataFrame(open_tickets.json())
      print(" 1234567"  ,dataframe)

      dataframe=dataframe.loc[:,('id','type','priority','description_text')]
      data_frame_html=dataframe.to_html()
      
      return render_template("dashboard.html",path=path,rows=rows,tables=data_frame_html)

def cart_show(user_id):
        items="Here is the list of items in your cart: <br/> <b>product_id, price, quantity </b>"
        items=""
        con = create_connection()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT COUNT(user_id) FROM cart_table WHERE user_id = ?", (user_id,)) 
        if cur.fetchone()[0]:
            cur.execute("SELECT product_id, price, quantity, amount FROM cart_table WHERE user_id = ?", (user_id,))
            for row in cur.fetchall():
                #items = items +  "<br/>"  + row[0] + ' ' + str(row[1]) + ' ' + str(row[2])
                items = items +  str(row[2]) + " unit(s) of " + str(row[0]) + " priced at " + str(row[1]) + " INR <br/>"
                
        #res = head + items
        else:
            items = "No items in your cart"
        
        return items

def cart_update(user_id, item_action, product_id,qty):
        res = ""
        item_price= ""
        amount = ""
        con = create_connection()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("SELECT COUNT(price) FROM product_table WHERE product_id = ?", (product_id,))
 
        if cur.fetchone()[0]:
            cur.execute("SELECT price FROM product_table WHERE product_id = ?", (product_id,))
            for row in cur.fetchall():
                item_price = row[0]
            
            if item_action == 'add':
                amount = float(item_price) * qty
                cur.execute("INSERT INTO cart_table (user_id, product_id, price, quantity, amount) VALUES (?,?,?,?,?)",(user_id,product_id,item_price, qty, amount) )
                con.commit()
                res = product_id + " is added cart succefully" 
                
            else:
                cur.execute("DELETE from cart_table WHERE product_id = ? and user_id=?", (product_id,user_id))
                con.commit()
                res = product_id + " is deleted from cart succefully" 
        else:
            res = "you have entered an invalid product id"

        con.close()
        return res

def cart_checkout(user_id):
        res=""
        con = create_connection()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT COUNT(user_id) FROM cart_table WHERE user_id = ?", (user_id,))
 
        if cur.fetchone()[0]:
            cur.execute("SELECT MAX(order_id) FROM order_table")
            max_ordid = cur.fetchone()[0]
            next_ordid =  int(max_ordid[3:]) + 1
            next_ordid = 'ORD' + str(next_ordid)
            print(next_ordid)
           
            cur.execute("SELECT user_id,product_id,price,quantity,amount FROM cart_table WHERE user_id = ?", (user_id,))
            for row in cur.fetchall():
                print(row[1])
                cur.execute("INSERT INTO order_table (order_id,user_id, product_id, price, quantity, amount, payment_status, order_status, return_flg) VALUES (?,?,?,?,?,?,?,?,?)", (next_ordid, row[0],row[1],row[2],row[3],row[4],'PAID','SHIPPED','N') )
                con.commit()

            dialogflow_entity(next_ordid)
            con = create_connection()
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("DELETE from cart_table WHERE user_id=?", (user_id,))
            print('deleted')
            con.commit()

            res = "order id: " + str(next_ordid) + "</b>"
 
        else:
            res = "you have no items in cart"
        
        return res

def order_status(user_id,order_id):
        res=""
        con = create_connection()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT COUNT(user_id) FROM order_table WHERE user_id = ? and order_id = ?", (user_id,order_id,)) 
        if cur.fetchone()[0]:
            cur.execute("SELECT order_id, product_id, order_status FROM order_table WHERE order_id = ?", (order_id,))
            for row in cur.fetchall():
                res = res + row[1] + " of order " + row[0] + " is <b>" + row[2] + " </b> <br />"
        #res = head + items
        else:
            res = "Please check your order id"
        
        return res        
   
def order_show(user_id):
        res=""
        con = create_connection()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT COUNT(user_id) FROM order_table WHERE user_id = ?", (user_id,)) 
        if cur.fetchone()[0]:
            cur.execute("SELECT order_id, product_id FROM order_table WHERE user_id = ?", (user_id,))
            for row in cur.fetchall():
                res = res + "<b>"+ row[1] + "</b> is ordered under <b>order id: "+ row[0]+"</b> <br />"
        #res = head + items
        else:
            res = "You have no orders to show"
        
        return res
        
def return_order(user_id,order_id,product_id):
        res=""
        con = create_connection()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT COUNT(product_id) FROM order_table WHERE user_id = ? and product_id = ? and order_id = ?", (user_id, product_id, order_id))
 
        if cur.fetchone()[0]:
    
            cur.execute("SELECT user_id,order_id, product_id,price,quantity,amount FROM order_table WHERE user_id = ? and product_id = ? and order_id = ?", (user_id, product_id,order_id))
            for row in cur.fetchall():
                cur.execute("INSERT INTO return_table (user_id, order_id, product_id, price, quantity, amount, return_status) VALUES (?,?,?,?,?,?,?)", (row[0],row[1],row[2],row[3],row[4],row[5],'RETURN_REQUESTED') )
                con.commit()
                cur.execute("UPDATE order_table set return_flg = 'Y' WHERE user_id = ? and product_id = ? and order_id = ?", (user_id, product_id, order_id))
                con.commit()


            res = "Return request succefully placed for <b> order id: " + str(order_id) + "</b> and <b> product:" + str(product_id) + "</b>"
 
        else:
            res = "Please check your order id and product id"
        
        return res
         


if __name__ == "__main__":
    main()
