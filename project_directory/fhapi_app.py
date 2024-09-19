import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash import dash_table
import CoolProp.CoolProp as CP

# Initialize the Dash app
app = dash.Dash(__name__)

# Default parameters for calculations
Parameter_dict = {
    'Ambient Temperature': 26.7,
    'Relative Humidity': 50,
    'Radiation loss': 0.05,
    'Oxygen content on wet basis': 5,
    'Flue gas exit temperature': 446,
    'CO2 Mass fraction': 0.1527,
    'H2O Mass fraction': 0.0715,
    'O2 Mass fraction': 0.062,
    'N2 Mass fraction': 0.709,
    'SO2 Mass fraction': 0.502e-2,
    'Combustion air temperature': 40,
    'Fuel temperature': 25,
    'Fuel mass flow rate': 12000,
    'Datum temperature': 15,
    'hL': 38520.4,
    'Specific heat of Fuel': 1.7,
    'Steam Mass Flow Rate': 4200,
    'Enthalpy of steam': 2777,
    'Flue Gas Mass': 239165.572,
    'Wet Air Mass': 222965.572,
    'Humidity of air': 0.4,
    'Psat': CP.PropsSI('P', 'T', 26.7 + 273.15, 'Q', 0, 'Water'),
}

# Calculate molar fraction water equivalent to humidity
molar_fraction_water_equivalent_to_humidity = (
    Parameter_dict['Relative Humidity'] * Parameter_dict['Psat'] * 18 / 28 / 100 / 101325
)

# Calculation functions
def energy_input_from_fuel(mfuel, hL, Cpf, X_h, tf, td, ta, mairwet, msteam, Hs):
    Hf = Cpf * (tf - td)
    H_fuel = (hL + Hf) * mfuel
    MWair = (1 - X_h) * 28.84 + X_h * 18
    Mair = mairwet / MWair
    Cpair = 33.915 + 1.214e-3 * (ta + td) / 2
    Cphum = 34.42 + 6.281e-4 * (ta + td) / 2 + 5.6106e-6 * pow(((ta + td) / 2), 2)
    Ha = ((1 - X_h) * Cpair + X_h * Cphum) * (ta - td) * Mair
    Hm = msteam * Hs
    return H_fuel + Ha + Hm

def Energy_Output(mfuel, hL, radiation_loss, tg, td, xc, m3, xo, xn, xh, xs, Q_in):
    Cpco2 = 43.2936 + 0.0115 * (tg + td) / 2 - 818558.5 / pow(((tg + td) / 2), 2)
    Nco2 = xc * m3 / 44
    Hco2 = Nco2 * Cpco2 * (tg - td)
    Cpo2 = 34.627 + 1.0802e-3 * (tg + td) / 2 - 785900 / pow(((tg + td) / 2), 2)
    No2 = xo * m3 / 32
    Ho2 = No2 * Cpo2 * (tg - td)
    Cpn2 = 27.2155 + 4.187e-3 * (tg + td) / 2
    Nn2 = xn * m3 / 28
    Hn2 = Nn2 * Cpn2 * (tg - td)
    Cph2o = 34.417 + 6.281e-4 * (tg + td) / 2 - 5.611e-6 * pow(((tg + td) / 2), 2)
    Nh2o = xh * m3 / 18
    Hh2o = Nh2o * Cph2o * (tg - td)
    Cpso2 = 32.24 + 0.0222 * (tg + td) / 2 - 3.475e-5 * pow(((tg + td) / 2), 2)
    Nhso2 = xs * m3 / 64
    Hso2 = Nhso2 * Cpso2 * (tg - td)
    hs = Hco2 + Ho2 + Hn2 + Hh2o + Hso2
    hr = radiation_loss * hL * mfuel
    Q_out = hs + hr
    Qu = Q_in - Q_out
    return Qu

def efficiency_by_direct_method_Net(Qu, Q_in):
    return 100 * (Qu / Q_in)

