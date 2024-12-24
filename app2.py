from flask import Flask, render_template, request
import requests
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate

app = Flask(__name__)
server = app  
dashboard = Dash(__name__, server=server, url_base_pathname='/dashboard/')

API_KEY = 'Вставьте свой ключ'  


def get_weather_data(city, api_key, days=1):
    try:
        url = f"http://dataservice.accuweather.com/locations/v1/cities/search"
        params = {'apikey': api_key, 'q': city}
        response = requests.get(url, params=params)

        if response.status_code != 200:
            return None

        location_data = response.json()
        if not location_data:
            return None

        location_key = location_data[0]['Key']
        forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/{days}day/{location_key}"
        forecast_params = {'apikey': api_key, 'metric': 'true', 'details': 'true'}
        forecast_response = requests.get(forecast_url, params=forecast_params)

        if forecast_response.status_code != 200:
            return None

        forecast_data = forecast_response.json()
        forecasts = []

        for daily_forecast in forecast_data['DailyForecasts']:
            temperature = daily_forecast['Temperature']['Maximum']['Value']
            wind_speed_kmh = daily_forecast['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0)
            wind_speed_ms = round(wind_speed_kmh * 0.27778, 2)
            precipitation_probability = daily_forecast['Day'].get('PrecipitationProbability', 0)

            forecasts.append({
                'date': daily_forecast['Date'],
                'temperature': temperature,
                'wind_speed': wind_speed_ms,
                'precipitation_probability': precipitation_probability
            })

        return forecasts
    except Exception:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_info = []
    error_message = None

    if request.method == 'POST':
        cities = request.form.getlist('cities')
        days = int(request.form.get('days', 1))

        for city in cities:
            data = get_weather_data(city, API_KEY, days)
            if data:
                weather_info.append({
                    'city': city,
                    'forecasts': data
                })
            else:
                error_message = f'Ошибка получения данных для города {city}. Проверьте название.'

    return render_template('index2.html', 
                           weather_info=weather_info,
                           error_message=error_message)


dashboard.layout = html.Div([
    html.H1("Визуализация погодных данных"),
    dcc.Input(id='city-input', type='text', placeholder='Введите города через запятую'),
    dcc.Dropdown(
        id='days-dropdown',
        options=[
            {'label': '1 день', 'value': 1},
            {'label': '3 дня', 'value': 3},
            {'label': '5 дней', 'value': 5}
        ],
        value=1
    ),
    html.Button('Получить прогноз', id='submit-button', n_clicks=0),
    dcc.Graph(id='weather-graph')
])

@dashboard.callback(
    Output('weather-graph', 'figure'),
    Input('submit-button', 'n_clicks'),
    State('city-input', 'value'),
    State('days-dropdown', 'value')
)
def update_graph(n_clicks, cities, days):
    if n_clicks is None or not cities:
        raise PreventUpdate

    cities = [city.strip() for city in cities.split(',')]
    figure = go.Figure()

    for city in cities:
        weather_data = get_weather_data(city, API_KEY, days)
        if not weather_data:
            continue

        for parameter in ['temperature', 'wind_speed', 'precipitation_probability']:
            figure.add_trace(
                go.Scatter(
                    x=[day['date'] for day in weather_data],
                    y=[day[parameter] for day in weather_data],
                    mode='lines+markers',
                    name=f'{city} ({parameter})'
                )
            )

    figure.update_layout(
        title='Прогноз погоды для маршрута',
        height=600,
        xaxis_title='Дата',
        yaxis_title='Значения',
        showlegend=True
    )

    return figure

if __name__ == '__main__':
    app.run(debug=True)
