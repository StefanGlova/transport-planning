from flask import Flask, app, redirect, render_template, request, send_file, g
import shutil
import os
import pandas
import csv
from project import planning_function


app = Flask(__name__)

# create path to base directory
basedir = os.path.abspath(os.path.dirname(__file__))
# create path which will be used to upload file
app.config["ENTRY_DATA"] = os.path.join(basedir, "Entry_DATA")
app.config["OUTCOME"] = os.path.join(basedir, "Outcome")

VOLUME_TARGET = 49.0
VOLUME_MAX = 55.0
MINIMUM_VOLUME = 0.35

@app.route("/")
def index():
    """
    open index web page
    """
    return render_template("index.html")


@app.route("/planning", methods=["GET", "POST"])
def planning():
    """

    """
    if request.method == "POST":
        # check if input directory exist and if so, delete it
        # in this directory are stored files
        if os.path.exists(app.config["ENTRY_DATA"]):
            shutil.rmtree(app.config["ENTRY_DATA"])

        # check if input directory exist and if not, create it
        # in this directory are stored files
        if not os.path.exists(app.config["ENTRY_DATA"]):
            os.makedirs(app.config["ENTRY_DATA"])
            
        # check if input directory exist and if so, delete it
        # in this directory are stored files
        if os.path.exists(app.config["OUTCOME"]):
            shutil.rmtree(app.config["OUTCOME"])

        # check if input directory exist and if not, create it
        # in this directory are stored files
        if not os.path.exists(app.config["OUTCOME"]):
            os.makedirs(app.config["OUTCOME"])

        # set variable parameters
        VOLUME_TARGET = float(request.form.get("VOLUME_TARGET"))
        VOLUME_MAX = float(request.form.get("VOLUME_MAX"))
        MINIMUM_VOLUME = float(request.form.get("MINIMUM_VOLUME"))

        
        # user upload file with back orders
        orders = request.files["orders"]
        filepathBO = os.path.join(app.config["ENTRY_DATA"], orders.filename)
        orders.save(filepathBO)
        
        inventory = request.files["inventory"]
        filepathBO = os.path.join(app.config["ENTRY_DATA"], inventory.filename)
        inventory.save(filepathBO)


        # call main planning function
        planning_function(VOLUME_TARGET, VOLUME_MAX, MINIMUM_VOLUME)

	
        return send_file("Functions/final_plan.txt", as_attachment=True)
        
        
        
    else:
        return render_template("planning.html")




if __name__ == '__main__':
    app.run()