def efficiency_by_direct_method_Gross(Qu, Q_in, hL, X_h):
    hH = hL + X_h * 2464.9
    return 100 * (Qu / (Q_in - hL + hH))

def efficiency_by_direct_method_Fuel(Qu, mfuel, hL):
    return 100 * (Qu / (hL * mfuel))

# Define the app layout
app.layout = html.Div(style={'backgroundColor': '#f0f0f0', 'padding': '20px'}, children=[
    # Header
    html.Div(style={'backgroundColor': '#fff9c4', 'borderRadius': '10px', 'boxShadow': '0px 4px 8px rgba(0,0,0,0.1)'}, children=[
        html.H1("Fired Heater Efficiency Calculation", style={'color': '#000000', 'padding': '10px', 'fontFamily': 'Arial, sans-serif'})
    ]),

    # Start button
    html.Div(style={'flex': '1', 'textAlign': 'left', 'marginTop': '20px'}, children=[
        html.Button('Start', id='start-button', n_clicks=0, style={'backgroundColor': '#388e3c', 'color': '#ffffff', 'padding': '15px', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer', 'fontSize': '16px'})
    ]),

    # Input Section
    html.Div(id='input-section', style={'display': 'none', 'backgroundColor': '#f2f2f2', 'borderRadius': '5px', 'boxShadow': '0px 4px 8px rgba(0,0,0,0.1)', 'padding': '10px', 'marginTop': '20px'}, children=[
        html.H2("Input Parameters", style={'backgroundColor': '#fff9c4', 'color': '#000', 'padding': '10px'}),
        
        # Input table
        dash_table.DataTable(
            id='inputs-table',
            columns=[
                {'name': 'Description', 'id': 'description'},
                {'name': 'Value', 'id': 'input', 'editable': True},
                {'name': 'Unit', 'id': 'units'}
            ],
            data=[
                {'description': 'Fuel Mass Flow Rate', 'input': 12000, 'units': 'kg/hr'},
                {'description': 'Flue Gas Exit Temperature', 'input': 446, 'units': '°C'},
                {'description': 'Steam Mass Flow Rate', 'input': 4200, 'units': 'kg/hr'},
                {'description': 'Enthalpy of Steam', 'input': 2777, 'units': 'kJ/kg'}
            ],
            style_table={'width': '40%', 'margin': '0', 'border': '1px solid #ddd'},
            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial, sans-serif', 'fontSize': '16px'},
            style_header={'backgroundColor': '#3498db', 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f2f2f2'},
                {'if': {'row_index': 'even'}, 'backgroundColor': '#ffffff'}
            ]
        ),
    
    ]),

    # Run button
    html.Div(id='run-button-section', style={'display': 'none', 'textAlign': 'left', 'marginTop': '20px'}, children=[
        html.Button('Run', id='calculate-button', n_clicks=0, style={'backgroundColor': '#3498db', 'color': '#ffffff', 'padding': '15px', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer', 'fontSize': '16px'})
    ]),
    
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '20px'}, children=[
    # Heat Balance Table
    html.Div(style={'flex': '1', 'marginRight': '10px'}, children=[
        html.Div(id = 'output-results', style={'display': 'none', 'backgroundColor': '#f2f2f2', 'borderRadius': '5px', 'boxShadow': '0px 4px 8px rgba(0,0,0,0.1)', 'padding': '10px'}, children=[
            html.H1("Results", style={'backgroundColor': '#fff9c4', 'color': '#00000', 'textAlign': 'left', 'padding': '15px', 'border': 'none', 'borderRadius': '5px', 'fontSize': '30px'}),
            dash_table.DataTable(
                id='output-table',
                columns=[
                    {'name': 'Description', 'id': 'description'},
                    {'name': 'Value', 'id': 'output'},
                    {'name': 'Unit', 'id': 'units'}
                ],
                style_table={'width': '40%', 'margin': '0', 'border': '1px solid #ddd'},
                style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial, sans-serif', 'fontSize': '16px'},
                style_header={'backgroundColor': '#3498db', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f2f2f2'
                    },
                    {
                        'if': {'row_index': 'even'},
                        'backgroundColor': '#ffffff'
                    }
                ]
            ),
        ]),
    ]),

    # Block Flow Diagram
    html.Div(id = 'bfd-section', style={'display': 'none', 'flex': '1', 'marginLeft': '10px'}, children=[
    html.Img(src='assets/BFD.png', style={'width': '80%', 'maxWidth': '800px', 'flag': '1',}),
    ]),
]),
])

# Callback to reveal input and run sections
@app.callback(
    [Output('input-section', 'style'), Output('run-button-section', 'style')],
    [Input('start-button', 'n_clicks')]
)
def show_inputs(n_clicks):
    if n_clicks > 0:
        return {'display': 'block'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}

# Callback to calculate results
@app.callback(
    [Output('output-table', 'data'), Output('output-results', 'style'), Output('bfd-section', 'style')],
    [Input('calculate-button', 'n_clicks')],
    [State('inputs-table', 'data')]
)
def update_output(n_clicks, inputs_data):
    if n_clicks == 0:
        return [], {'display': 'none'}, {'display': 'none'}

    input_dict = {item['description']: float(item['input']) for item in inputs_data}
    
    # Extract values from inputs
    fuel_mass_flow_rate = input_dict['Fuel Mass Flow Rate']
    flue_gas_exit_temp = input_dict['Flue Gas Exit Temperature']
    steam_mass_flow_rate = input_dict['Steam Mass Flow Rate']
    enthalpy_steam = input_dict['Enthalpy of Steam']
    
    # Calculate Q_in and Qu
    Q_in = energy_input_from_fuel(fuel_mass_flow_rate, Parameter_dict['hL'], Parameter_dict['Specific heat of Fuel'],
                                  molar_fraction_water_equivalent_to_humidity, Parameter_dict['Fuel temperature'],
                                  Parameter_dict['Datum temperature'], Parameter_dict['Combustion air temperature'],
                                  Parameter_dict['Wet Air Mass'], steam_mass_flow_rate, enthalpy_steam)
    
    Qu = Energy_Output(fuel_mass_flow_rate, Parameter_dict['hL'], Parameter_dict['Radiation loss'], flue_gas_exit_temp,
                       Parameter_dict['Datum temperature'], Parameter_dict['CO2 Mass fraction'], Parameter_dict['Flue Gas Mass'],
                       Parameter_dict['O2 Mass fraction'], Parameter_dict['N2 Mass fraction'], Parameter_dict['H2O Mass fraction'],
                       Parameter_dict['SO2 Mass fraction'], Q_in)
    
    # Calculate efficiencies
    net_efficiency = efficiency_by_direct_method_Net(Qu, Q_in)
    gross_efficiency = efficiency_by_direct_method_Gross(Qu, Q_in, Parameter_dict['hL'], molar_fraction_water_equivalent_to_humidity)
    fuel_efficiency = efficiency_by_direct_method_Fuel(Qu, fuel_mass_flow_rate, Parameter_dict['hL'])
    
    # Prepare output data
    output_data = [
        {'description': 'Heat Input', 'output': f'{Q_in:.2f}', 'units': 'kJ'},
        {'description': 'Energy Useful', 'output': f'{Qu:.2f}', 'units': 'kJ'},
        {'description': 'Net Efficiency', 'output': f'{net_efficiency:.2f}', 'units': '%'},
        {'description': 'Gross Efficiency', 'output': f'{gross_efficiency:.2f}', 'units': '%'},
        {'description': 'Fuel Efficiency', 'output': f'{fuel_efficiency:.2f}', 'units': '%'}
    ]
    
    return output_data, {'display': 'block'}, {'display': 'block'}

if __name__ == '__main__':
    app.run_server(debug=True)
