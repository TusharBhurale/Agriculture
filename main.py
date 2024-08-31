import json
import requests as requests
from flask import Flask, render_template, request, redirect, url_for
import pickle
from CropApi import CROPAPI
import lightgbm as lgb
import pandas as pd

app = Flask(__name__)


crop_recommendation_model = pickle.load(open("cropRecommdendationModel.pkl", "rb"))
API_KEY_OPEN_WEATHER = "4c61f798e1507fb0f06b70da4c7d41c8"
# cropdf = pd.read_csv("Crop_recommendation.csv")
cropApi = CROPAPI()
api_data = []
Current_location=None
Nitrogen = 0

with open("Random_model.pickle", 'rb') as file:
    loaded_model = pickle.load(file)
    print(loaded_model.predict([[2045,9]]))
print("Model unpickled successfully!")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_soil_data", methods=['GET', 'POST'])
def get_soil_data():
    if request.method == "POST":
        # NPK – nitrogen, phosphorus, and potassium
        n = request.form.get('n')
        p = request.form.get('p')
        k = request.form.get('k')
        ph = request.form.get('ph')
        temperature = request.form.get('temp')
        humidity = request.form.get('humidity')
        rainfall = request.form.get('RainFall')
        recommended_crop = crop_recommendation_model.predict(pd.DataFrame([[float(n), float(p), float(k), float(temperature), float(humidity), float(ph), float(rainfall)]], columns = ['N', 'P', 'K',	'temperature', 'humidity', 'ph','rainfall']))[0]
        return render_template("soil_data_input.html", crop=recommended_crop, result=1)
    return render_template("soil_data_input.html", crop="", result=0)


@app.route('/process/<string:userinfo>', methods=['GET', 'POST'])
def process(userinfo):
    userinfo = json.loads(userinfo)
    print(f"User type :: {userinfo['values']}")
    latitude, longitude = (userinfo['values'][7:-1]).split(',')
    response = requests.get(f'https://rest.isric.org/soilgrids/v2.0/properties/query?lon={longitude}1&lat={latitude}&property=bdod&property=cec&property=cfvo&property=clay&property=nitrogen&property=ocd&property=ocs&property=phh2o&property=sand&property=silt&property=soc&depth=0-5cm&depth=0-30cm&depth=5-15cm&depth=15-30cm&depth=30-60cm&depth=60-100cm&depth=100-200cm&value=Q0.05&value=Q0.5&value=Q0.95&value=mean&value=uncertainty')
    soilGridData = response.json()['properties']['layers']

    global Nitrogen, api_data, Current_location
    Current_location = [latitude, longitude]
    Nitrogen = soilGridData[4]['depths'][3]['values']['mean']
    api_data = cropApi.data(float(latitude), float(longitude))
    return redirect(url_for('location'))


@app.route("/location", methods=['GET','POST'])
def location():
    print(Nitrogen)
    if request.method == "POST":
        properties = ['Nitrogen', 'Phosphorus', 'Potassium', 'PH Level', 'Temperature', 'Humidity', 'RainFall ']
        p = request.form.get('p')
        k = request.form.get('k')
        ph = request.form.get('ph')
        rainfall = request.form.get('RainFall')
        # api_data=[102,180]
        if len(api_data) > 0:
            print(p, k, ph, rainfall, api_data[0],api_data[1])
            recommended_crop = crop_recommendation_model.predict(
                pd.DataFrame([[float(Nitrogen), float(p), float(k), float(api_data[0]), float(api_data[1]), float(ph), float(rainfall)]],
                         columns=['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']))[0]
            print(recommended_crop)
            values = [float(Nitrogen), float(p), float(k), float(api_data[0]), float(api_data[1]), float(ph), float(rainfall)]
            return render_template('Location.html', valuesLength=range(len(values)), values=values, Location=Current_location, result=1, properties=properties, crop=recommended_crop)
    return render_template('Location.html', values=0 ,result=0)


@app.route("/rainfallPrediction", methods=['GET', 'POST'])
def rainfallPrediction():
    predict_value = ""
    if request.method == 'POST':
        year = int(request.form.get('year'))
        month = int(request.form.get('Month'))
        print(year, month)

        with open("Random_model.pickle", 'rb') as file:
            loaded_model = pickle.load(file)
            predict_value = f"Predicted Value = {loaded_model.predict([[year, month]])[0]}"
        print(predict_value)

    return render_template("predict.html", predict_value=str(predict_value))



@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True, port=2000)