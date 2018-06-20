from flask import Flask, render_template, request
import yaml
import engine

app = Flask(__name__)

with open('/var/www/smogradar/smogradar/config.yml', 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
    api_key = cfg['google_js_api_key']

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html', api_key=api_key)

@app.route("/address/", methods=['GET'])
def results():
    address = request.args.get('address')
    if len(address) < 2:
        return render_template('index.html', api_key=api_key)
    else:
        client = engine.AQIApiService()
        if client.get_aqi_from_address(address.title()):
            return render_template('results.html', results=client)
        else:
            return render_template('index.html', api_key=api_key)

@app.route("/coords/", methods=["GET"])
def show_coords_results():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    if lat and lng:
        client = engine.AQIApiService()
        client.get_aqi_from_lat_lng(lat, lng)
        return render_template('results.html', results=client)
    else:
        return render_template('index.html', api_key=api_key)

if __name__ == "__main__":
    app.run()

