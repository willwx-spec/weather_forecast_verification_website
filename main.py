from drafter import *
from dataclasses import dataclass, asdict
from datetime import date
import json

# dug a little bit too far into the documentation
# CSS is a very distracting side quest
add_website_css("body { background-color: #567ea3; }")

set_website_title("Wx Fcst Analysis Website WD")
set_site_information(
    author="William Dorsch",
    description="Information about CS1 final project website",
    sources="drafter documentation",
    planning=["CS!_final_project_BRAINSTORMING.docx","CS1_final_project_DESIGN.docx"],
    links="https://github.com/willwx-spec/weather_forecast_verification_website"
)
hide_debug_information()
set_website_framed(False)

# dataclasses
@dataclass
class Forecast:
    # for the record, this can be used for both observations and forecasts
    date_valid: str
    temp: int
    wind: int
    is_cloudy: bool
    is_rainy: bool

@dataclass
class Observation:
    # having different names for the same data is wacky but makes the code make more sense to me
    date_valid: str
    temp: int
    wind: int
    was_cloudy: bool
    was_rainy: bool

@dataclass
class Analysis:
    temp: str
    wind: str
    is_cloudy: str
    is_rainy: str
    
@dataclass
class State:
    forecasts: dict[str, Forecast]
    observations: dict[str, Observation]
    current_forecast: Forecast
    current_observation: Observation
    error_message: str
    
# constants
EMPTY_FORECAST = Forecast(None, 0, 0, False, False)
EMPTY_OBSERVATION = Observation(None, 0, 0, False, False)
EMPTY_DATE = date.min

# main page
def jsonify(forecasts, observations) -> str:
    json_forecasts = {}
    json_observations = {}

    for key, value in forecasts.items():
        json_forecasts[key] = asdict(value)

    for key, value in observations.items():
        json_observations[key] = asdict(value)

    output = json.dumps({"forecasts": json_forecasts, "observations": json_observations}, indent=4)

    return output

@route
def index(state: State) -> Page:
    file_data = jsonify(state.forecasts, state.observations)
    return Page(state, [
        Button("Forecast Manager", "forecast_manager"),
        Button("Forecasting Resources", "resources"), "\n",
        FileUpload("data", accept=".json"), Button("Load data", "load_data"), "\n",
        Download("Download forecast and observation data", "weather_data.json", file_data)
    ])

@route
def load_data(state: State, data: str) -> Update:
    wx_data = json.loads(data)
    

    for key in wx_data["forecasts"]:
        print("key: ", key)
        value = wx_data["forecasts"][key]
        forecast = Forecast(value["date_valid"], value["temp"], value["wind"], value["is_cloudy"], value["is_rainy"])
        state.forecasts[key] = forecast

    for key in wx_data["observations"]:
        print("key: ", key)
        value = wx_data["observations"][key]
        observations = Observation(value["date_valid"], value["temp"], value["wind"], value["was_cloudy"], value["was_rainy"])
        state.observations[key] = observations

    return Update(state)

# forecast resources page
@route
def resources(state: State) -> Page:
    return Page(state, [
        Link("Mesoanalysis", "https://www.spc.noaa.gov/exper/mesoanalysis/"), "\n",
        Button("Return to Home", "index")
    ])

# forecast manager landing page
@route
def forecast_manager(state: State) -> Page:
    state.current_forecast = EMPTY_FORECAST
    return Page(state, [
        Button("Make or Edit Forecast", "load_forecast", [Argument("day_valid", date.today().strftime("%F"))]),
        Button("Make or Edit Observation", "load_observation", [Argument("day_obs_valid", date.today().strftime("%F"))]),
        Button("Analyze a Forecast", "analyze_forecast", [Argument("initialize_flag", True), Argument("date", "-")]),
        Button("Return to Home", "index"),
        ])

# begin forecast editor
@route
def forecast_editor(state: State, date: str) -> Page:
    return Page(state, [
        Text("date valid: ", style_color="white"),
        DateInput("day_valid", state.current_forecast.date_valid, on_input="load_forecast"),
        "\n",
        Text("expected temperature (F):", style_color="white"),
        TextBox("expected_temperature", state.current_forecast.temp, on_input="validate_temp"),
        Output("valid_temp", [""], style_color="red"),
        Text("\n expected wind (mph): ", style_color="white"),
        TextBox("expected_wind", state.current_forecast.wind, on_input="validate_wind"),
        Output("valid_wind", [""], style_color="red"),
        Text("\n cloudy: ", style_color="white"),
        CheckBox("cloudy", state.current_forecast.is_cloudy),
        Text("\n rainy: ", style_color="white"), CheckBox("rainy", state.current_forecast.is_rainy),
        "\n", Button("Save Forecast", "save_forecast"),
        change_color(Output("save_status", [""]), "white"),
        "\n", Button("Go back", "forecast_manager"),
        Button("Return to Home", "index")
        ])

