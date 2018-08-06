from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from decimal import Decimal

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    
    portofolio = []
    symbolsDB = db.execute("SELECT symbol FROM portofolio WHERE user_id = :userid GROUP BY symbol", userid = session["user_id"])
    print(symbolsDB)
    grandTotal = 0
    for symbolRow in symbolsDB:
        stock = {}
        numberShares = db.execute("SELECT SUM(quantity) FROM portofolio WHERE user_id = :userid AND symbol = :symbol", userid = session["user_id"], symbol= symbolRow["symbol"])[0]["SUM(quantity)"]
        print(numberShares)
        if numberShares <= 0:
            print("number of shares is negative")
            continue
        
        lookupValue = lookup(symbolRow["symbol"])
        
        stock.update({'shares': numberShares, 'price' : usd(lookupValue["price"]), 'name' : lookupValue["name"], 'symbol' : lookupValue["symbol"], 'total' : usd(numberShares * lookupValue["price"]) })
        grandTotal += numberShares * lookupValue["price"]
        portofolio.append(stock)
        
        
    currentCash = db.execute("SELECT cash FROM users WHERE id = :userid", userid = session["user_id"])[0]["cash"]  
    grandTotal += currentCash
    return render_template("index.html", portofolio = portofolio, cash = usd(currentCash), total = usd(grandTotal))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    if request.method == "POST":
        #buy stocks
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("Input can't be blank")
        
        lookupValue = lookup(request.form.get("symbol"))
        if not lookupValue:
            return apology("Invalid symbol")
        #{'name': 'Advanced Micro Devices, Inc.', 'price': 13.42, 'symbol': 'AMD'}
        
        
        #validate user input to prevent entering something other than number
        try:
            numberShares = int(request.form.get("shares"))
        except(TypeError, ValueError):
            return apology("Invalid number of shares")
            
        if numberShares <= 0:
            return apology("Invalid number of shares")
        
        currentCash = db.execute("SELECT cash FROM users WHERE id = :userid", userid = session["user_id"])[0]["cash"]
        
        
        #checks does user have enough money in account
        transactionAmount = numberShares * lookupValue["price"]
        if transactionAmount > currentCash:
            return apology("Not enough money in account")
        else:
            db.execute("INSERT INTO 'portofolio' ('user_id','symbol','quantity','price') VALUES (:userid, :symbol, :shares, :price)", userid=session["user_id"], symbol=lookupValue["symbol"], shares= numberShares, price=usd(lookupValue["price"]))
            db.execute("UPDATE users SET cash = cash - :amount WHERE id = :userid", amount = transactionAmount, userid = session["user_id"])
            flash('Bought')
            return redirect(url_for("index"))
    else:
        return render_template("buy.html")
    

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    table = db.execute("SELECT * FROM portofolio WHERE user_id = :userid", userid = session["user_id"])
    print(table)
    return render_template("history.html", table = table)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbolQuote = lookup(request.form.get("symbol"))
        if symbolQuote is not None:
            return render_template("quoted.html", name=symbolQuote['name'], symbol=symbolQuote['symbol'], price=usd(symbolQuote['price']))
        
        else:
            return apology("Invalid stock symbol")
        
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    #return apology("TODO")
    #checks if user reached this page by post, which means that form is subbmitted
    if request.method == "POST":
        #checks for errors with form(username or password not entered)
        if not request.form.get("username"):
            return apology("must provide username")
        elif not request.form.get("password"):
            return apology("must provide password")
        elif not request.form.get("password2"):
            return apology("must confirm password")
        elif not request.form.get("password") == request.form.get("password2"):
            return apology("passwords don't match")
            
        hashedPassword = pwd_context.hash(request.form.get("password"))
        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=request.form.get("username"), hash=hashedPassword)
        if not result:
            return apology("Username already exists")
        
        #print("Result is {0}".format(result))    
        session["user_id"] = result
        return redirect(url_for("index"))
    #if method is GET, just render register template because user just arrived here  
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method == "POST":
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("Input can't be blank")
        
        lookupValue = lookup(request.form.get("symbol"))
        if not lookupValue:
            return apology("Invalid symbol")
            
        try:
            numberShares = int(request.form.get("shares"))
        except(TypeError, ValueError):
            return apology("Invalid number of shares")
            
        if numberShares <= 0:
            return apology("Invalid number of shares")
            
        sharesOwned = db.execute("SELECT SUM(quantity) FROM portofolio WHERE user_id = :userid AND SYMBOL = :symbol", userid = session["user_id"], symbol=lookupValue["symbol"])[0]["SUM(quantity)"]
        if numberShares > sharesOwned:
            return apology("Too many shares")
        else:
            transactionAmount = numberShares * lookupValue["price"]
            db.execute("INSERT INTO 'portofolio' ('user_id','symbol','quantity','price') VALUES (:userid, :symbol, :shares, :price)", userid=session["user_id"], symbol=lookupValue["symbol"], shares= -numberShares, price=usd(lookupValue["price"]))
            db.execute("UPDATE users SET cash = cash + :amount WHERE id = :userid", amount = transactionAmount, userid = session["user_id"])
            flash("Sold")
            return redirect(url_for("index"))
            
    else:
        return render_template("sell.html")


@app.route("/account", methods=["GET"])
@login_required
def account():
    return render_template("account.html")
    
@app.route("/deposit", methods=["POST"])
@login_required
def deposit():
    if not request.form.get("amount"):
        return apology("Invalid amount")
    
    try:
        amount = float(request.form.get("amount"))
    except (TypeError, ValueError):
        return apology("Invalid amount")
        
    if amount <= 0:
        return apology("Amount must be positive")
    
    print(amount)
    db.execute("UPDATE users SET cash = cash + :amount WHERE id = :userid", amount = amount, userid = session["user_id"])
    
    flash("Added {0} to account".format(usd(amount)))
    return redirect(url_for("index"))
    
@app.route("/pwd_change", methods=["POST"])
@login_required
def pwd_change():
    if not request.form.get("ogpassword") or not request.form.get("newpassword1") or not request.form.get("newpassword2") :
        return apology("Field can't be left blank")
        
    if not request.form.get("newpassword1") == request.form.get("newpassword2"):
        return apology("Passwords don't match")
    
    tableHash = db.execute("SELECT * FROM users WHERE id = :userid", userid=session["user_id"])[0]["hash"]
    if not pwd_context.verify(request.form.get("ogpassword"), tableHash):
        return apology("Current password is incorrect")
    
    db.execute("UPDATE users SET hash = :newhash WHERE id = :userid", newhash = pwd_context.hash(request.form.get("newpassword1")), userid = session["user_id"])  
    
    flash("Successfully changed password")
    return redirect(url_for("index"))