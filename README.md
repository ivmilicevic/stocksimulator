# Stock Simulator

Stock Simulator is web app via which users can simulate buying and selling stocks. On registration user is "given" $10000 which they can spend on stocks.
Data is retrieved from Yahoo Finance API. Users can see change in stock value over time, thus simulating earnings without spending money. 
Built for Harvard's CS50 course.


# Technologies

 - Python 3
 - Flask (web server)
 - SQLite database
 - Bootstrap (CSS Framework)
 - Jinja (Templating language)
 - corejs-typeahead (Search autocomplete)

## Usage and installation

    git clone https://github.com/ivmilicevic/stocksimulator.git
    cd stocksimulator/
    pip install --user -r requirements.txt    
    flask run

## Demo

![Registration](https://s.put.re/3VnCqdP.png)
![Starter dashboard](https://s.put.re/QSsW6zW.png)
![Bought stock](https://s.put.re/T9HxvHq.png)
