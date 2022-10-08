import datetime as dt
import numpy as np
import pandas as pd 

#import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#database setup

engine = create_engine("sqlite:///Resources/hawaii.sqlite")
#reflect existing database into a new model
Base = automap_base()
#reflect the tables
Base.prepare(engine, reflect=True)
#save reference tables
measurement = Base.classes.measurement
station = Base.classes.station

#flask setup
app = Flask(__name__)

session=Session(engine)

#flask routes
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"Precipitation: /api/v1.0/precipitation<br/>"
        f"List of Stations: /api/v1.0/stations<br/>"
        f"Temperature for one year: /api/v1.0/tobs<br/>"
        f"Temperature stat from the start date(yyyy-mm-dd): /api/v1.0/yyyy-mm-dd<br/>"
        f"Temperature stat from start to end dates(yyyy-mm-dd): /api/v1.0/yyyy-mm-dd/yyyy-mm-dd"
    )
    
@app.route('/api/v1.0/precipitation')
def precipitation():
    #create session (link) from Python to the DB
    session = Session(engine)
    #Calculate the date 1 year ago from last date in database
    start_date = '2016-08-23'
    sel = [measurement.date, 
        func.sum(measurement.prcp)]
    #Query for the date and precipitation for the last year    
    precipitation = session.query(*sel).\
            filter(measurement.date >= start_date).\
            group_by(measurement.date).\
            order_by(measurement.date).all()
   
    session.close()

    # Return a dictionary with the date as key and the daily precipitation total as value
    precipitation_dates = []
    precipitation_totals = []

    for date, dailytotal in precipitation:
        precipitation_dates.append(date)
        precipitation_totals.append(dailytotal)
    
    precipitation_dict = dict(zip(precipitation_dates, precipitation_totals))

    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all the active Weather stations in Hawaii"""

    sel = [measurement.station]
    activestations = session.query(*sel).\
        group_by(measurement.station).all()
    session.close()

    # Return a JSON list of stations from the dataset.
    list_of_stations = list(np.ravel(activestations)) 
    return jsonify(list_of_stations)

@app.route('/api/v1.0/tobs')
def tobs():
    session = Session(engine)
    results = session.query(measurement.date,  measurement.tobs, measurement.prcp).\
                filter(measurement.date >= '2016-08-23').\
                filter(measurement.station=='USC00519281').\
                order_by(measurement.date).all()

    session.close()

    tobs_all = []
    for date, tobs in results:
        tobs_dict = {}
        tobs_dict["Date"] = date
        tobs_dict["Tobs"] = tobs
        tobs_all.append(tobs_dict)

    return jsonify(tobs_all)

@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/temp/<start>/<end>')
def stats(start=None, end=None):

    print("Enter start date in url: ie(/2017-08-01)")

    session = Session(engine)
    if not end:
        stats_temp_data= session.query(measurement.date,\
                                func.min(measurement.tobs), \
                                func.avg(measurement.tobs), \
                                func.max(measurement.tobs)).\
                                filter(measurement.date >= start).\
                                group_by(measurement.date).\
                                order_by(measurement.date.desc()).all()
    else:
        stats_temp_data= session.query(measurement.date,\
                            func.min(measurement.tobs), \
                            func.avg(measurement.tobs), \
                            func.max(measurement.tobs)).\
                            filter(measurement.date >= start).\
                            filter(measurement.date <= end).\
                            group_by(measurement.date).\
                            order_by(measurement.date.desc()).all()
    session.close() 

    stats_temp_list = []

    for date, tmin, tavg, tmax in stats_temp_data:
        stat_dict = {}
        stat_dict["Date"] = date
        stat_dict["tmin"] = tmin
        stat_dict["tavg"] = tavg
        stat_dict["tmax"] = tmax
        stats_temp_list.append(stat_dict)

    
    return jsonify(stats_temp_list)


if __name__ == '__main__':
    app.run(debug=True)