@route
def validate_temp(state: State, expected_temperature: str) -> Fragment:
    if not expected_temperature.isdigit():
        return Fragment(state, ["Invalid input.  Please enter an integer."], target="#valid_temp")
    return Fragment(state, [""], target="#valid_temp")

@route
def validate_wind(state: State, expected_wind: str) -> Fragment:
    if not expected_wind.isdigit():
        return Fragment(state, ["Invalid input.  Please enter an integer."], target="#valid_wind")
    return Fragment(state, [""], target="#valid_wind")

@route
def load_forecast(state: State, day_valid: str) -> Page:
    state.error_message = ""
    if day_valid in state.forecasts:
        state.current_forecast = state.forecasts[day_valid]
    else:
        state.current_forecast = Forecast(day_valid, 0, 0, False, False)

    return forecast_editor(state, day_valid)

@route
def save_forecast(state: State, day_valid: str, expected_temperature: str, expected_wind: str, cloudy: bool, rainy: bool) -> Fragment:
    condition = True
    if not expected_temperature.isdigit():
        condition = False
    if not expected_wind.isdigit():
        condition = False
    if not condition:
        change_color("save_status", "red")
        return Fragment(state, ["invalid inputs"], target="#save_status")
    else:
        change_color(Output("save_status", [""]), "green"),
        state.current_forecast = Forecast(day_valid, int(expected_temperature), int(expected_wind), not cloudy, not rainy)
        state.forecasts[day_valid] = state.current_forecast
        return Fragment(state, ["Save succesful!"], target="#save_status")
# end forecast editor

# begin observation editor
@route
def observation_editor(state: State, date: str) -> Page:
    return Page(state, [
        Text("date valid: ", style_color="white"),
        DateInput("day_obs_valid", state.current_observation.date_valid, on_input="load_observation"),
        "\n",
        Text("observed temperature (F):", style_color="white"),
        TextBox("observed_temperature", state.current_observation.temp, on_input="validate_obs_temp"),
        Output("valid_obs_temp", [""], style_color="red"),
        Text("\n observed wind (mph): ", style_color="white"),
        TextBox("observed_wind", state.current_observation.wind, on_input="validate_obs_wind"),
        Output("valid_obs_wind", [""], style_color="red"),
        Text("\n Was it cloudy: ", style_color="white"),
        CheckBox("was_cloudy", state.current_observation.was_cloudy),
        Text("\n Was it rainy: ", style_color="white"), CheckBox("was_rainy", state.current_observation.was_rainy),
        "\n", Button("Save Observation", "save_observation"),
        change_color(Output("obs_save_status", [""]), "white"),
        "\n", Button("Go back", "forecast_manager"),
        Button("Return to Home", "index")
        ])

@route
def validate_obs_temp(state: State, observed_temperature: str) -> Fragment:
    if not observed_temperature.isdigit():
        return Fragment(state, ["Invalid input.  Please enter an integer."], target="#valid_obs_temp")
    return Fragment(state, [""], target="#valid_obs_temp")

@route
def validate_obs_wind(state: State, observed_wind: str) -> Fragment:
    if not observed_wind.isdigit():
        return Fragment(state, ["Invalid input.  Please enter an integer."], target="#valid_obs_wind")
    return Fragment(state, [""], target="#valid_obs_wind")

@route
def load_observation(state: State, day_obs_valid: str) -> Page:
    state.error_message = ""
    if day_obs_valid in state.observations:
        state.current_observation = state.observations[day_obs_valid]
    else:
        state.current_observation = Observation(day_obs_valid, 0, 0, False, False)

    return observation_editor(state, day_obs_valid)

@route
def save_observation(state: State, day_obs_valid: str, observed_temperature: str, observed_wind: str, was_cloudy: bool, was_rainy: bool) -> Fragment:
    condition = True
    state.error_message = ""
    if not observed_temperature.isdigit():
        condition = False
    if not observed_wind.isdigit():
        condition = False
    if not condition:
        change_color("obs_save_status", "red")
        return Fragment(state, ["invalid inputs"], target="#obs_save_status")
    else:
        change_color(Output("obs_save_status", [""]), "green"),
        state.current_observation = Observation(day_obs_valid, int(observed_temperature), int(observed_wind), was_cloudy, was_rainy)
        state.observations[day_obs_valid] = state.current_observation
        return Fragment(state, ["Save succesful!"], target="#obs_save_status")
# end observation editor

# begin forecast analyzer
def calculate_difference(forecast: Analysis, observation: Analysis) -> Analysis:
    temp_difference = abs(int(forecast.temp) - int(observation.temp))
    wind_difference = abs(int(forecast.wind) - int(observation.wind))

    if forecast.is_cloudy == "True":
        is_cloudy = True
    else:
        is_cloudy = False
    if forecast.is_rainy == "True":
        is_rainy = True
    else:
        is_rainy = False

    if observation.is_cloudy == "True":
        was_cloudy = True
    else:
        was_cloudy = False
    if observation.is_rainy == "True":
        was_rainy = True
    else:
        was_rainy = False

    cloudy_difference = is_cloudy == was_cloudy
    rainy_difference = is_rainy == was_rainy
    return Analysis(temp_difference, wind_difference, cloudy_difference, rainy_difference)

@route
def analyze_forecast(state: State, initialize_flag: bool, date: str) -> Page:
    select_box_contents = [""]
    for key in state.forecasts.keys():
        select_box_contents.append(key)

    if initialize_flag:
        prediction = Analysis("-", "-", "-", "-")
        observed = Analysis("-", "-", "-", "-")
        difference = Analysis("-", "-", "-", "-")
    else:
        prediction = Analysis(str(state.current_forecast.temp), str(state.current_forecast.wind), str(state.current_forecast.is_rainy), str(state.current_forecast.is_cloudy))
        observed = Analysis(str(state.current_observation.temp), str(state.current_observation.wind), str(state.current_observation.was_cloudy), str(state.current_observation.was_rainy))
        difference = calculate_difference(prediction, observed)
    
    return Page(state, [
        Text("Analyze a Forecast \n", style_color="white"),

        # i'm sorry
        Text("Select Forecast: ", style_color="white"), 
        SelectBox("forecast_selector", select_box_contents, date, allow_missing=True, on_input="reload_analyzer"), 
        change_color(state.error_message, "red"), "\n",
        Row( 
            change_width(Div(Text("Field", style_color="white"), style_padding="5px", style_background_color="black"), "175px"), 
            change_width(Div(Text("Predicted", style_color="white"), style_padding="5px", style_background_color="black"), "150px"),
            change_width(Div(Text("Observed", style_color="white"), style_padding="5px", style_background_color="black"), "150px"),
            change_width(Div(Text("Difference", style_color="white"), style_padding="5px", style_background_color="black"), "150px"),
        ),
        Row(
            change_width(Div(Text("Temperature", style_color="white"), style_padding="5px", style_background_color="#F07965"), "175px"),
            change_width(Div(Text(prediction.temp, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
            change_width(Div(Text(observed.temp, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
            change_width(Div(Text(difference.temp, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
        ),
        Row(
            change_width(Div(Text("Wind", style_color="white"), style_padding="5px", style_background_color="#F07965"), "175px"),
            change_width(Div(Text(prediction.wind, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
            change_width(Div(Text(observed.wind, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
            change_width(Div(Text(difference.wind, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
        ),
        Row(
            change_width(Div(Text("Cloudy", style_color="white"), style_padding="5px", style_background_color="#F07965"), "175px"),
            change_width(Div(Text(prediction.is_cloudy, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
            change_width(Div(Text(observed.is_cloudy, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
            change_width(Div(Text(difference.is_cloudy, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
        ),
        Row(
            change_width(Div(Text("Rainy", style_color="white"), style_padding="5px", style_background_color="#F07965"), "175px"),
            change_width(Div(Text(prediction.is_rainy, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
            change_width(Div(Text(observed.is_rainy, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
            change_width(Div(Text(difference.is_rainy, style_color="white"), style_padding="5px", style_background_color="#222D33"), "150px"),
        ),
        Button("Go back", "forecast_manager"), "\n",
        Button("Return to home", "index")
    ])

@route
def reload_analyzer(state: State, forecast_selector: str) -> Page:
    if forecast_selector in state.forecasts.keys() and forecast_selector in state.observations.keys():
        state.error_message = ""
        init = False
        state.current_forecast = state.forecasts[forecast_selector]
        state.current_observation = state.observations[forecast_selector]
    elif forecast_selector in state.forecasts.keys() and not forecast_selector in state.observations.keys():
        state.error_message = "No observation exists for selected date"
        init = True
    elif not forecast_selector in state.forecasts.keys() and forecast_selector in state.observations.keys():
        state.error_message = "No forecast exists for selected date"
        init = True
    else:
        state.error_message = "No forecast or observation exists for selected date"
        init = True
    return analyze_forecast(state, init, forecast_selector)
# end forecast analyzer

@route
def return_to_home(state: State) -> Page:
    state.error_message = ""
    return Page(state, [
        "Save before returning? /n",
        Button("yes", ),
        Button("no", "index"),
        ])

# website init
start_server(State({}, {}, EMPTY_FORECAST, EMPTY_OBSERVATION, ""))
    
